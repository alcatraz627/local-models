"""Tell voices apart: turn a stretch of speech into a voice print, and compare prints.

A voice print is a list of 256 numbers that stays close for one person and moves
away for another, whatever they are saying. `lm hear` uses it to give each real
speaker one label: across the windows of a long call, and sentence by sentence
in live notes. It needs no names and stores none.

The network is WeSpeaker's ResNet34, in the MLX port published as
mlx-community/wespeaker-voxceleb-resnet34-LM (MIT). The layer names below match
that port's weights file.
"""
import re
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
import numpy as np

REPO = "mlx-community/wespeaker-voxceleb-resnet34-LM"
RATE = 16000
MIN_S = 1.0      # under a second of speech there is too little voice to print

# Measured on a 41-minute real call. Two halves of one person's speech scored 0.96 to
# 0.99. Two different people on the same line scored 0.82. So a join needs 0.88.
SAME = 0.88
# A label with little speech has a noisy print and cannot reach 0.88 (19 s of one
# speaker scored 0.76 against 15 minutes of the same person). It is attached to its
# closest voice at this lower bar, and only when no other voice is nearly as close.
BRIEF_S = 20.0
LIKELY = 0.70
CLEAR_BY = 0.08
# One sentence against a running voice is noisier still: same person 0.55 to 0.91,
# a similar-sounding other person 0.44 to 0.76. Live labels are a first guess.
LIVE_SAME = 0.62
# Cutting a sentence in two is costly when it is wrong: the tail is too short to hear
# properly. So a cut needs a clearly different voice on both sides, each at least 1.5 s.
SPLIT_BELOW = 0.50
SPLIT_MIN_S = 1.5


class Block(nn.Module):
    def __init__(self, cin: int, cout: int, stride: int):
        super().__init__()
        self.conv1 = nn.Conv2d(cin, cout, 3, stride=stride, padding=1)
        self.bn1 = nn.BatchNorm(cout)
        self.conv2 = nn.Conv2d(cout, cout, 3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm(cout)
        self.has_shortcut = stride != 1 or cin != cout
        if self.has_shortcut:
            self.shortcut_conv = nn.Conv2d(cin, cout, 1, stride=stride, padding=0)
            self.shortcut_bn = nn.BatchNorm(cout)

    def __call__(self, x):
        out = self.bn2(self.conv2(nn.relu(self.bn1(self.conv1(x)))))
        if self.has_shortcut:
            x = self.shortcut_bn(self.shortcut_conv(x))
        return nn.relu(out + x)


class VoiceNet(nn.Module):
    def __init__(self, width: int = 32):
        super().__init__()
        self.conv1 = nn.Conv2d(1, width, 3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm(width)
        self.layer1 = self._stack(width, width, 3, 1)
        self.layer2 = self._stack(width, width * 2, 4, 2)
        self.layer3 = self._stack(width * 2, width * 4, 6, 2)
        self.layer4 = self._stack(width * 4, width * 8, 3, 2)
        self.fc = nn.Linear(width * 8 * 10 * 2, 256)

    @staticmethod
    def _stack(cin, cout, count, stride):
        return nn.Sequential(Block(cin, cout, stride), *[Block(cout, cout, 1) for _ in range(count - 1)])

    def __call__(self, feats):
        """feats is (batch, time, 80 mel bins); returns (batch, 256)."""
        x = mx.transpose(mx.expand_dims(feats, -1), (0, 2, 1, 3))    # to (batch, mel, time, 1)
        x = nn.relu(self.bn1(self.conv1(x)))
        x = self.layer4(self.layer3(self.layer2(self.layer1(x))))
        stats = mx.concatenate([mx.mean(x, axis=2), mx.sqrt(mx.var(x, axis=2) + 1e-7)], axis=-1)
        return self.fc(stats.reshape(stats.shape[0], -1))


_net = None


def net() -> VoiceNet:
    """The voice network, loaded once per process (26 MB, fetched on first use)."""
    global _net
    if _net is None:
        from huggingface_hub import snapshot_download
        weights = mx.load(str(Path(snapshot_download(REPO, allow_patterns=["weights.npz"])) / "weights.npz"))
        pairs = []
        for key, value in weights.items():
            if not key.startswith("resnet.") or key.endswith("num_batches_tracked"):
                continue
            key = key[len("resnet."):].replace(".shortcut.0.", ".shortcut_conv.").replace(".shortcut.1.", ".shortcut_bn.")
            key = re.sub(r"^seg_1\.", "fc.", key)
            key = re.sub(r"(layer[1-4])\.(\d+)\.", r"\1.layers.\2.", key)
            pairs.append((key, value))
        model = VoiceNet()
        model.load_weights(pairs, strict=False)
        model.eval()
        _net = model
    return _net


def mel_features(audio: np.ndarray) -> np.ndarray:
    """80 log-mel bands every 10 ms, the way the network was trained to see speech."""
    x = audio.astype(np.float64) * 32768.0
    size, hop, nfft = 400, 160, 512
    if len(x) < size:
        x = np.pad(x, (0, size - len(x)))
    count = 1 + (len(x) - size) // hop
    idx = np.arange(size)[None, :] + hop * np.arange(count)[:, None]
    frames = x[idx]
    frames = frames - frames.mean(axis=1, keepdims=True)
    frames = np.concatenate([frames[:, :1], frames[:, 1:] - 0.97 * frames[:, :-1]], axis=1)   # lift the high end
    frames = frames * (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(size) / (size - 1))) ** 0.85
    power = np.abs(np.fft.rfft(frames, nfft, axis=1)) ** 2

    def to_mel(f):
        return 1127.0 * np.log(1.0 + f / 700.0)
    edges = np.linspace(to_mel(20.0), to_mel(RATE / 2), 82)
    bins = to_mel(np.arange(nfft // 2 + 1) * RATE / nfft)
    left, mid, right = edges[:-2, None], edges[1:-1, None], edges[2:, None]
    bank = np.maximum(0.0, np.minimum((bins[None, :] - left) / (mid - left), (right - bins[None, :]) / (right - mid)))
    logmel = np.log(np.maximum(power @ bank.T, 1.1920929e-07))
    return (logmel - logmel.mean(axis=0, keepdims=True)).astype(np.float32)


def print_of(audio: np.ndarray):
    """The voice print of one stretch of speech, or None when it is too short to tell."""
    if len(audio) < MIN_S * RATE:
        return None
    audio = audio[:int(10 * RATE)]             # ten seconds says as much as a minute
    v = np.array(net()(mx.array(mel_features(audio)[None])))[0]
    return v / (np.linalg.norm(v) + 1e-9)


def closeness(a, b) -> float:
    """How alike two prints are: 1.0 is identical, near 0 is unrelated."""
    return float(np.dot(a, b))


def label_print(audio: np.ndarray, segs, most: int = 10):
    """One print for a speaker label, from its longest turns. Also says how much speech it rests on."""
    usable = sorted((s for s in segs if s["end"] - s["start"] >= MIN_S), key=lambda s: s["start"] - s["end"])[:most]
    prints, weight = [], 0.0
    for s in usable:
        p = print_of(audio[int(s["start"] * RATE):int(s["end"] * RATE)])
        if p is not None:
            dur = min(10.0, s["end"] - s["start"])
            prints.append(p * dur)
            weight += dur
    if not prints:
        return None, 0.0
    v = np.sum(prints, axis=0)
    return v / (np.linalg.norm(v) + 1e-9), weight


def join_labels(prints: dict):
    """Decide which labels are the same person, from their prints alone.

    `prints` maps a label to (print, seconds of speech the print rests on).
    Returns who each label belongs to, how many joins were sure, and how many
    were only likely.

    Sure joins come first: the closest pair at or above SAME is joined, their
    prints are pooled, and it repeats. Then each brief label is attached to its
    closest voice if that voice is close enough and clearly closer than the next.
    """
    prints = dict(prints)
    owner = {label: label for label in prints}
    sure = likely = 0

    def absorb(keep, gone):
        (pa, wa), (pb, wb) = prints[keep], prints[gone]
        v = pa * wa + pb * wb
        prints[keep] = (v / (np.linalg.norm(v) + 1e-9), wa + wb)
        del prints[gone]
        for label, o in owner.items():
            if o == gone:
                owner[label] = keep

    while len(prints) > 1:
        labels = list(prints)
        best, pair = SAME, None
        for i, a in enumerate(labels):
            for b in labels[i + 1:]:
                c = closeness(prints[a][0], prints[b][0])
                if c >= best:
                    best, pair = c, (a, b)
        if pair is None:
            break
        absorb(*pair)
        sure += 1
    for brief in sorted((lb for lb in prints if prints[lb][1] < BRIEF_S), key=lambda lb: prints[lb][1]):
        others = sorted(((closeness(prints[brief][0], prints[o][0]), o) for o in prints if o != brief), reverse=True)
        if not others:
            break
        top, target = others[0]
        runner_up = others[1][0] if len(others) > 1 else -1.0
        if top >= LIKELY and top - runner_up >= CLEAR_BY:
            absorb(target, brief)
            likely += 1
    return owner, sure, likely


def merge_voices(segs, audio: np.ndarray):
    """Give each real speaker one label by joining labels whose voices match.

    A long call is read in windows, and a person who is quiet where two windows
    meet comes out with two or three labels. This prints every label's voice and
    joins the ones that are the same person. Labels with too little speech to
    print are left as they are.

    Returns the relabelled turns and a count of sure joins, likely joins, and
    labels that could not be checked.
    """
    by_label = {}
    for s in segs:
        by_label.setdefault(s["speaker"], []).append(s)
    prints, unchecked = {}, 0
    for label, own in by_label.items():
        p, weight = label_print(audio, own)
        if p is None:
            unchecked += 1
        else:
            prints[label] = (p, weight)
    owner, sure, likely = join_labels(prints)
    # Number people in the order they first speak.
    order, out = {}, []
    for s in segs:
        o = owner.get(s["speaker"], s["speaker"])
        order.setdefault(o, str(len(order)))
        out.append({**s, "speaker": order[o]})
    return out, {"sure": sure, "likely": likely, "unchecked": unchecked, "people": len(order)}


def split_at_voice_change(audio: np.ndarray, printer=None, same: float = SPLIT_BELOW, min_pause_s: float = 0.3):
    """Cut one stretch of speech where the speaker changes at a pause.

    Live audio is cut at long pauses, so a quick exchange ("Can we stream it?"
    "Yes.") arrives as one stretch. This looks at each short pause inside it and
    cuts there when the voice before and the voice after are not the same
    person. A stretch with one speaker comes back whole.

    Returns (start_second, audio) pieces in order.
    """
    printer = printer or print_of
    n = int(0.03 * RATE)
    frames = len(audio) // n
    if frames < 2:
        return [(0.0, audio)]
    levels = np.sqrt(np.mean(audio[:frames * n].reshape(frames, n) ** 2, axis=1))
    quiet = levels < max(0.004, 0.12 * float(np.percentile(levels, 90)))
    need = int(min_pause_s / 0.03)
    cuts, run = [], 0
    for i, q in enumerate(quiet):
        run = run + 1 if q else 0
        if run == need:
            cuts.append((i - need // 2) * n)       # the middle of the pause
    pieces, last = [], 0
    for c in cuts:
        if c - last >= SPLIT_MIN_S * RATE and len(audio) - c >= SPLIT_MIN_S * RATE:
            pieces.append((last, c))
            last = c
    pieces.append((last, len(audio)))
    if len(pieces) == 1:
        return [(0.0, audio)]
    out, start, end = [], pieces[0][0], pieces[0][1]
    held = printer(audio[start:end])
    for a, b in pieces[1:]:
        p = printer(audio[a:b])
        if held is not None and p is not None and closeness(held, p) < same:
            out.append((start / RATE, audio[start:end]))
            start, held = a, p
        end = b
    out.append((start / RATE, audio[start:end]))
    return out


class LiveVoices:
    """Labels each utterance of a live session as it arrives.

    The first voice heard is speaker 0. Each later utterance goes to the known
    voice it is closest to, or becomes a new speaker when it is close to none.
    An utterance too short to print gets no label.
    """

    def __init__(self, same: float = LIVE_SAME):
        self.same, self.known = same, []     # known[i] = [print, seconds heard]

    def label(self, audio: np.ndarray):
        p = print_of(audio)
        if p is None:
            return None
        scores = [closeness(p, k[0]) for k in self.known]
        if scores and max(scores) >= self.same:
            i = int(np.argmax(scores))
            dur = min(10.0, len(audio) / RATE)
            v = self.known[i][0] * self.known[i][1] + p * dur
            self.known[i] = [v / (np.linalg.norm(v) + 1e-9), self.known[i][1] + dur]
            return str(i)
        self.known.append([p, min(10.0, len(audio) / RATE)])
        return str(len(self.known) - 1)
