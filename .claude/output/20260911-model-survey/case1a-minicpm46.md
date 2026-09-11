# Case 1a: MiniCPM-V 4.6 vs incumbent minicpm-v

- Date: 2026-09-11. Candidate: minicpm-v4.6 (1.6 GB). Incumbent: minicpm-v (5.5 GB).
- Gate: FX-OCR verbatim + FX-UI-1 kanban structure + FX-UI-2 settings badges, scored
  against hand-labeled ground truth. Zero hallucinated elements is a hard requirement
  (the measured trust boundary: local vision is a verifier, not a critic).
- Footprint: +1.6 GB (to ~107 GB). If adopted, the incumbent's 5.5 GB can be pruned, a net −3.9 GB.

## FX-OCR (ground truth: "VERIFY FIXTURE", "corner")
- minicpm-v4.6: `VERIFY FIXTURE` / `corner`. Exact, clean.
- minicpm-v: `Title: VERIFY FIXTURE` / `Body Text: corner`. Exact strings, added labels.
- Verdict: tie on accuracy, candidate cleaner.

## FX-UI-1 kanban (ground truth: INBOX 0, BACKLOG 0, ACTIVE 43, BLOCKED 0, DONE 97)
- minicpm-v4.6: all 5 columns; ACTIVE 43 and DONE 97 both correct; only fumbled BLOCKED (read its body "—" instead of the header 0). 4.5/5.
- minicpm-v: only 4 columns, MISSED the ACTIVE column entirely, and reported DONE as 0 (actually 97). 2/5, and wrong on both information-bearing counts.
- Verdict: candidate wins decisively. This is the structure-discrimination task the incumbent was documented to fail, and it did.

## FX-UI-2 settings badges (ground truth: Jobs 2, Active parts 8, Unlisted parts 6, Error management 12)
- minicpm-v4.6: Active 8, Unlisted 6, Error 12 correct; missed Jobs 2; zero hallucinations.
- minicpm-v: all four reals correct, but hallucinated two badges ("Import parts: 1", "Catalog: 8"; Catalog is a section header). 
- Verdict: candidate is 3/4 clean; incumbent is 4/4 reals but invents two elements. For a verifier, the incumbent's hallucinations are the worse failure.

## Overall verdict

ACCEPTED. minicpm-v4.6 matches the incumbent on OCR, wins decisively on UI structure (the
documented weak spot), and hallucinates nothing where the incumbent invents elements, at
less than a third of the disk. It meets every acceptance criterion.

Recommendation: set `VISION_MODEL=minicpm-v4.6` in config.sh, then prune minicpm-v (−5.5 GB).
Its strength on structure also makes it a candidate to reconsider whether `see --ui` still
needs the 17 GB gemma4:26b; that is decided in Stage 2 against Qwen3-VL-8B.

Residual: candidate missed the Jobs 2 badge and fumbled BLOCKED's 0. Real but minor; the
incumbent is worse on both fixtures. Re-run against more fixtures before pruning gemma4:26b's role.
