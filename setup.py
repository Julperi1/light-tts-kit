#!/usr/bin/env python3
"""
One-time setup for local Chatterbox TTS on NVIDIA GTX 900 / 10-series cards
(Maxwell and Pascal, e.g. GTX 970, 980 Ti, 1060, 1080 Ti). Cards up to the RTX 40-series
should work too; RTX 50-series needs a newer PyTorch build than this installs.

    python setup.py
    python setup.py --yes     (skip the confirmation question)

What it does:
  1. Creates a private virtual environment in ./.venv (nothing touches your system Python)
  2. Installs Chatterbox TTS + dependencies
  3. Swaps PyTorch for the CUDA 12.6 build -- the last official build that still
     supports Maxwell and Pascal cards (sm_52 / sm_61). Newer default builds (cu128+)
     won't run on them. Falls back to CUDA 11.8 if your NVIDIA driver is too old for 12.x.
  4. Checks the GPU actually works with that build
  5. Pre-downloads the model weights so the first generation starts right away

Use Python 3.10 or 3.11 (3.11 recommended). Needs ~8 GB free disk space.
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENV = HERE / ".venv"
PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

# Pinned so setup installs the release this kit was tested with, not whatever is newest.
CHATTERBOX_VERSION = "0.1.7"

# Tried in order; cu126 is preferred (last official Maxwell/Pascal-compatible build).
CUDA_INDEXES = ["cu126", "cu124", "cu121", "cu118"]

# CUDA 12.x builds need at least this NVIDIA driver; older drivers only run cu118.
MIN_DRIVER_CUDA12 = 528 if os.name == "nt" else 525

# Below this much VRAM, long chunks can run out of memory (generate.py then uses the CPU).
LOW_VRAM_MB = 6000


def step(msg):
    print(f"\n=== {msg} ===", flush=True)


def run(args, check=True, capture=False):
    print("  $", " ".join(str(a) for a in args), flush=True)
    return subprocess.run(
        [str(a) for a in args],
        check=check,
        text=True,
        capture_output=capture,
    )


def pip(*args, check=True):
    return run([PY, "-m", "pip", *args], check=check)


def venv_eval(code):
    r = run([PY, "-c", code], capture=True, check=False)
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


def detect_gpu():
    """Return (name, vram_mb, driver_major) for the first NVIDIA GPU, or None."""
    try:
        r = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            capture_output=True,
            timeout=30,
        )
        name, vram, driver = (f.strip() for f in r.stdout.strip().splitlines()[0].split(","))
        return name, int(vram), int(driver.split(".")[0])
    except (OSError, subprocess.TimeoutExpired, ValueError, IndexError):
        return None


def confirm(skip_download):
    """Show what setup is about to do and ask before doing it."""
    plan = [
        "Create a private virtual environment in .venv (your system Python is not touched)",
        "Install Chatterbox TTS and its dependencies into it",
        "Swap PyTorch for the CUDA build that supports your GPU",
        "Check that the GPU works",
    ]
    if not skip_download:
        plan.append("Download the model weights (~3 GB)")
    print("This setup will:\n")
    for item in plan:
        print(f"  - {item}")
    print("\nIt needs ~8 GB of disk space and takes a while.\n")
    try:
        answer = input("Continue? [Y/n] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = "n"
        print()
    if answer not in ("", "y", "yes"):
        sys.exit("Setup cancelled. Nothing was installed.")


def main():
    force ="--force" in sys.argv
    skip_download = "--skip-download" in sys.argv
    assume_yes = "--yes" in sys.argv or "-y" in sys.argv

    v = sys.version_info
    if not (v.major == 3 and v.minor in (10, 11)) and not force:
        print(
            f"You're running Python {v.major}.{v.minor}, but Python 3.11 is needed.\n"
            "Install Python 3.11, then run setup with it:\n\n"
            "    py -3.11 setup.py        (Windows)\n"
            "    python3.11 setup.py      (Linux/macOS)\n\n"
            "Or re-run with --force to try anyway."
        )
        sys.exit(1)

    if not assume_yes:
        confirm(skip_download)

    step("Creating virtual environment in .venv")
    if PY.exists() and venv_eval("import pip")[0] == 0:
        print("  .venv already exists, reusing it")
    else:
        if VENV.exists():
            print("  .venv is incomplete or broken, rebuilding it")
        # Use the real interpreter path, not a symlink/shim to it: standalone Pythons
        # (uv, pyenv) produce a venv that can't find its standard library otherwise.
        run([os.path.realpath(sys.executable), "-m", "venv", "--clear", VENV])

    step("Upgrading pip")
    # setuptools 81+ dropped pkg_resources, which Chatterbox's watermarker still imports
    pip("install", "--upgrade", "pip", "setuptools<81", "wheel")

    step("Installing Chatterbox TTS and dependencies (this takes a while)")
    pip("install", f"chatterbox-tts=={CHATTERBOX_VERSION}", "soundfile", "numpy", "setuptools<81")

    step("Swapping PyTorch for a build that supports your GPU")
    indexes = CUDA_INDEXES
    gpu = detect_gpu()
    if not gpu:
        print(
            "  WARNING: nvidia-smi didn't report a GPU. Install the NVIDIA driver if you\n"
            "  have a GTX 900 / 10-series card. Continuing anyway."
        )
    else:
        name, vram, driver = gpu
        print(f"  Found {name}  ({vram} MB, driver {driver})")
        if driver < MIN_DRIVER_CUDA12:
            print(
                f"  Driver {driver} is too old for CUDA 12 (needs {MIN_DRIVER_CUDA12}+), using the\n"
                "  CUDA 11.8 build. Updating the NVIDIA driver is recommended."
            )
            indexes = ["cu118"]
    code, out, err = venv_eval(
        "import torch, torchaudio; print(torch.__version__); print(torchaudio.__version__)"
    )
    if code != 0:
        print(err)
        sys.exit("Couldn't read the installed torch version.")
    torch_v, ta_v = (s.split("+")[0] for s in out.splitlines()[-2:])
    print(f"  Chatterbox wants torch {torch_v} / torchaudio {ta_v}")

    installed = None
    for idx in indexes:
        r = pip(
            "install",
            f"torch=={torch_v}+{idx}",
            f"torchaudio=={ta_v}+{idx}",
            # only the PyTorch index for this step, so nothing here is resolved from PyPI
            "--index-url",
            f"https://download.pytorch.org/whl/{idx}",
            check=False,
        )
        if r.returncode == 0:
            installed = idx
            break
        print(f"  No {idx} build for this version, trying next...")
    if not installed:
        sys.exit(
            "Couldn't install a CUDA build of PyTorch that supports GTX 900 / 10-series.\n"
            "Check your internet connection and that your NVIDIA driver is up to date."
        )
    print(f"  Installed torch {torch_v}+{installed}")

    step("Checking the GPU")
    code, out, err = venv_eval(
        "import torch\n"
        "assert torch.cuda.is_available(), 'CUDA not available'\n"
        "p = torch.cuda.get_device_properties(0)\n"
        "archs = [a[3:] for a in torch.cuda.get_arch_list() if a.startswith('sm_')]\n"
        "ok = any(a[:-1] == str(p.major) and int(a[-1]) <= p.minor for a in archs)\n"
        "assert ok, f'this PyTorch build does not support sm_{p.major}{p.minor} ({p.name})'\n"
        "x = torch.randn(256, 256, device='cuda'); (x @ x).sum().item()\n"
        "print(f'{p.name}  ({p.total_memory // 2**20} MB, sm_{p.major}{p.minor})')\n"
    )
    if code == 0:
        print(f"  OK: {out}")
        if gpu and gpu[1] < LOW_VRAM_MB:
            print(
                f"  NOTE: this card has {gpu[1]} MB of VRAM, which can be tight for Chatterbox.\n"
                "  If it runs out, generate.py switches to the CPU on its own. A smaller\n"
                "  --max-chars (e.g. 150) uses less memory."
            )
    else:
        print(err.splitlines()[-1] if err else "unknown error")
        print(
            "\n  WARNING: the GPU isn't usable from PyTorch. generate.py will fall back to CPU\n"
            "  (works, but very slow). Usually the fix is updating the NVIDIA driver."
        )

    if not skip_download:
        step("Downloading model weights (~3 GB, one time)")
        code, out, err = venv_eval(
            "from chatterbox.tts import ChatterboxTTS\n"
            "ChatterboxTTS.from_pretrained(device='cpu')\n"
            "print('done')"
        )
        if code != 0:
            print(err[-2000:])
            print("  Download failed; it will be retried on first run of generate.py.")
        else:
            print("  Model downloaded.")

    step("All set")
    print(
        "Generate speech with:\n\n"
        "    python generate.py --path=test.txt\n\n"
        "It reads inputs/test.txt and saves the audio to output/test.wav.\n\n"
        "Clone a voice (put 10-20 s of clean speech in voices/, see voices/VOICES.md):\n\n"
        "    python generate.py --path=test.txt --voice=myvoice\n"
    )


if __name__ == "__main__":
    main()