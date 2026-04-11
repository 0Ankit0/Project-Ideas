#!/usr/bin/env python3
"""Validate Mermaid fenced code blocks in Markdown files.

This validator extracts ```mermaid fenced blocks from Markdown files and applies
strict checks intended to catch common authoring mistakes before review.

Usage:
    python3 scripts/validate-mermaid.py
    python3 scripts/validate-mermaid.py README.md docs/*.md
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class MermaidBlock:
    file_path: Path
    start_line: int
    end_line: int
    lines: list[str]
    terminated: bool

    @property
    def first_line(self) -> str:
        return self.lines[0].strip() if self.lines else ""


def discover_markdown_files() -> list[Path]:
    return sorted(p for p in REPO_ROOT.rglob("*.md") if p.is_file())


def extract_mermaid_blocks(file_path: Path) -> list[MermaidBlock]:
    blocks: list[MermaidBlock] = []
    lines = file_path.read_text(encoding="utf-8").splitlines()
    in_mermaid = False
    block_start = 0
    collected: list[str] = []

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not in_mermaid and stripped.startswith("```"):
            lang = stripped[3:].strip().lower()
            if lang == "mermaid":
                in_mermaid = True
                block_start = idx
                collected = []
            continue

        if in_mermaid and stripped == "```":
            blocks.append(
                MermaidBlock(
                    file_path=file_path,
                    start_line=block_start,
                    end_line=idx,
                    lines=collected.copy(),
                    terminated=True,
                )
            )
            in_mermaid = False
            collected = []
            continue

        if in_mermaid:
            collected.append(line)

    if in_mermaid:
        # unterminated block still gets reported by validator
        blocks.append(
            MermaidBlock(
                file_path=file_path,
                start_line=block_start,
                end_line=len(lines),
                lines=collected.copy(),
                terminated=False,
            )
        )

    return blocks


def _strip_quoted_text(text: str) -> str:
    # Avoid false positives from characters inside quotes.
    text = re.sub(r'"[^"]*"', "", text)
    text = re.sub(r"'[^']*'", "", text)
    return text


def validate_block(block: MermaidBlock) -> list[str]:
    errors: list[str] = []
    text = "\n".join(block.lines)

    if not block.lines:
        return ["empty Mermaid block"]

    if not block.terminated:
        errors.append("unterminated Mermaid fence")

    diagram_type = block.first_line
    if not diagram_type:
        errors.append("first line must declare Mermaid diagram type (for example: flowchart TD)")

    # Basic paired delimiter checks outside quoted text.
    sanitized = _strip_quoted_text(text)
    for open_char, close_char, label in [("(", ")", "parentheses"), ("[", "]", "brackets"), ("{", "}", "braces")]:
        if sanitized.count(open_char) != sanitized.count(close_char):
            errors.append(f"unbalanced {label}")

    if diagram_type.startswith("sequenceDiagram"):
        for offset, line in enumerate(block.lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("%%"):
                continue

            # Keep participant IDs simple/alphanumeric (with underscores), per repo guidance.
            participant_match = re.match(r"^participant\s+([A-Za-z0-9_]+)(?:\s+as\s+.+)?$", stripped)
            if stripped.startswith("participant ") and not participant_match:
                errors.append(
                    f"line {block.start_line + offset}: participant IDs should be alphanumeric/underscore only"
                )

            # Validate message lines and forbid ';' in message text.
            if "->" in stripped:
                parts = re.split(r"\s*:\s*", stripped, maxsplit=1)
                if len(parts) == 2:
                    message_text = parts[1]
                    if ";" in message_text:
                        errors.append(
                            f"line {block.start_line + offset}: avoid ';' in sequenceDiagram message text"
                        )
                    if len(re.findall(r"\b(and|then|also|after that)\b", message_text, flags=re.IGNORECASE)) > 0:
                        errors.append(
                            f"line {block.start_line + offset}: prefer one action per sequenceDiagram message line"
                        )

    return errors


def validate_files(markdown_files: Iterable[Path]) -> int:
    files = list(markdown_files)
    all_errors: list[str] = []
    total_blocks = 0

    for md_path in files:
        blocks = extract_mermaid_blocks(md_path)
        total_blocks += len(blocks)
        for block in blocks:
            errors = validate_block(block)
            for err in errors:
                rel = block.file_path.relative_to(REPO_ROOT)
                all_errors.append(f"{rel}:{block.start_line}-{block.end_line}: {err}")

    if all_errors:
        print("Mermaid validation failed:\n", file=sys.stderr)
        for err in all_errors:
            print(f"- {err}", file=sys.stderr)
        print(f"\nChecked {total_blocks} Mermaid blocks across {len(files)} Markdown files.", file=sys.stderr)
        return 1

    print(f"Mermaid validation passed: checked {total_blocks} Mermaid blocks across {len(files)} Markdown files.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Mermaid blocks in Markdown files.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Markdown files to validate (defaults to all *.md files in repo).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.paths:
        files = [Path(p).resolve() for p in args.paths]
        markdown_files = [p for p in files if p.suffix.lower() == ".md" and p.exists()]
    else:
        markdown_files = discover_markdown_files()

    if not markdown_files:
        print("No Markdown files found to validate.")
        return 0

    return validate_files(markdown_files)


if __name__ == "__main__":
    raise SystemExit(main())
