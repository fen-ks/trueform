"""trueform command-line interface (standard-library only, zero extra deps).

Examples:
    trueform "It is important to note that we utilize this."
    trueform --file draft.txt --tone professional --strength heavy
    trueform score "Paste a paragraph to check."
    trueform score --file draft.txt -o report.txt
    cat draft.md | trueform --provider ollama --model llama3.1 -o out.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from trueform.config import HumanizeConfig, Strength, Tone
from trueform.pipeline.humanizer import Humanizer
from trueform.pipeline.report import format_csv, format_report
from trueform.pipeline.scoring import score_text
from trueform.providers import ProviderError

_SUBCOMMANDS = frozenset({"humanize", "score"})


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


def _add_io_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("text", nargs="?", help="Input text. Omit to use --file or stdin.")
    p.add_argument("-f", "--file", help="Read input from a file.")
    p.add_argument("-o", "--output", help="Write result to a file instead of stdout.")


def _add_humanize_args(p: argparse.ArgumentParser) -> None:
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
    p.add_argument(
        "--max-passes",
        type=int,
        default=3,
        metavar="N",
        help="Rewrite up to N times until the target score is met (default: 3).",
    )
    p.add_argument(
        "--target-score",
        type=float,
        default=70.0,
        metavar="SCORE",
        help="Stop when human-likeness reaches this 0-100 score (default: 70).",
    )
    p.add_argument(
        "--single-pass",
        action="store_true",
        help="Disable the multi-pass loop (same as --max-passes 1).",
    )


def _normalize_argv(argv: list[str]) -> list[str]:
    """Keep `trueform "text"` working by defaulting to the humanize subcommand."""
    if not argv:
        return ["humanize"]
    if argv[0] in _SUBCOMMANDS or argv[0] in ("-h", "--help"):
        return argv
    return ["humanize", *argv]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="trueform",
        description="Make AI-assisted or stiff writing sound like a real person - yours.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    humanize = sub.add_parser(
        "humanize",
        help="Rewrite text so it sounds more human (default command).",
    )
    _add_io_args(humanize)
    _add_humanize_args(humanize)

    score = sub.add_parser(
        "score",
        help="Score text for human-likeness and print a CSV row.",
    )
    _add_io_args(score)
    score.add_argument(
        "--report",
        action="store_true",
        help="Print a plain-English report instead of CSV.",
    )
    score.add_argument(
        "--json",
        action="store_true",
        help="Print raw numbers as JSON instead of CSV.",
    )

    return p


def _run_humanize(args: argparse.Namespace) -> int:
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
        max_passes=1 if args.single_pass else args.max_passes,
        target_score=args.target_score,
    )

    try:
        if not args.quiet:
            passes = config.max_passes
            _eprint(
                f"Humanizing with {args.provider or 'auto'} "
                f"(up to {passes} pass{'es' if passes != 1 else ''}, "
                f"target {config.target_score}) ..."
            )
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
        before = result.scores.get("before", {}).get("overall", "?")
        after = result.scores.get("after", {}).get("overall", "?")
        passes = result.scores.get("pass_count", 1)
        _eprint(f"Score: {before} -> {after} ({passes} pass{'es' if passes != 1 else ''})")
        for note in result.notes:
            _eprint(f"  {note}")
        _eprint("--- humanized ---")
    print(result.text)
    return 0


def _run_score(args: argparse.Namespace) -> int:
    source = _read_input(args.text, args.file)
    if not source.strip():
        _eprint("Nothing to score: input text is empty.")
        return 2

    result = score_text(source)
    if args.json:
        import json

        output = json.dumps(result.to_dict(), indent=2)
    elif args.report:
        output = format_report(source, score=result)
    else:
        output = format_csv(source, score=result)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        if not getattr(args, "quiet", False):
            _eprint(f"Wrote {args.output}")
        return 0

    print(output)
    return 0


def main(argv: list[str] | None = None) -> int:
    normalized = _normalize_argv(list(argv if argv is not None else sys.argv[1:]))
    args = build_parser().parse_args(normalized)

    if args.command == "score":
        return _run_score(args)

    return _run_humanize(args)


def app() -> None:
    """Console-script entry point."""
    raise SystemExit(main())


if __name__ == "__main__":
    app()
