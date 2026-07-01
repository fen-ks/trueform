"""trueform command-line interface (standard-library only, zero extra deps).

Examples:
    trueform "It is important to note that we utilize this."
    trueform --file draft.txt --tone professional --strength heavy
    cat draft.md | trueform --provider ollama --model llama3.1 -o out.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from trueform.config import HumanizeConfig, Strength, Tone
from trueform.pipeline.humanizer import Humanizer
from trueform.providers import ProviderError


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def _read_input(text: str | None, file: str | None) -> str:
    if file:
        return Path(file).read_text(encoding="utf-8")
    if text:
        return text
    if not sys.stdin.isatty():
        return sys.stdin.read()
    _eprint("No input. Pass text as an argument, use --file, or pipe via stdin.")
    raise SystemExit(2)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="trueform",
        description="Make AI-assisted or stiff writing sound like a real person - yours.",
    )
    p.add_argument("text", nargs="?", help="Text to humanize. Omit to use --file or stdin.")
    p.add_argument("-f", "--file", help="Read input from a file.")
    p.add_argument("-o", "--output", help="Write result to a file instead of stdout.")
    p.add_argument(
        "-t", "--tone", choices=[t.value for t in Tone], default=Tone.NATURAL.value,
        help="Target voice/register.",
    )
    p.add_argument(
        "-s", "--strength", choices=[s.value for s in Strength], default=Strength.MEDIUM.value,
        help="How hard to rewrite.",
    )
    p.add_argument(
        "-p", "--provider",
        help="anthropic | openai | ollama | mock (auto-detected from env if omitted).",
    )
    p.add_argument("-m", "--model", help="Override the model name.")
    p.add_argument("--api-key", help="API key (else read from environment).")
    p.add_argument("--base-url", help="Override provider endpoint URL.")
    p.add_argument("--temperature", type=float, default=0.9, help="Sampling temperature.")
    p.add_argument("-i", "--instructions", help="Extra guidance for the rewrite.")
    p.add_argument("-q", "--quiet", action="store_true", help="Print only the result text.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = _read_input(args.text, args.file)

    config = HumanizeConfig(
        tone=Tone(args.tone),
        strength=Strength(args.strength),
        provider=args.provider,
        model=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
        temperature=args.temperature,
        extra_instructions=args.instructions,
    )

    try:
        if not args.quiet:
            _eprint(f"Humanizing with {args.provider or 'auto'} ...")
        result = Humanizer(config).run(source)
    except ProviderError as e:
        _eprint(f"Provider error: {e}")
        return 1
    except ValueError as e:
        _eprint(str(e))
        return 2

    if args.output:
        Path(args.output).write_text(result.text, encoding="utf-8")
        if not args.quiet:
            _eprint(f"Wrote {args.output}")
        return 0

    if not args.quiet:
        _eprint("--- humanized ---")
    print(result.text)
    return 0


def app() -> None:
    """Console-script entry point."""
    raise SystemExit(main())


if __name__ == "__main__":
    app()
