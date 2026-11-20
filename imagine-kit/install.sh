#!/bin/bash
# install.sh: set up Imagine Kit on this Mac. Safe to run again.
#
# It makes a private Python environment inside this folder, installs the image
# engine into it, and offers to download the default model. Nothing is installed
# outside this folder except the model files, which go to the shared Hugging
# Face cache in your home folder so other tools can reuse them.
#
#   ./install.sh              set up, then ask before the 16 GB model download
#   ./install.sh --yes        set up and download without asking
#   ./install.sh --no-model   set up only
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MFLUX_VERSION="0.18.0"       # the version this kit was tested with
PYTHON_VERSION="3.12"        # constraints.txt lists versions tested on this Python
ASK=ask
for arg in "$@"; do
  case "$arg" in
    -y|--yes)    ASK=yes ;;
    --no-model)  ASK=no ;;
    -h|--help)   sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "install.sh: unknown option: $arg (try: ./install.sh --help)" >&2; exit 2 ;;
  esac
done

say()  { printf '%s\n' "$*"; }
stop() { printf 'install.sh: %s\n' "$*" >&2; exit 1; }

# Linux, and Windows under WSL, use a different engine and need an NVIDIA
# graphics card to draw. Without one the app still installs, and draws on
# another machine that offers its models.
if [ "$(uname -s)" = Linux ]; then
  command -v python3 >/dev/null 2>&1 || stop "python3 was not found. Install it, then run ./install.sh again:
  sudo apt install python3 python3-venv"
  python3 -m venv --clear "$HERE/.venv" 2>/dev/null || stop "python3 could not make an environment. Install this, then run ./install.sh again:
  sudo apt install python3-venv"
  chmod +x "$HERE/imagine"
  if ! command -v nvidia-smi >/dev/null 2>&1; then
    say "No NVIDIA graphics card was found, so this computer cannot draw by itself."
    say "The app is installed. In it, pick Gemini image or GPT image, which run at Google or OpenAI with your own key."
    say "Or point it at a machine that can draw:  ./imagine server add NAME ADDRESS"
    say "Start it with:  ./imagine"
    exit 0
  fi
  # A card under 12 GB cannot rework an image even with the lightest copy of the model,
  # so the 5 GB engine and the 16 GB model would be a wasted download.
  CARD_GB=$(( $(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | sort -n | tail -n 1 || echo 0) / 1024 ))
  if [ "${CARD_GB:-0}" -lt 12 ]; then
    say "This computer's graphics card has ${CARD_GB} GB of memory. The image model needs 12 GB or more, so it cannot draw by itself."
    say "The app is installed. In it, pick Gemini image or GPT image, which run at Google or OpenAI with your own key."
    say "Or point it at a machine that can draw:  ./imagine server add NAME ADDRESS"
    say "Start it with:  ./imagine"
    exit 0
  fi
  say "Installing the image engine (PyTorch and diffusers). This downloads about 5 GB the first time."
  "$HERE/.venv/bin/python" -m pip install --quiet --upgrade pip
  "$HERE/.venv/bin/python" -m pip install --quiet --requirement "$HERE/requirements-linux.txt" \
    || stop "the image engine did not install. Run ./install.sh again and read the error above it."
  # Installed is not the same as working: load the engine once and make sure it sees the card.
  "$HERE/.venv/bin/python" -c "import torch, diffusers; assert torch.cuda.is_available(); diffusers.Flux2KleinPipeline" \
    2>"$HERE/.venv/install-check.log" \
    || stop "the image engine installed but cannot use the graphics card. The reason is in $HERE/.venv/install-check.log"
  say "The engine is installed."
  if [ "$ASK" = yes ]; then "$HERE/imagine" download klein; else say "Get the model (16 GB) with: ./imagine download klein"; fi
  say ""
  say "Done. Start the app with:  ./imagine"
  say "Check the setup with:      ./imagine doctor"
  exit 0
fi

[ "$(uname -s)" = Darwin ] && [ "$(uname -m)" = arm64 ] \
  || stop "this kit runs on a Mac with an Apple Silicon (M-series) chip, on Linux, and on Windows under WSL."

RAM_GB=$(( $(sysctl -n hw.memsize) / 1073741824 ))
[ "$RAM_GB" -ge 16 ] || say "Note: this Mac has ${RAM_GB} GB of memory. Renders need 16 GB and may fail here."

# Python 3.12, the version the pinned packages were tested on. uv fetches it
# when it is missing; without uv, a python3.12 must already be installed.
if command -v uv >/dev/null 2>&1; then
  say "Creating the environment with uv (Python $PYTHON_VERSION)."
  uv venv --quiet --clear --python "$PYTHON_VERSION" "$HERE/.venv" \
    || stop "uv could not provide Python $PYTHON_VERSION. Check the network, then run ./install.sh again."
  INSTALL=(uv pip install --quiet --python "$HERE/.venv/bin/python" --constraint "$HERE/constraints.txt")
elif command -v "python$PYTHON_VERSION" >/dev/null 2>&1; then
  say "Creating the environment with python$PYTHON_VERSION."
  "python$PYTHON_VERSION" -m venv --clear "$HERE/.venv"
  "$HERE/.venv/bin/python" -m pip install --quiet --upgrade pip
  INSTALL=("$HERE/.venv/bin/python" -m pip install --quiet --constraint "$HERE/constraints.txt")
else
  stop "Python $PYTHON_VERSION was not found. Install one of these, then run ./install.sh again:
  brew install uv            (recommended: it fetches the right Python by itself)
  brew install python@$PYTHON_VERSION"
fi

say "Installing the image engine (mflux $MFLUX_VERSION). This downloads about 1 GB the first time."
"${INSTALL[@]}" "mflux==$MFLUX_VERSION"
[ -x "$HERE/.venv/bin/mflux-generate-flux2" ] || stop "the image engine did not install. Run ./install.sh again and read the error above it."
# Installed is not the same as working: start the engine once and make sure it loads.
"$HERE/.venv/bin/mflux-generate-flux2" --help >/dev/null 2>"$HERE/.venv/install-check.log" \
  || stop "the image engine installed but does not start. The reason is in $HERE/.venv/install-check.log"

chmod +x "$HERE/imagine"
say "The engine is installed."

if "$HERE/imagine" models | grep -q "^klein .* ready"; then
  say "The default model is already downloaded."
elif [ "$ASK" = no ]; then
  say "Skipping the model download. Get it later with: ./imagine download klein"
else
  FREE_GB=$(( $(df -k "$HOME" | awk 'NR==2 {print $4}') / 1048576 ))
  say "The default model, FLUX.2 klein 4B, is a 16 GB download. This disk has ${FREE_GB} GB free."
  [ "$FREE_GB" -ge 20 ] || stop "not enough free disk for the model. Free some space, then run: ./imagine download klein"
  if [ "$ASK" = ask ]; then
    if [ -t 0 ]; then
      printf 'Download it now? [Y/n] '
      read -r reply
      case "$reply" in n|N|no|No) ASK=no ;; *) ASK=yes ;; esac
    else
      ASK=no
      say "Not downloading without a terminal to ask in. Get it with: ./imagine download klein"
    fi
  fi
  [ "$ASK" = yes ] && "$HERE/imagine" download klein
fi

say ""
say "Done. Start the app with:  ./imagine"
say "Check the setup with:      ./imagine doctor"
