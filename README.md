# trueform

**An open-source, self-hostable text humanizer that makes AI-assisted writing sound like a real person — specifically, like *you*.**

Most "humanizer" tools are a single hidden prompt behind a paywall. `trueform` is different by design: it's free, runs on your own API key (pennies per document) or fully local via [Ollama]($0), and its quality comes from its **architecture**, not a copy-pasteable prompt.

> Status: **v0.5** — multi-pass humanization loop, local scoring, explainability reports, `doctor` setup checker, and a local web UI. Style-learning and semantic fidelity guard are on the roadmap.

---

## Quick start (free, no API key)

```powershell
cd trueform
$env:PYTHONPATH="src"

# Check your setup
python -m trueform doctor

# Score text
python -m trueform score --file examples/sample.txt --report

# Humanize (offline mock — for testing)
python -m trueform humanize --provider mock --file examples/sample.txt

# Web UI in your browser
python -m trueform serve
# open http://127.0.0.1:8765
```

For **real rewrites at $0**, install [Ollama](docs/ollama-setup.md) and use `--provider ollama`.

---

## Why this exists

AI text gets flagged and *feels* robotic for two measurable reasons:

- **Low perplexity** — every word is too predictable.
- **Low burstiness** — every sentence is about the same length and shape.

`trueform` deliberately reintroduces natural human irregularity — varied sentence length, less-predictable phrasing, broken-up rhythm — **without changing your meaning**.

## What makes it different

- **Bring your own key — no subscription, ever.** Use Claude, OpenAI, or run 100% locally with Ollama.
- **Provider-agnostic core.** Swap backends with one flag; adding a new one is a ~30-line file.
- **Content protection.** Code blocks, inline code, and URLs are shielded so the humanizer never mangles them.
- **Tone + strength control.** `natural / casual / professional / academic / personal` × `light / medium / heavy`.
- **One core, many surfaces.** A clean Python library under the CLI — the web UI and browser extension (roadmap) are thin wrappers over the same engine.

### On the roadmap (the real differentiators)

- [x] **Multi-pass pipeline** — rewrite → score → refine until target is met
- [x] **Local human-likeness scoring** — measure offline, no paid detector API
- [x] **Explainability report** — see *why* text looked AI-generated
- [ ] **Style learning** — feed it a few paragraphs you've written; it rewrites toward *your* voice
- [ ] **Semantic fidelity guard** — embedding check that your meaning didn't drift

## Install

```bash
git clone https://github.com/fen-ks/trueform
cd trueform
pip install -e ".[dev]"
```

## Usage

```bash
# Auto-detects provider from your environment (ANTHROPIC_API_KEY / OPENAI_API_KEY, else Ollama)
trueform "In conclusion, it is important to note that we utilize this tool."

# From a file, with options
trueform --file examples/sample.txt --tone professional --strength heavy

# Fully local & free (requires `ollama pull llama3.1`)
trueform -f draft.md --provider ollama --model llama3.1 -o out.md

# Pipe via stdin, print only the result
cat draft.md | trueform --quiet
```

### As a library

```python
from trueform import humanize, HumanizeConfig
from trueform.config import Tone, Strength

text = humanize(
    "It is important to note that we utilize this.",
    HumanizeConfig(tone=Tone.CASUAL, strength=Strength.MEDIUM),
)
print(text)
```

## Configuration

Set a key once and forget it:

```bash
export ANTHROPIC_API_KEY=sk-ant-...    # or OPENAI_API_KEY=sk-...
# or run Ollama locally for $0 and no key at all
```

## Architecture

```
CLI / web / extension        <- thin surfaces
        |
   Humanizer (pipeline)      <- orchestration: protect -> prompt -> rewrite -> restore
        |
   Provider (abstract)       <- anthropic | openai | ollama | mock
```

The pipeline is intentionally staged so upcoming features (scoring, multi-pass, style profiles) slot in without changing the public API.

## Development

```bash
pip install -e ".[dev]"
pytest            # tests run offline via a built-in mock provider — no API key needed
ruff check .
```

## Roadmap

- [x] v0.1 — CLI, provider abstraction, single-pass rewrite, content protection, CI
- [x] v0.5 — multi-pass pipeline, local scoring, explainability report, doctor, web UI
- [ ] v1.0 — style learning, semantic fidelity guard, polished docs
- [ ] v1.x — browser extension, PyPI release

## License

MIT © 2026 Fenet
