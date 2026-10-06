# Voices

Put a short recording of a voice in this folder and `generate.py` will speak in that voice.

## Use a voice

Save the recording here, for example `voices/myvoice.wav`, then pass its name:

```
python generate.py --path=test.txt --voice=myvoice
```

- The file extension is optional: `--voice=myvoice` and `--voice=myvoice.wav` both work.
- Supported formats: `.wav`, `.mp3`, `.flac`, `.ogg`, `.m4a`.
- A file outside this folder works too: `--voice=/path/to/clip.wav`.
- Without `--voice`, the model's built-in voice is used.

There is no training step. The clip is read on every run, so to change the voice
just swap the file or pass a different name.

## Make a good recording

- **Length:** 10-20 seconds of continuous speech. Longer does not help much.
- **Clean audio:** a quiet room, no music, no echo, no other voices. This matters
  more than the microphone.
- **Natural delivery:** speak the way you want the result to sound. The model copies
  pace and tone as well as the sound of the voice, so read a few normal sentences,
  not a list of words.
- **One speaker only.**

Record 15 seconds from your microphone on Linux:

```
arecord -f cd -d 15 voices/myvoice.wav
```

On Windows use Sound Recorder, on macOS use QuickTime Player or Voice Memos, then
save or copy the file into this folder.

## Tuning

If the result sounds flat or too dramatic, try these with your voice:

| Option | Default | Effect |
|---|---|---|
| `--exaggeration` | 0.5 | Higher is more emotional, lower is calmer |
| `--cfg` | 0.5 | Lower (around 0.3) gives looser, less metronomic pacing |
| `--temperature` | 0.8 | Higher varies more between runs |
| `--seed` | none | Fix it to get the same result every time |

## Only clone voices you are allowed to use

Use your own voice, or one you have clear permission to use.
