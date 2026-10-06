# light-tts-kit

Turn a text file into speech on your own computer with
[Chatterbox TTS](https://github.com/resemble-ai/chatterbox). Runs locally on older
NVIDIA cards (GTX 900 / 10-series) as well as newer ones, and can speak in your own voice.

## Requirements

- An NVIDIA GPU with a working driver. GTX 900 and 10-series are the target; newer
  cards work too. Without a usable GPU it falls back to the CPU, which is very slow.
- Python 3.11 (3.10 also works).
- About 8 GB of free disk space.

## Setup

Run once:

```
python3.11 setup.py        (Linux/macOS)
py -3.11 setup.py          (Windows)
```

It lists what it is about to do and asks before doing it. It then creates a private
environment in `.venv`, installs Chatterbox, installs the PyTorch build that matches
your GPU, checks the GPU, and downloads the model weights (~3 GB).

| Option | Effect |
|---|---|
| `--yes`, `-y` | Skip the confirmation question |
| `--skip-download` | Don't download the model now (it downloads on first use) |
| `--force` | Try with a Python version other than 3.10 / 3.11 |

If setup says Python 3.11 is needed, install it and run setup again with it. One way
that works on any Linux distribution, without touching the system Python:

```
uv python install 3.11
python3.11 setup.py
```

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

- **"Python 3.11 is needed"**: install Python 3.11 and run setup with it (see Setup).
- **"GPU isn't usable from PyTorch"**: update the NVIDIA driver, then run setup again.
- **Running out of GPU memory**: cards with 2-4 GB can run out. `generate.py` then
  continues on the CPU. A smaller `--max-chars` (for example 150) uses less memory.
- **"No environment found"**: run `setup.py` first.
