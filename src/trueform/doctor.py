"""Environment checks for trueform setup.

`trueform doctor` runs these checks and prints plain-English guidance so you
know which provider you can use without paying anything.
"""

from __future__ import annotations

import importlib.util
import os
import platform
import shutil
import sys
from dataclasses import dataclass, field

import httpx

from trueform import __version__
from trueform.config import HumanizeConfig
from trueform.pipeline.humanizer import Humanizer

OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
RECOMMENDED_OLLAMA_MODEL = "llama3.2:3b"


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str
    hint: str | None = None
    required: bool = True


@dataclass
class DoctorReport:
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks if c.required)

    def add(
        self,
        name: str,
        ok: bool,
        detail: str,
        hint: str | None = None,
        *,
        required: bool = True,
    ) -> None:
        self.checks.append(
            CheckResult(name=name, ok=ok, detail=detail, hint=hint, required=required)
        )


def run_doctor() -> DoctorReport:
    report = DoctorReport()

    py_ok = sys.version_info >= (3, 10)
    report.add(
        "Python",
        py_ok,
        f"{platform.python_version()} ({platform.system()})",
        None if py_ok else "Install Python 3.10 or newer.",
    )

    httpx_ok = importlib.util.find_spec("httpx") is not None
    report.add(
        "httpx",
        httpx_ok,
        "installed" if httpx_ok else "missing",
        None if httpx_ok else "Run: pip install httpx",
    )

    try:
        result = Humanizer(HumanizeConfig(provider="mock")).run("We utilize it.")
        mock_ok = "use" in result.text
        report.add(
            "mock provider",
            mock_ok,
            "working (free, offline testing)" if mock_ok else "smoke test failed",
        )
    except Exception as exc:  # noqa: BLE001 - doctor should never crash
        report.add("mock provider", False, f"error: {exc}")

    ollama_cli = shutil.which("ollama")
    report.add(
        "Ollama CLI",
        ollama_cli is not None,
        ollama_cli or "not found in PATH",
        None
        if ollama_cli
        else "Install from https://ollama.com/download — then restart your terminal.",
        required=False,
    )

    ollama_api_ok = False
    ollama_models: list[str] = []
    try:
        resp = httpx.get(OLLAMA_TAGS_URL, timeout=3)
        resp.raise_for_status()
        ollama_api_ok = True
        data = resp.json()
        ollama_models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except Exception:
        pass

    report.add(
        "Ollama server",
        ollama_api_ok,
        "running on http://localhost:11434"
        if ollama_api_ok
        else "not reachable",
        None
        if ollama_api_ok
        else "Start the Ollama app, or run: ollama serve",
        required=False,
    )

    if ollama_api_ok:
        has_model = len(ollama_models) > 0
        detail = ", ".join(ollama_models[:3]) if ollama_models else "no models pulled yet"
        if len(ollama_models) > 3:
            detail += f" (+{len(ollama_models) - 3} more)"
        report.add(
            "Ollama models",
            has_model,
            detail,
            None
            if has_model
            else f"Run: ollama pull {RECOMMENDED_OLLAMA_MODEL}",
            required=False,
        )

    anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    openai = bool(os.getenv("OPENAI_API_KEY"))
    paid_detail = []
    if anthropic:
        paid_detail.append("ANTHROPIC_API_KEY set")
    if openai:
        paid_detail.append("OPENAI_API_KEY set")
    report.add(
        "paid API keys (optional)",
        True,
        ", ".join(paid_detail) if paid_detail else "none set (that's fine — use mock or Ollama)",
        required=False,
    )

    # Free path recommendation
    if ollama_api_ok and ollama_models:
        recommended = f"--provider ollama --model {ollama_models[0]}"
    else:
        recommended = "--provider mock"
    report.add("recommended now", True, recommended, required=False)

    return report


def format_doctor_report(report: DoctorReport) -> str:
    lines = [f"trueform doctor v{__version__}", "=" * 40, ""]
    icon = {True: "[ok]", False: "[!!]"}

    for check in report.checks:
        mark = icon[check.ok]
        lines.append(f"{mark} {check.name}: {check.detail}")
        if check.hint and not check.ok:
            lines.append(f"    -> {check.hint}")

    lines.append("")
    if report.ok:
        lines.append("Core setup is ready (mock provider works).")
    else:
        lines.append("Core setup has issues — fix required checks above.")

    optional_failed = [c for c in report.checks if not c.required and not c.ok]
    if optional_failed:
        lines.append("Optional upgrades available (Ollama for real rewrites at $0).")

    free = next((c for c in report.checks if c.name == "recommended now"), None)
    if free:
        lines.append("")
        lines.append(f"Try: trueform humanize {free.detail} --file examples/sample.txt")

    return "\n".join(lines)
