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

Run the test suite:

```
python3 -m unittest discover -s tests
```

## Status

This project is built autonomously, one milestone at a time, and each change
is gated on its automated tests passing before it is kept.
