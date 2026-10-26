import sys

from .attention import run_attention


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    text = " ".join(argv) if argv else "the cat sat on the mat"

    result = run_attention(text)
    tokens = result["tokens"]
    print("tokens:", tokens)
    for i, row in enumerate(result["weights"]):
        formatted = ", ".join(f"{w:.3f}" for w in row)
        print(f"{tokens[i]!r:>12}: [{formatted}]")


if __name__ == "__main__":
    main()
