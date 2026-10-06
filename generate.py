#!/usr/bin/env python3
"""
Turn a text file into speech with Chatterbox TTS.

    python generate.py --path=test.txt
    python generate.py --path=story.txt --voice=myvoice --out=story.wav
    python generate.py --path=tarina.txt --lang=fi

Text files are looked up in the inputs/ folder (a full path works too).
Voices are looked up in the voices/ folder, see voices/VOICES.md.
The result is saved to output/<text file name>.wav unless you pass --out.

Text rules:
  * Lines next to each other are one paragraph, read continuously.
  * One empty line = a pause (default 0.8 s). Two empty lines = twice as long, etc.

Run setup.py once before using this. You can run this with any Python;
it automatically switches to the environment setup.py created.
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENV = HERE / ".venv"
INPUTS = HERE / "inputs"
OUTPUT = HERE / "output"
VOICES = HERE / "voices"
VOICE_EXTS = (".wav", ".mp3", ".flac", ".ogg", ".m4a")

# Languages of Chatterbox's multilingual model. "en" uses the English-only model.
LANGUAGES = {
    "ar": "Arabic", "da": "Danish", "de": "German", "el": "Greek", "en": "English",
    "es": "Spanish", "fi": "Finnish", "fr": "French", "he": "Hebrew", "hi": "Hindi",
    "it": "Italian", "ja": "Japanese", "ko": "Korean", "ms": "Malay", "nl": "Dutch",
    "no": "Norwegian", "pl": "Polish", "pt": "Portuguese", "ru": "Russian",
    "sv": "Swedish", "sw": "Swahili", "tr": "Turkish", "zh": "Chinese",
}


def _ensure_venv():
    if Path(sys.prefix).resolve() == VENV.resolve():
        return
    py = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not py.exists():
        sys.exit("No environment found. Run   python setup.py   first.")
    sys.exit(subprocess.run([str(py), str(Path(__file__).resolve()), *sys.argv[1:]]).returncode)


if __name__ == "__main__":
    _ensure_venv()

import argparse  # noqa: E402
import inspect  # noqa: E402
import re  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402


# ---------------------------------------------------------------- text parsing

def parse_text(text):
    """Return a list of ("speech", paragraph) and ("pause", n_empty_lines) items."""
    items, para, blanks = [], [], 0
    for line in text.splitlines():
        if line.strip():
            if blanks and items:  # pause only between speech, not at start
                items.append(("pause", blanks))
            blanks = 0
            para.append(line.strip())
        else:
            if para:
                items.append(("speech", " ".join(para)))
                para = []
            blanks += 1
    if para:
        items.append(("speech", " ".join(para)))
    return items


def chunk_paragraph(paragraph, max_chars):
    """Split a paragraph into sentence-based chunks the model handles reliably."""
    sentences = re.split(r"(?<=[.!?…])[\"”’)\]]*\s+", paragraph)
    pieces = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(s) <= max_chars:
            pieces.append(s)
            continue
        # very long sentence: break at commas/semicolons, then hard-wrap words
        buf = ""
        for part in re.split(r"(?<=[,;:—–])\s+", s):
            if len(buf) + len(part) + 1 <= max_chars:
                buf = f"{buf} {part}".strip()
            else:
                if buf:
                    pieces.append(buf)
                while len(part) > max_chars:
                    cut = part.rfind(" ", 0, max_chars)
                    cut = cut if cut > 0 else max_chars
                    pieces.append(part[:cut].strip())
                    part = part[cut:].strip()
                buf = part
        if buf:
            pieces.append(buf)

    # merge short sentences into chunks up to max_chars (sounds more natural)
    chunks, buf = [], ""
    for p in pieces:
        if buf and len(buf) + len(p) + 1 > max_chars:
            chunks.append(buf)
            buf = p
        else:
            buf = f"{buf} {p}".strip()
    if buf:
        chunks.append(buf)
    return chunks


# ---------------------------------------------------------------- audio helpers

def trim_silence(wav, sr, pad_ms=40, floor_db=-45):
    """Cut leading/trailing silence so pauses come only from our own timing."""
    frame = max(1, int(sr * 0.01))
    n = len(wav) // frame
    if n == 0:
        return wav
    rms = np.sqrt(np.mean(wav[: n * frame].reshape(n, frame) ** 2, axis=1) + 1e-12)
    loud = np.where(20 * np.log10(rms / (rms.max() + 1e-12)) > floor_db)[0]
    if len(loud) == 0:
        return wav
    pad = int(sr * pad_ms / 1000)
    start = max(0, loud[0] * frame - pad)
    end = min(len(wav), (loud[-1] + 1) * frame + pad)
    return wav[start:end]


def silence(seconds, sr):
    return np.zeros(int(round(seconds * sr)), dtype=np.float32)


def find_voice(name):
    """Resolve --voice: a path, or a file name in voices/ (extension optional)."""
    given = Path(name)
    for base in (given, VOICES / given, HERE / given):
        for cand in (base, *(base.with_name(base.name + ext) for ext in VOICE_EXTS)):
            if cand.is_file():
                return cand
    return None


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="Text file -> speech (Chatterbox TTS)")
    ap.add_argument("--path", required=True, help="text file to read (a name in inputs/, or a path)")
    ap.add_argument("--out", help="output .wav (default: output/<text file name>.wav)")
    ap.add_argument("--voice", help="voice to clone: a file name in voices/ (extension optional), or a path")
    ap.add_argument("--lang", default="en", help="language of the text, e.g. fi, sv, de (en)")
    ap.add_argument("--pause", type=float, default=0.8, help="seconds of pause per empty line (0.8)")
    ap.add_argument("--gap", type=float, default=0.25, help="seconds between sentence chunks (0.25)")
    ap.add_argument("--exaggeration", type=float, default=0.5, help="emotion, 0.25-1.0 (0.5)")
    ap.add_argument("--cfg", type=float, default=0.5, help="pacing/adherence, 0.2-0.8 (0.5)")
    ap.add_argument("--temperature", type=float, default=0.8, help="variation (0.8)")
    ap.add_argument("--max-chars", type=int, default=250, help="max characters per chunk (250)")
    ap.add_argument("--seed", type=int, help="fix randomness for repeatable output")
    ap.add_argument("--turbo", action="store_true", help="use Chatterbox Turbo (supports [laugh], [sigh] tags)")
    ap.add_argument("--cpu", action="store_true", help="force CPU (slow)")
    args = ap.parse_args()

    args.lang = args.lang.lower()
    if args.lang not in LANGUAGES:
        known = ", ".join(f"{code} ({name})" for code, name in LANGUAGES.items())
        sys.exit(f"Unknown language: {args.lang}\nAvailable: {known}")
    if args.turbo and args.lang != "en":
        sys.exit("--turbo only supports English. Leave out --turbo to use --lang.")

    src = Path(args.path)
    # a bare name means a file in inputs/; paths relative to the kit folder work too
    src = next((c for c in (src, INPUTS / src, HERE / src) if c.is_file()), src)
    if not src.is_file():
        sys.exit(f"Text file not found: {args.path}  (also looked in {INPUTS})")
    if args.voice:
        voice = find_voice(args.voice)
        if not voice:
            sys.exit(f"Voice file not found: {args.voice}  (also looked in {VOICES})")
        args.voice = str(voice)
    out = Path(args.out) if args.out else OUTPUT / f"{src.stem}.wav"

    items = parse_text(src.read_text(encoding="utf-8-sig"))
    plan = []  # ("chunk", text, ends_paragraph) | ("pause", n)
    for kind, val in items:
        if kind == "pause":
            plan.append(("pause", val))
        else:
            chunks = chunk_paragraph(val, args.max_chars)
            for i, c in enumerate(chunks):
                plan.append(("chunk", c, i == len(chunks) - 1))
    total = sum(1 for p in plan if p[0] == "chunk")
    if total == 0:
        sys.exit("The text file has no text in it.")

    # Stay off the network: load the model from the local cache without asking
    # Hugging Face for updates. Must be set before huggingface_hub is imported.
    forced_offline = "HF_HUB_OFFLINE" not in os.environ
    if forced_offline:
        os.environ["HF_HUB_OFFLINE"] = "1"

    import soundfile as sf
    import torch

    device = "cuda" if torch.cuda.is_available() and not args.cpu else "cpu"
    if device == "cpu" and not args.cpu:
        print("WARNING: GPU not available, running on CPU (this will be slow).")
    if args.seed is not None:
        torch.manual_seed(args.seed)
        np.random.seed(args.seed)

    print(f"Loading model on {device} ({LANGUAGES[args.lang]})...", flush=True)
    if args.turbo:
        from chatterbox.tts_turbo import ChatterboxTurboTTS as Model
    elif args.lang != "en":
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS as Model
    else:
        from chatterbox.tts import ChatterboxTTS as Model
    try:
        model = Model.from_pretrained(device=device)
    except FileNotFoundError:
        if not forced_offline:
            raise
        # model (or part of it) isn't in the cache yet: start over with downloads
        # allowed, this once
        print("Model not downloaded yet, downloading it (one time)...", flush=True)
        env = {**os.environ, "HF_HUB_OFFLINE": "0"}
        sys.exit(subprocess.run([sys.executable, *sys.argv], env=env).returncode)
    except torch.OutOfMemoryError:
        if device == "cpu":
            raise
        print("WARNING: not enough GPU memory to load the model, using the CPU (slow).")
        torch.cuda.empty_cache()
        device = "cpu"
        model = Model.from_pretrained(device=device)
    sr = model.sr

    wanted = {
        "audio_prompt_path": args.voice,
        "language_id": args.lang,
        "exaggeration": args.exaggeration,
        "cfg_weight": args.cfg,
        "temperature": args.temperature,
    }
    accepted = inspect.signature(model.generate).parameters
    kwargs = {k: v for k, v in wanted.items() if k in accepted and v is not None}

    parts, done, t0 = [], 0, time.time()
    for step in plan:
        if step[0] == "pause":
            parts.append(silence(args.pause * step[1], sr))
            continue
        _, text, ends_para = step
        done += 1
        preview = text if len(text) <= 70 else text[:67] + "..."
        print(f"[{done}/{total}] {preview}", flush=True)
        try:
            with torch.inference_mode():
                wav = model.generate(text, **kwargs)
        except torch.OutOfMemoryError:
            # small cards (2-4 GB GTX 900/10-series) can run out mid-file: finish on CPU
            if device == "cpu":
                raise
            print("WARNING: GPU ran out of memory, continuing on the CPU (slow).")
            del model
            torch.cuda.empty_cache()
            device = "cpu"
            model = Model.from_pretrained(device=device)
            with torch.inference_mode():
                wav = model.generate(text, **kwargs)
        wav = wav.squeeze().detach().float().cpu().numpy().astype(np.float32)
        parts.append(trim_silence(wav, sr))
        if not ends_para:
            parts.append(silence(args.gap, sr))

    audio = np.concatenate(parts)
    peak = float(np.abs(audio).max())
    if peak > 0.98:
        audio *= 0.98 / peak
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), audio, sr)

    dur = len(audio) / sr
    took = time.time() - t0
    print(f"\nSaved {out}  ({dur:.1f} s of audio, took {took:.0f} s, {dur / max(took, 1e-6):.2f}x realtime)")


if __name__ == "__main__":
    main()