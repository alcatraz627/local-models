#!/usr/bin/env python3
"""RAG core for `lm rag` — turn local markdown docs into a searchable vector index.

Everything stays on the box: chunks are embedded via the local Ollama embedder
and stored in a single sqlite-vec file, so there is no server, no idle cost,
and nothing leaves the machine. The conductor (lib/rag) drives this; the chat
model never drives retrieval itself (docs/03 decision).

Commands (JSON on stdout, machine-first — lib/rag renders for humans):
  index <db> <file.md>...   rebuild the index from the given files
  search <db> "query" -k N  KNN over chunks -> {chunks:[{ref,path,heading,...}]}
  status <db>               corpus + embedder facts
"""
import json
import os
import sqlite3
import sys
import urllib.request

import sqlite_vec
from sqlite_vec import serialize_float32

HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
MODEL = os.environ.get("RAG_EMBED_MODEL", "nomic-embed-text")
DIMS = 768
MAX_CHARS = 2400   # ~600 tokens per chunk keeps 6-8 retrieved chunks inside q's ctx
OVERLAP_LINES = 3


def api(path, payload=None, timeout=180):
    req = urllib.request.Request(
        HOST.rstrip("/") + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def resident_keep_alive():
    """Honor the _lib.sh residency contract: never evict a warm/leased model,
    never leave a cold one loaded (keep_alive is last-writer-wins per request)."""
    try:
        names = [m.get("name", "") for m in api("/api/ps").get("models", [])]
        return -1 if any(n.split(":")[0] == MODEL.split(":")[0] for n in names) else 0
    except Exception:
        return 0


def embed(texts, keep):
    out = []
    for i in range(0, len(texts), 32):
        r = api("/api/embed", {"model": MODEL, "input": texts[i : i + 32], "keep_alive": keep})
        out.extend(r["embeddings"])
    return out


def chunk_file(path):
    """Split a markdown file into heading-scoped chunks; oversized sections are
    windowed at line boundaries with a small overlap so no fact falls between
    two chunks. Yields (heading, start_line, text)."""
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    sections, cur, cur_head, cur_start = [], [], "(top)", 1
    for n, line in enumerate(lines, 1):
        if line.startswith(("# ", "## ", "### ")):
            if any(l.strip() for l in cur):
                sections.append((cur_head, cur_start, cur))
            cur_head, cur_start, cur = line.lstrip("#").strip(), n, [line]
        else:
            cur.append(line)
    if any(l.strip() for l in cur):
        sections.append((cur_head, cur_start, cur))

    for head, start, seg in sections:
        buf, buf_start, size = [], start, 0
        for off, line in enumerate(seg):
            buf.append(line)
            size += len(line) + 1
            if size >= MAX_CHARS:
                yield head, buf_start, "\n".join(buf)
                keep = buf[-OVERLAP_LINES:]
                buf_start = start + off - len(keep) + 1
                buf, size = list(keep), sum(len(l) + 1 for l in keep)
        if any(l.strip() for l in buf):
            yield head, buf_start, "\n".join(buf)


def open_db(path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    db = sqlite3.connect(path)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    return db


def cmd_index(db_path, files):
    db = open_db(db_path)
    db.executescript(
        "DROP TABLE IF EXISTS chunks; DROP TABLE IF EXISTS vec_chunks; DROP TABLE IF EXISTS meta;"
        "CREATE TABLE chunks(id INTEGER PRIMARY KEY, path TEXT, heading TEXT, start_line INT, text TEXT);"
        f"CREATE VIRTUAL TABLE vec_chunks USING vec0(embedding float[{DIMS}]);"
        "CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);"
    )
    keep = resident_keep_alive()
    rows, n_files = [], 0
    for f in files:
        n_files += 1
        for head, start, text in chunk_file(f):
            rows.append((f, head, start, text))
    vecs = embed([f"{p} § {h}\n{t}" for p, h, t in [(r[0], r[1], r[3]) for r in rows]], keep)
    for i, ((path, head, start, text), v) in enumerate(zip(rows, vecs), 1):
        db.execute("INSERT INTO chunks(id,path,heading,start_line,text) VALUES(?,?,?,?,?)",
                   (i, path, head, start, text))
        db.execute("INSERT INTO vec_chunks(rowid,embedding) VALUES(?,?)", (i, serialize_float32(v)))
    from datetime import datetime, timezone
    for k, v in (("embedder", MODEL), ("dims", str(DIMS)),
                 ("created", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
                 ("files", str(n_files))):
        db.execute("INSERT INTO meta VALUES(?,?)", (k, v))
    db.commit()
    print(json.dumps({"ok": True, "files": n_files, "chunks": len(rows),
                      "db": db_path, "embedder": MODEL}))


def cmd_search(db_path, query, k):
    db = open_db(db_path)
    keep = resident_keep_alive()
    qv = embed([query], keep)[0]
    hits = db.execute(
        "SELECT rowid, distance FROM vec_chunks WHERE embedding MATCH ? AND k = ? ORDER BY distance",
        (serialize_float32(qv), k),
    ).fetchall()
    chunks = []
    for ref, (rowid, dist) in enumerate(hits, 1):
        path, head, start, text = db.execute(
            "SELECT path, heading, start_line, text FROM chunks WHERE id = ?", (rowid,)
        ).fetchone()
        chunks.append({"ref": ref, "path": path, "heading": head,
                       "start_line": start, "distance": round(dist, 4), "text": text})
    print(json.dumps({"ok": True, "query": query, "chunks": chunks}))


def cmd_status(db_path):
    if not os.path.exists(db_path):
        print(json.dumps({"ok": False, "code": "no_index", "message": f"no index at {db_path} — run: lm rag index"}))
        sys.exit(12)
    db = open_db(db_path)
    meta = dict(db.execute("SELECT key, value FROM meta").fetchall())
    n = db.execute("SELECT count(*) FROM chunks").fetchone()[0]
    paths = [r[0] for r in db.execute("SELECT DISTINCT path FROM chunks ORDER BY path").fetchall()]
    print(json.dumps({"ok": True, "chunks": n, "meta": meta, "db": db_path,
                      "size_mb": round(os.path.getsize(db_path) / 1e6, 1), "paths": len(paths)}))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "index":
        cmd_index(sys.argv[2], sys.argv[3:])
    elif cmd == "search":
        k = 6
        args = sys.argv[3:]
        if "-k" in args:
            i = args.index("-k")
            k = int(args[i + 1])
            del args[i : i + 2]
        cmd_search(sys.argv[2], " ".join(args), k)
    elif cmd == "status":
        cmd_status(sys.argv[2])
    else:
        print(json.dumps({"ok": False, "code": "invalid_args", "message": "usage: rag.py index|search|status <db> ..."}))
        sys.exit(2)


if __name__ == "__main__":
    main()
