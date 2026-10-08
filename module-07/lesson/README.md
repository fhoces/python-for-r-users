# Module 7 audio lesson

`python-around-sql.m4b`: about 27 minutes, 9 chapters, for Apple Books (AirDrop it to
the phone, or add it to Books on the Mac and sync). It walks through the four Python
files and the R twin in words: no code is read character by character.

- `text/NN_title.txt`: the narration, one file per chapter (first line is the chapter
  title). Edit these, then rebuild.
- `cover.png`: the title card used as the cover.
- `audio/`: per-chapter MP3s, an intermediate (gitignored).

Rebuild from the repo root:

```sh
rm -rf module-07/lesson/audio
zsh tools/quiz/narrate_sections.sh module-07/lesson/text module-07/lesson/audio
~/Desktop/sandbox/audiotext/.venv/bin/python tools/quiz/make_audiobook.py \
  module-07/lesson/audio module-07/lesson/text module-07/lesson/cover.png \
  module-07/lesson/python-around-sql.m4b \
  "Python Around SQL" "python-for-r-users, module 7"
```
