#!/bin/bash
# ui_check.sh: photograph every screen of the app, with no model loaded.
#
# It starts the kit with its stand-in engine, puts the app into each state a
# person can meet (nothing made yet, a shelf of images, drawing, failed, model
# not downloaded), and saves a screenshot of each for a person to read. It also
# fails by itself when a control's words do not fit, or an ellipsis reaches the
# screen.
#
#   tests/ui_check.sh OUT_DIR [PORT]
set -u
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:?usage: ui_check.sh OUT_DIR [PORT]}"; PORT="${2:-6279}"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
[ -x "$CHROME" ] || { echo "ui_check: Chrome not found at $CHROME (set CHROME=)" >&2; exit 1; }
mkdir -p "$OUT"
BASE="http://127.0.0.1:$PORT"
FAILS=0
SRV=""

start() {   # start a kit server with the given env assignments, on a fresh or kept data folder
  env IMAGINE_KIT_FAKE=1 IMAGINE_KIT_FAKE_RAM_GB=64 IMAGINE_KIT_NET="$DATA/no-other-machines" "$@" python3 "$KIT/kit.py" app --port "$PORT" --no-open >/dev/null 2>&1 &
  SRV=$!
  for _ in $(seq 1 50); do curl -s -o /dev/null "$BASE/api/state" && return 0; sleep 0.1; done
  echo "ui_check: the server did not start" >&2; exit 1
}
stop() { [ -n "$SRV" ] && kill "$SRV" 2>/dev/null; wait "$SRV" 2>/dev/null; SRV=""; }
trap stop EXIT

url_for() { # WIDTH HEIGHT QUERY: Chrome cannot go under 500 wide, so a narrower view is shown in a frame
  if [ "$1" -lt 500 ]; then
    local src; src="$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "/$3")"
    printf '%s/__frame?w=%s&h=%s&src=%s' "$BASE" "$1" "$2" "$src"
  else printf '%s/%s' "$BASE" "$3"; fi
}
win_w() { [ "$1" -lt 500 ] && echo 500 || echo "$1"; }

shot() {    # NAME WIDTH HEIGHT [QUERY]
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size="$(win_w "$2"),$3" \
    --virtual-time-budget=2500 --screenshot="$OUT/$1.png" "$(url_for "$2" "$3" "${4:-}")" >/dev/null 2>&1
  [ -s "$OUT/$1.png" ] && echo "  shot $OUT/$1.png" || { echo "  FAIL no screenshot for $1"; FAILS=$((FAILS+1)); }
}
post() { curl -s -X POST "$BASE$1" -H 'Content-Type: application/json' -d "$2" >/dev/null; }
wait_idle() { for _ in $(seq 1 100); do curl -s "$BASE/api/state" | grep -q '"state": "running"' || return 0; sleep 0.1; done; }

measure() { # NAME WIDTH: fail when a control's words are clipped, or an ellipsis is on screen
  local dom
  dom="$("$CHROME" --headless=new --disable-gpu --window-size="$(win_w "$2"),1000" --virtual-time-budget=4000 --dump-dom \
        "$(url_for "$2" 1000 "?probe=1")" 2>/dev/null)"
  if printf '%s' "$dom" | grep -q 'data-overflow="0"'; then echo "  ok   $1 at $2 wide: the page does not scroll sideways"
  else echo "  FAIL $1 at $2 wide: the page is wider than the screen by $(printf '%s' "$dom" | grep -o 'data-overflow="[^"]*"' | head -n 1) px"; FAILS=$((FAILS+1)); fi
  if printf '%s' "$dom" | grep -q 'data-clipped="0"'; then echo "  ok   $1 at $2 wide: every control's words fit"
  else echo "  FAIL $1 at $2 wide: clipped controls: $(printf '%s' "$dom" | grep -o 'data-clipped="[^"]*"' | head -n 1)"; FAILS=$((FAILS+1)); fi
  if printf '%s' "$dom" | grep -q 'data-ellipsis="0"'; then echo "  ok   $1 at $2 wide: no ellipsis on screen"
  else echo "  FAIL $1 at $2 wide: an ellipsis is on screen"; FAILS=$((FAILS+1)); fi
}

DATA="$(mktemp -d)"
echo "nothing made yet"
start IMAGINE_KIT_DATA="$DATA"
shot 01-empty-dark 1440 1000 "?theme=dark"
shot 02-empty-light 1440 1000 "?theme=light"

echo "a shelf of images"
python3 - "$DATA" <<'PY'
import os, sys, pathlib
os.environ.update(IMAGINE_KIT_FAKE="1", IMAGINE_KIT_DATA=sys.argv[1], IMAGINE_KIT_FAKE_STEP_S="0", IMAGINE_KIT_FAKE_RAM_GB="64")
sys.path.insert(0, os.environ.get("KIT", "."))
PY
for p in "A red bicycle leaning on a wet brick wall, early morning" "A lighthouse on a cliff in a storm" \
         "A bowl of ramen seen from above on a wooden table" "A paper boat on a puddle"; do
  post /api/generate "{\"prompt\": \"$p\", \"style\": \"photo\"}"; wait_idle
done
post /api/generate '{"follow": "rework", "id": 1, "change": "Make the bicycle blue. Keep the wall, the light and the framing exactly the same."}'; wait_idle
post /api/star '{"id": 3}'
shot 03-shelf-dark 1440 1000 "?theme=dark"
shot 04-shelf-light 1440 1000 "?theme=light"
shot 05-shelf-narrow 390 1400 "?theme=dark"
shot 06-shelf-tablet 820 1100 "?theme=light"
shot 06b-rework-dark 1440 1000 "?theme=dark&from=2"
shot 06c-rework-light 1440 1000 "?theme=light&from=2"
shot 06d-area-dark 1440 1100 "?theme=dark&open=5&mark=1"
shot 06e-area-light 1440 1100 "?theme=light&open=5&mark=1"
shot 06f-compare-dark 1440 1100 "?theme=dark&open=5&view=compare"
shot 06g-source-dark 1440 1100 "?theme=dark&open=5&view=source"
shot 06h-new-thread-dark 1440 1000 "?theme=dark&new=1"
shot 06i-area-narrow 390 1700 "?theme=dark&open=5&mark=1"
shot 06j-threads-mid 1024 1100 "?theme=light&open=5"
shot 06k-more-menu-dark 1440 1000 "?theme=dark&open=5&menu=more"
shot 06l-add-photo-light 1440 1000 "?theme=light&open=5&menu=photo"
shot 06m-settings-dark 1440 1000 "?theme=dark&new=1&menu=settings"
shot 06n-large-text-dark 1440 1000 "?theme=dark&open=5&size=lg"
shot 06o-medium-text-light 1440 1000 "?theme=light&open=5&size=md"
shot 06p-narrow-light 390 1400 "?theme=light&open=5"
shot 06q-narrow-large-text 390 1700 "?theme=dark&open=5&size=lg"
for w in 1440 1024 820 390; do measure shelf "$w"; done
# Drag an area on the image and read back what the page made of it.
DRAG="$("$CHROME" --headless=new --disable-gpu --window-size=1440,1100 --virtual-time-budget=4000 --dump-dom "$BASE/?open=5&drag=1" 2>/dev/null)"
if printf '%s' "$DRAG" | grep -q 'data-dragged="0.20,0.30,0.40,0.40"' && printf '%s' "$DRAG" | grep -q 'data-drag-button="Change the area"'; then
  echo "  ok   dragging on the image marks that area and the button says Change the area"
else
  echo "  FAIL dragging an area: got $(printf '%s' "$DRAG" | grep -o 'data-drag[a-z-]*="[^"]*"' | tr '\n' ' ')"; FAILS=$((FAILS+1))
fi
stop

echo "drawing"
start IMAGINE_KIT_DATA="$DATA" IMAGINE_KIT_FAKE_STEP_S=4
post /api/generate '{"prompt": "A slow one, to see the progress bar", "count": 3}'
sleep 5
shot 07-drawing-dark 1440 1000 "?theme=dark"
shot 07b-drawing-light 1440 1000 "?theme=light"
stop

echo "a failed render"
start IMAGINE_KIT_DATA="$DATA" IMAGINE_KIT_FAKE_FAIL=1 IMAGINE_KIT_FAKE_STEP_S=0
post /api/generate '{"prompt": "This one fails"}'; wait_idle
shot 08-failed-dark 1440 1000 "?theme=dark"
shot 09-failed-light 1440 1000 "?theme=light"
stop

echo "model not downloaded"
start IMAGINE_KIT_DATA="$(mktemp -d)" IMAGINE_KIT_FAKE_MISSING=klein,qwen
shot 10-no-model-dark 1440 1000 "?theme=dark"
stop

echo "a cloud model with no key yet"
start IMAGINE_KIT_DATA="$DATA" IMAGINE_KIT_FAKE_MISSING=gpt
shot 10b-needs-key-dark 1440 1000 "?theme=dark&model=gpt"
shot 10c-needs-key-light 1440 1000 "?theme=light&model=gpt"
shot 10d-needs-key-narrow 390 1500 "?theme=dark&model=gpt"
stop

echo "a computer whose graphics card is too small to draw"
start IMAGINE_KIT_DATA="$(mktemp -d)" IMAGINE_KIT_FAKE_NO_ENGINE=1 IMAGINE_KIT_FAKE_MISSING=gemini,gpt
shot 10e-cannot-draw-dark 1440 1000 "?theme=dark&model=klein"
shot 10f-cannot-draw-light 1440 1000 "?theme=light"
stop

echo "this Mac is too small for the chosen model"
start IMAGINE_KIT_DATA="$(mktemp -d)" IMAGINE_KIT_FAKE_RAM_GB=16 IMAGINE_KIT_FAKE_MISSING=klein
shot 11-too-large-dark 1440 1000 "?theme=dark&model=qwen"
stop

echo "a small computer that knows a bigger one"
NET="$(mktemp -d)"
printf '[{"name": "M5 Pro", "url": "http://127.0.0.1:9", "host": "m5pro", "services": ["see", "imagine"]}]\n' > "$NET/servers.json"
start IMAGINE_KIT_DATA="$DATA" IMAGINE_KIT_NET="$NET" IMAGINE_KIT_FAKE_RAM_GB=8
shot 12-elsewhere-dark 1440 1000 "?theme=dark"
shot 13-elsewhere-light 1440 1000 "?theme=light"
shot 14-elsewhere-narrow 390 1400 "?theme=dark"
for w in 1440 390; do measure elsewhere "$w"; done
stop

[ "$FAILS" -eq 0 ] && echo "ui_check: all screens captured, 0 failures. Now read them." || echo "ui_check: $FAILS failure(s)"
exit "$FAILS"
