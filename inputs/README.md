# Inputs

Put the text files you want read aloud in this folder, then pass the file name:

```
python generate.py --path=test.txt
```

`test.txt` is an English sample you can try right away, and `testi.txt` is a Finnish
one (`--path=testi.txt --lang=fi`). A file outside this folder works too:
`--path=/path/to/story.txt`.

## How the text is read

- **Paragraphs:** lines next to each other are one paragraph and are read continuously,
  so you can wrap long lines freely.
- **Pauses:** one empty line is a pause (0.8 s by default). Two empty lines are twice
  as long, three are three times as long. Change the length with `--pause`.
- **Long paragraphs:** these are split at sentence ends into chunks of up to 250
  characters (`--max-chars`), with a short gap between chunks (`--gap`).

## Tips

- Save files as plain text in UTF-8.
- Write the way people talk: contractions, shorter sentences, and commas where you
  would breathe. Stiff text sounds robotic in any voice.
- Spell out things that should be spoken a certain way, such as numbers,
  abbreviations and symbols.
- For text that is not in English, pass the language with `--lang`, for example
  `--lang=fi`. The main README lists the codes.
- With `--turbo` you can add tags such as `[laugh]` and `[sigh]` in the text.
