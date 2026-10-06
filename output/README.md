# Output

Generated audio is saved here, named after the text file it came from:

```
python generate.py --path=test.txt        ->  output/test.wav
```

- Running the same file again **overwrites** the previous audio. Use `--out` to keep
  both, for example `--out=output/test_take2.wav`.
- `--out` also lets you save anywhere else: `--out=/path/to/file.wav`.
- Files are WAV.
- The audio in this folder is not tracked by git; only this README is.
