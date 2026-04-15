"""Suppression audit: scan codebase for inline suppressions of security, coverage, docs, and linting.

Detects and reports on inline suppression comments such as:
- ``# noqa`` / ``# noqa: CODE`` (ruff/flake8 linting suppressions)
- ``# nosec`` / ``# nosec: CODE`` (bandit security suppressions)
- ``# type: ignore`` / ``# type: ignore[CODE]`` (mypy/pyright type-checking suppressions)
- ``# pragma: no cover`` (coverage suppressions)
- ``# noinspection CODE`` (PyCharm/IDE suppressions)

Outputs a detailed per-file report, an ASCII histogram, and a letter grade.
"""

from __future__ import annotations

import io
import re
import sys
import tokenize
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Suppression patterns
# ---------------------------------------------------------------------------

# Each entry: (kind_label, compiled_regex).
# The first capture group (if any) captures the comma-separated rule codes.
SUPPRESSION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "noqa",
        re.compile(r"#\s*noqa(?:\s*:\s*([A-Z0-9]+(?:\s*,\s*[A-Z0-9]+)*))?", re.IGNORECASE),
    ),
    (
        "nosec",
        re.compile(r"#\s*nosec(?:\s*:?\s*([A-Z0-9]+(?:\s*,\s*[A-Z0-9]+)*))?", re.IGNORECASE),
    ),
    (
        "type:ignore",
        re.compile(r"#\s*type\s*:\s*ignore(?:\[([^\]]+)\])?", re.IGNORECASE),
    ),
    (
        "no cover",
        re.compile(r"#\s*pragma\s*:\s*no\s+cover", re.IGNORECASE),
    ),
    (
        "noinspection",
        re.compile(r"#\s*noinspection\s+(\w+)", re.IGNORECASE),
    ),
]

# Directories to skip during the scan
_SKIP_DIRS = {".venv", ".git", "node_modules", ".tox", "build", "dist", "__pycache__", "tests"}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Suppression:
    """Represents a single suppression comment found in the codebase."""

    file: str
    line_no: int
    kind: str
    codes: list[str] = field(default_factory=list)
    raw: str = ""


# ---------------------------------------------------------------------------
# Scanning helpers
# ---------------------------------------------------------------------------


def _should_skip(path: Path) -> bool:
    """Return True if any path component is in the skip-list."""
    return bool(_SKIP_DIRS.intersection(path.parts))


def _is_rhiza_repo(root: Path) -> bool:
    """Return True if *root* is the rhiza framework repo itself.

    Consumer repos have a ``.rhiza/template.yml`` file that records the upstream
    rhiza repository reference. The rhiza repo itself never has this file — its
    absence is the reliable signal that we are running inside the framework repo.
    """
    return not (root / ".rhiza" / "template.yml").exists()


def scan_file(path: Path) -> list[Suppression]:
    """Scan a single Python file and return all suppressions found.

    Uses Python's ``tokenize`` module so that only actual comment tokens are
    inspected — patterns that appear inside string literals or docstrings are
    correctly ignored.
    """
    suppressions: list[Suppression] = []
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return suppressions

    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok_type, tok_string, tok_start, _tok_end, _line in tokens:
            if tok_type != tokenize.COMMENT:
                continue
            line_no = tok_start[0]
            for kind, pattern in SUPPRESSION_PATTERNS:
                match = pattern.search(tok_string)
                if match:
                    codes_raw = match.group(1) if match.lastindex and match.group(1) else ""
                    codes = [c.strip() for c in codes_raw.split(",") if c.strip()] if codes_raw else []
                    suppressions.append(
                        Suppression(
                            file=str(path),
                            line_no=line_no,
                            kind=kind,
                            codes=codes,
                            raw=tok_string.strip(),
                        )
                    )
                    break  # count each comment line once
    except tokenize.TokenError:
        pass  # skip files with tokenization errors (e.g. incomplete source)

    return suppressions


def count_non_empty_lines(path: Path) -> int:
    """Count non-empty lines in a file."""
    try:
        return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())
    except OSError:
        return 0


# ---------------------------------------------------------------------------
# Grading
# ---------------------------------------------------------------------------

# Grade thresholds: suppressions per 100 lines of code
_GRADE_THRESHOLDS: list[tuple[float, str]] = [
    (0.0, "A+"),
    (0.5, "A"),
    (1.0, "B"),
    (2.0, "C"),
    (3.0, "D"),
]


def compute_grade(density: float) -> str:
    """Return a letter grade based on suppression density (count per 100 lines)."""
    grade = "F"
    for threshold, letter in _GRADE_THRESHOLDS:
        if density <= threshold:
            grade = letter
            break
    return grade


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

_BAR_WIDTH = 24


def _bar(count: int, max_count: int) -> str:
    """Render a fixed-width ASCII progress bar."""
    if max_count == 0:
        return "░" * _BAR_WIDTH
    filled = round(count / max_count * _BAR_WIDTH)
    return "█" * filled + "░" * (_BAR_WIDTH - filled)


_GRADE_COLOURS = {
    "A+": "[92m",  # bright green
    "A": "[32m",  # green
    "B": "[32m",  # green
    "C": "[33m",  # yellow
    "D": "[33m",  # yellow
    "F": "[31m",  # red
}
_RESET = "[0m"
_BOLD = "[1m"
_BLUE = "[36m"
_YELLOW = "[33m"
_GREEN = "[32m"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    """Run the suppression audit and print a structured report."""
    root = Path(".")

    in_rhiza_repo = _is_rhiza_repo(root)

    def _include(p: Path) -> bool:
        if _should_skip(p):
            return False
        # In consumer repos, skip the .rhiza/ framework directory entirely
        return not (not in_rhiza_repo and ".rhiza" in p.parts)

    py_files = sorted(p for p in root.rglob("*.py") if _include(p))

    all_suppressions: list[Suppression] = []
    total_lines = 0

    for py_file in py_files:
        all_suppressions.extend(scan_file(py_file))
        total_lines += count_non_empty_lines(py_file)

    # -----------------------------------------------------------------------
    # Header
    # -----------------------------------------------------------------------
    print()
    print(f"{_BOLD}{'=' * 62}{_RESET}")
    print(f"{_BOLD}  Suppression Audit Report{_RESET}")
    print(f"{_BOLD}{'=' * 62}{_RESET}")
    print()

    # -----------------------------------------------------------------------
    # Detailed per-file report
    # -----------------------------------------------------------------------
    print(f"{_BOLD}Detailed Report:{_RESET}")
    if all_suppressions:
        for sup in all_suppressions:
            codes_str = f"[{', '.join(sup.codes)}]" if sup.codes else ""
            print(f"  {_YELLOW}{sup.file}{_RESET}:{_GREEN}{sup.line_no}{_RESET}: # {sup.kind}{codes_str}")
    else:
        print(f"  {_GREEN}No inline suppressions found.{_RESET}")
    print()

    # -----------------------------------------------------------------------
    # Histogram by code
    # -----------------------------------------------------------------------
    print(f"{_BOLD}Histogram (by suppression code):{_RESET}")
    code_counter: Counter[str] = Counter()
    for sup in all_suppressions:
        if sup.codes:
            for code in sup.codes:
                code_counter[f"{sup.kind}[{code}]"] += 1
        else:
            code_counter[f"{sup.kind}"] += 1
    if code_counter:
        max_code_count = max(code_counter.values())
        total_code_count = sum(code_counter.values())
        for label, count in code_counter.most_common():
            pct = count / total_code_count * 100
            print(f"  {label:<20} {_BLUE}{_bar(count, max_code_count)}{_RESET}  {count:>3}  ({pct:.0f}%)")
    else:
        print("  (none)")
    print()

    # -----------------------------------------------------------------------
    # Summary + Grade
    # -----------------------------------------------------------------------
    density = (len(all_suppressions) / total_lines * 100) if total_lines > 0 else 0.0
    grade = compute_grade(density)
    grade_colour = _GRADE_COLOURS.get(grade, _RESET)

    print(f"{_BOLD}Summary:{_RESET}")
    print(f"  Files scanned   : {len(py_files)}")
    print(f"  Lines scanned   : {total_lines:,}")
    print(f"  Suppressions    : {len(all_suppressions)}")
    print(f"  Density         : {density:.2f} per 100 lines")
    print()
    print(f"  Grade           : {grade_colour}{_BOLD}{grade}{_RESET}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
