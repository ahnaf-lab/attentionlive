# attentionlive

A background daemon that watches a plain text scratch file, runs a minimal
hand-rolled self-attention head over whatever sentence you type, and serves a
live local webpage animating the attention weights as glowing lines between
words on every save. It turns an abstract ML diagram into something you poke
at with your own sentences.

This milestone adds the tokenizer and embedding lookup that feed the
attention core. The tokenizer splits arbitrary text into words and
punctuation/symbol marks without silently dropping any character (it
handles unicode letters, hyphenated and apostrophe-joined words, digits,
and arbitrary punctuation). The embedding lookup turns each token into a
fixed-dimension vector by hashing the token into a seed and sampling from
it, so the same token always maps to the same vector, with no training and
no learned weights. A small memoizing lookup table avoids re-hashing the
same token twice within a sentence.

This milestone also adds a watcher daemon. It polls a plain text scratch
file you point it at, and whenever the file's content changes (detected by
hashing the file, not by trusting its last-modified time, since two quick
saves can land within the same mtime tick), it recomputes the attention
matrix for the file's current text and broadcasts the result as JSON to
any locally connected client over Server-Sent Events (SSE). The only
network behavior is this local HTTP server: by default it binds to
`127.0.0.1` so the stream is reachable only from the machine running it,
never the network.

## Install

Requires Python 3.9+. No third-party dependencies — everything (tokenizing,
matrix math, and the attention computation) is hand-rolled on top of the
standard library, since the point of this project is to make the mechanism
visible rather than reach for a tensor library to hide it.

```
git clone <this-repo>
cd attentionlive
```

## Usage

Run the attention head over a sentence from the command line:

```
python3 -m attentionlive "the cat sat on the mat"
```

This prints the tokenized sentence and the row-normalized attention weight
matrix: row `i` shows how much token `i` attends to every other token.

Watch a scratch file and stream its attention weights as JSON over SSE
whenever you save it:

```
python3 -m attentionlive.watch path/to/scratch.txt
```

This starts a local HTTP server (default `http://127.0.0.1:8765/events`)
and prints its address. Connect to that URL with any SSE client (for
example `curl -N http://127.0.0.1:8765/events`) to receive a `data: {...}`
event, containing the current text, tokens, and attention weight matrix,
every time the scratch file's content changes. Use `--host`, `--port`, and
`--poll-interval` to change the bind address, port, or how often the file
is checked for changes.

Run the test suite:

```
python3 -m unittest discover -s tests
```

## Status

This project is built autonomously, one milestone at a time, and each change
is gated on its automated tests passing before it is kept.
