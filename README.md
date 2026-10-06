# light-tts-kit

Local, offline text-to-speech (TTS) with voice cloning. Turn a text file into speech
on your own computer with [Chatterbox TTS](https://github.com/resemble-ai/chatterbox),
on older NVIDIA GPUs such as the GTX 1080 Ti, GTX 1060 and GTX 970. Nothing is sent to
a cloud service; after the one-time download it runs without an internet connection.

## Requirements

- An NVIDIA GPU with a working driver (see the list below). Without a usable GPU it
  falls back to the CPU, which is very slow.
- Python 3.11 (3.10 also works).
- About 8 GB of free disk space.

## Supported GPUs

| Series | Cards | Status |
|---|---|---|
| GTX 900 (Maxwell) | GTX 950, 960, 970, 980, 980 Ti, Titan X | Supported |
| GTX 10 (Pascal) | GTX 1050, 1050 Ti, 1060, 1070, 1070 Ti, 1080, 1080 Ti, Titan X / Xp | Supported, tested on a GTX 1080 Ti |
| GTX 16, RTX 20, 30, 40 | all | Should work with the same PyTorch build, not tested |
| RTX 50 | all | Not supported: these need a newer PyTorch build than setup installs |
| AMD, Intel, Apple | all | Not supported, CPU only |

Cards with 2-4 GB of memory (for example GTX 950, 960, 1050) may run out of GPU
memory, in which case generation continues on the CPU.

## Installation

Setup is the same everywhere once Python 3.11 and the NVIDIA driver are in place.
Getting those two is the part that differs between systems.

### Linux

**1. Check the NVIDIA driver**

```
nvidia-smi
```

If this prints your card and a driver version of 525 or newer, you are done with this
step. If the command is missing, install the proprietary NVIDIA driver the way your
distribution documents it (for example `sudo ubuntu-drivers install` on Ubuntu, the
RPM Fusion `akmod-nvidia` package on Fedora, the `nvidia` packages on Arch), then reboot.

GTX 900 and 10-series cards are no longer supported by the newest driver branches.
If your distribution has moved on, install its legacy 580-series driver package.

**2. Install Python 3.11 and git**

This is where distributions differ, because most ship only one Python version:

| Distribution | Commands |
|---|---|
| Debian 12 | `sudo apt install git python3 python3-venv` (its `python3` is 3.11, so use `python3` below) |
| Ubuntu 22.04 | `sudo apt install git python3.11 python3.11-venv` |
| Ubuntu 24.04 and newer, Debian 13 and newer | Not in the standard repositories. Use the uv method below. |
| Fedora | `sudo dnf install git python3.11` |
| Arch, CachyOS, Manjaro | Not in the official repositories. `sudo pacman -S git uv`, then the uv method below. |
| Anything else | Use the uv method below. |

**The uv method** works on every distribution and does not touch the system Python.
Install [uv](https://docs.astral.sh/uv/) from your package manager if it has it, or with:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then:

```
uv python install 3.11
```

This gives you a `python3.11` command. If the shell cannot find it, add `~/.local/bin`
to your PATH and open a new terminal.

**3. Get the kit and run setup**

```
git clone https://github.com/Julperi1/light-tts-kit.git
cd light-tts-kit
python3.11 setup.py
```

### Windows (PowerShell)

**1. Check the NVIDIA driver**

```
nvidia-smi
```

If this prints your card and a driver version of 528 or newer, you are done with this
step. Otherwise install or update the driver from the NVIDIA website or the NVIDIA app.

**2. Install Python 3.11 and git**

```
winget install Python.Python.3.11
winget install Git.Git
```

Close and reopen PowerShell afterwards so the new commands are found.

**3. Get the kit and run setup**

```
git clone https://github.com/Julperi1/light-tts-kit.git
cd light-tts-kit
py -3.11 setup.py
```

`py` is the Python launcher installed with Python on Windows. Use it in place of
`python` in the commands further down, for example `py generate.py --path=test.txt`.
If typing `python` opens the Microsoft Store, that is a Windows placeholder and not a
real Python.

### What setup does

Setup runs once. It lists what it is about to do and asks before doing it. It then
creates a private environment in `.venv`, installs Chatterbox, installs the PyTorch
build that matches your GPU, checks the GPU, and downloads the model weights (~3 GB).

| Option | Effect |
|---|---|
| `--yes`, `-y` | Skip the confirmation question |
| `--skip-download` | Don't download the model now (it downloads on first use) |
| `--force` | Try with a Python version other than 3.10 / 3.11 |

## Generate speech

Put a text file in `inputs/` and pass its name:

```
python generate.py --path=test.txt
```

The audio is saved to `output/test.wav`. You can run `generate.py` with any Python;
it switches to the `.venv` environment by itself.

To use your own voice, put a short recording in `voices/` and pass its name:

```
python generate.py --path=test.txt --voice=myvoice
```

See [voices/VOICES.md](voices/VOICES.md) for how to record a good clip.

## Writing the text

- Lines next to each other are one paragraph and are read continuously.
- One empty line is a pause (0.8 s by default). Two empty lines are twice as long, and so on.

See [inputs/README.md](inputs/README.md) for more.

## Options

| Option | Default | Effect |
|---|---|---|
| `--path` | required | Text file: a name in `inputs/`, or a path |
| `--out` | `output/<name>.wav` | Where to save the audio |
| `--voice` | built-in voice | Voice to clone: a name in `voices/`, or a path |
| `--pause` | 0.8 | Seconds of pause per empty line |
| `--gap` | 0.25 | Seconds of silence between sentence chunks |
| `--exaggeration` | 0.5 | Emotion, roughly 0.25 to 1.0 |
| `--cfg` | 0.5 | Pacing; lower (around 0.3) sounds less metronomic |
| `--temperature` | 0.8 | Variation between runs |
| `--max-chars` | 250 | Longest chunk sent to the model at once |
| `--seed` | none | Fix it to get the same result every time |
| `--turbo` | off | Use Chatterbox Turbo, which supports tags like `[laugh]` and `[sigh]` |
| `--cpu` | off | Force the CPU (slow) |

## Folders

| Folder | Contents |
|---|---|
| `inputs/` | Your text files |
| `output/` | Generated audio |
| `voices/` | Voice recordings to clone |
| `.venv/` | The environment `setup.py` creates |

## Troubleshooting

- **"Python 3.11 is needed"**: install Python 3.11 and run setup with it (see Installation).
- **"GPU isn't usable from PyTorch"**: update the NVIDIA driver, then run setup again.
- **Running out of GPU memory**: cards with 2-4 GB can run out. `generate.py` then
  continues on the CPU. A smaller `--max-chars` (for example 150) uses less memory.
- **"No environment found"**: run `setup.py` first.

## License

[MIT](LICENSE). This covers the scripts in this repository. Chatterbox TTS and the
other packages that setup installs have their own licenses.
