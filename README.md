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

This milestone adds a live page served at the daemon's root path. It is a
single self-contained HTML document with an inline SVG stage and a small
script, no build step and no external assets: the script opens an
`EventSource` to the same server's `/events` stream and, on every pushed
payload, lays tokens out along a line and draws a glowing edge between
every pair of tokens whose thickness and opacity scale with how strongly
that pair attends to each other. Existing SVG elements are updated in
place (not torn down and recreated) so CSS transitions animate the edges
and labels smoothly from one saved sentence to the next.

This milestone adds a static SVG renderer and golden tests. `svg.py`
renders a sentence's tokens and attention weights as a standalone,
non-animated SVG document that is a pure function of its inputs: the same
tokens and weights always produce byte-for-byte the same markup, with no
timestamps, randomness, or dict/set ordering involved. That determinism is
what the golden tests in `tests/test_svg.py` pin down: a fixed sentence is
asserted to produce an exact tokens list, an exact attention weight
matrix, and exact SVG markup, each captured once from a known-good run and
compared verbatim, so any future change that silently shifts the numbers
or the markup gets caught immediately.

This milestone packages the three pieces above behind a single
`attentionlive` command (`cli.py`), installed as a console script, so
nobody needs to know the module layout (`attentionlive.watch`,
`attentionlive.svg`, ...) to use the tool. `run`, `watch`, and `svg` are
now subcommands of one entry point.

## Install

Requires Python 3.9+. No third-party dependencies — everything (tokenizing,
matrix math, and the attention computation) is hand-rolled on top of the
standard library, since the point of this project is to make the mechanism
visible rather than reach for a tensor library to hide it.

```
git clone <this-repo>
cd attentionlive
pip install -e .
```

This installs a single `attentionlive` command. If you'd rather not
install anything, every subcommand below also works as
`python3 -m attentionlive <subcommand> ...` run from the repository root.

## Usage

Run the attention head over a sentence from the command line:

```
attentionlive run "the cat sat on the mat"
```

This prints the tokenized sentence and the row-normalized attention weight
matrix: row `i` shows how much token `i` attends to every other token.
Omit the sentence to run it over a default one.

Watch a scratch file and stream its attention weights as JSON over SSE
whenever you save it:

```
attentionlive watch path/to/scratch.txt
```

This starts a local HTTP server (default `http://127.0.0.1:8765`) and
prints its address. Open `http://127.0.0.1:8765/` in a browser to watch
the live page: it draws a glowing line between every pair of tokens,
weighted by how much attention they pay each other, and redraws itself
every time you save the scratch file. The raw stream backing that page is
also available directly: connect to `http://127.0.0.1:8765/events` with
any SSE client (for example `curl -N http://127.0.0.1:8765/events`) to
receive a `data: {...}` event, containing the current text, tokens, and
attention weight matrix, every time the scratch file's content changes.
Use `--host`, `--port`, and `--poll-interval` to change the bind address,
port, or how often the file is checked for changes.

Render a sentence's attention weights as a one-off static SVG file, with
no server involved:

```
attentionlive svg "the cat sat on the mat" > sentence.svg
```

Use `--width`, `--height`, and `--margin` to change the canvas size and
the horizontal margin tokens are laid out within.

Run the test suite:

```
python3 -m unittest discover -s tests
```

## Status

This project is built autonomously, one milestone at a time, and each change
is gated on its automated tests passing before it is kept.
