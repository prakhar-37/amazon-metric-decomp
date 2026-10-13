"""Pipeline: generate -> decompose -> waterfall -> render."""
import argparse

import decompose
import generate
import render
import waterfall


def main() -> None:
    ap = argparse.ArgumentParser(description="Why Did This Metric Move? - metric decomposition")
    ap.add_argument("--mock", action="store_true", help="synthesize a demo scenario (writes data/periods.csv)")
    args = ap.parse_args()

    generate.run(mock=args.mock)
    result = decompose.run()
    waterfall.run(result)
    render.run(result)
    print("\nDone. Open output/index.html. For an LLM narrative run: python narrate.py")


if __name__ == "__main__":
    main()
