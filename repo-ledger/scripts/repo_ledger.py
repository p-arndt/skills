#!/usr/bin/env python3
"""Repo Ledger: a small Git-native implementation ledger for coding agents."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional


VALID_STATUSES = {
    "active",
    "completed",
    "partial",
    "blocked",
    "abandoned",
    "superseded",
}
SECTION_NAMES = [
    "Goal",
    "Scope",
    "Discoveries",
    "Decisions",
    "Failures",
    "Validation",
    "Remaining risks",
    "Handoff",
]


class LedgerError(RuntimeError):
    pass


@dataclass
class TaskDocument:
    path: Path
    metadata: dict[str, Any]
    body: str


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def run_git(repo: Path, *args: str, check: bool = False) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def find_repo_root(start: Path) -> Path:
    start = start.resolve()
    root = run_git(start, "rev-parse", "--show-toplevel")
    return Path(root).resolve() if root else start


def ledger_root(repo: Path) -> Path:
    configured = os.environ.get("REPO_LEDGER_DIR")
    if configured:
        path = Path(configured)
        return path.resolve() if path.is_absolute() else (repo / path).resolve()
    return repo / ".agent-ledger"


def ensure_initialized(root: Path) -> None:
    (root / "tasks").mkdir(parents=True, exist_ok=True)
    ignore_path = root / ".gitignore"
    required = [".active.json", ".cache/"]
    existing: list[str] = []
    if ignore_path.exists():
        existing = ignore_path.read_text(encoding="utf-8").splitlines()
    changed = False
    for item in required:
        if item not in existing:
            existing.append(item)
            changed = True
    if changed or not ignore_path.exists():
        ignore_path.write_text("\n".join(existing).strip() + "\n", encoding="utf-8")


def slugify(value: str, max_len: int = 54) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return (value[:max_len].rstrip("-") or "task")


def yaml_value(value: Any) -> str:
    # JSON is valid YAML and avoids a PyYAML dependency.
    return json.dumps(value, ensure_ascii=False)


def serialize_frontmatter(metadata: dict[str, Any]) -> str:
    preferred = [
        "id",
        "title",
        "status",
        "updated",
        "base_commit",
        "branch",
        "agent",
        "tags",
        "files",
    ]
    lines = ["---"]
    for key in preferred:
        if key not in metadata:
            continue
        value = metadata[key]
        if key == "files" and isinstance(value, list) and value:
            lines.append("files:")
            for item in value:
                lines.append(f"  - {yaml_value(item)}")
        else:
            lines.append(f"{key}: {yaml_value(value)}")
    for key in sorted(set(metadata) - set(preferred)):
        lines.append(f"{key}: {yaml_value(metadata[key])}")
    lines.append("---")
    return "\n".join(lines)


def parse_scalar(raw: str) -> Any:
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def parse_task(path: Path) -> TaskDocument:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", text, re.S)
    if not match:
        raise LedgerError(f"Invalid ledger frontmatter: {path}")
    frontmatter, body = match.groups()
    metadata: dict[str, Any] = {}
    lines = frontmatter.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if ":" not in line:
            raise LedgerError(f"Invalid frontmatter line in {path}: {line}")
        key, raw = line.split(":", 1)
        key = key.strip()
        raw = raw.strip()
        if not raw:
            items: list[Any] = []
            i += 1
            while i < len(lines) and lines[i].startswith("  - "):
                items.append(parse_scalar(lines[i][4:]))
                i += 1
            metadata[key] = items
            continue
        metadata[key] = parse_scalar(raw)
        i += 1
    return TaskDocument(path=path, metadata=metadata, body=body.rstrip() + "\n")


def write_task(task: TaskDocument) -> None:
    task.metadata["updated"] = now_iso()
    content = serialize_frontmatter(task.metadata) + "\n\n" + task.body.lstrip()
    task.path.write_text(content.rstrip() + "\n", encoding="utf-8")


def default_body(title: str, goal: Optional[str]) -> str:
    goal_text = goal.strip() if goal else "Describe the intended observable result."
    return f"""# {title}

## Goal

{goal_text}

## Scope

## Discoveries

## Decisions

## Failures

## Validation

## Remaining risks

## Handoff
"""


def active_path(root: Path) -> Path:
    return root / ".active.json"


def load_active(root: Path) -> Optional[dict[str, Any]]:
    path = active_path(root)
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LedgerError(f"Invalid active state: {path}") from exc
    if not isinstance(value, dict) or "task" not in value:
        raise LedgerError(f"Invalid active state: {path}")
    return value


def save_active(root: Path, task_path: Path) -> None:
    value = {"task": task_path.name, "updated": now_iso()}
    active_path(root).write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def clear_active(root: Path) -> None:
    path = active_path(root)
    if path.exists():
        path.unlink()


def get_active_task(root: Path) -> TaskDocument:
    state = load_active(root)
    if not state:
        raise LedgerError("No active ledger task. Run `start` first.")
    path = root / "tasks" / str(state["task"])
    if not path.exists():
        raise LedgerError(f"Active task file does not exist: {path}")
    return parse_task(path)


def replace_section(body: str, section: str, new_content: str) -> str:
    if section not in SECTION_NAMES:
        raise LedgerError(f"Unknown section: {section}")
    header = f"## {section}"
    # Match only the header line's own newline (not the blank separator that
    # follows an empty section), so appending does not accrue extra blank lines.
    pattern = re.compile(
        rf"(?ms)^{re.escape(header)}[ \t]*\n(.*?)(?=^##\s|\Z)"
    )
    match = pattern.search(body)
    if not match:
        suffix = "" if body.endswith("\n") else "\n"
        return body + suffix + f"\n{header}\n\n{new_content.strip()}\n"
    start, end = match.span(1)
    replacement = "\n" + new_content.strip() + "\n\n" if new_content.strip() else "\n"
    return body[:start] + replacement + body[end:]


def section_content(body: str, section: str) -> str:
    pattern = re.compile(
        rf"(?ms)^## {re.escape(section)}\s*\n(.*?)(?=^##\s|\Z)"
    )
    match = pattern.search(body)
    return match.group(1).strip() if match else ""


def append_to_section(body: str, section: str, entry: str) -> str:
    current = section_content(body, section)
    combined = f"{current}\n\n{entry}".strip() if current else entry.strip()
    return replace_section(body, section, combined)


def changed_files(repo: Path, base_commit: Optional[str]) -> list[str]:
    files: set[str] = set()
    if base_commit:
        output = run_git(repo, "diff", "--name-only", base_commit, "--")
        if output:
            files.update(line for line in output.splitlines() if line.strip())
    else:
        output = run_git(repo, "diff", "--name-only", "--")
        if output:
            files.update(line for line in output.splitlines() if line.strip())

    untracked = run_git(repo, "ls-files", "--others", "--exclude-standard")
    if untracked:
        files.update(line for line in untracked.splitlines() if line.strip())

    files = {
        path
        for path in files
        if not path.startswith(".agent-ledger/")
        and "/.agent-ledger/" not in path
    }
    return sorted(files)


def update_changed_files(task: TaskDocument, repo: Path) -> list[str]:
    files = changed_files(repo, task.metadata.get("base_commit"))
    task.metadata["files"] = files
    write_task(task)
    return files


def iter_tasks(root: Path) -> Iterable[TaskDocument]:
    tasks_dir = root / "tasks"
    if not tasks_dir.exists():
        return []
    result = []
    for path in sorted(tasks_dir.glob("*.md"), reverse=True):
        try:
            result.append(parse_task(path))
        except LedgerError:
            continue
    return result


def first_nonempty_lines(text: str, limit: int = 3) -> list[str]:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lines.append(stripped)
        if len(lines) >= limit:
            break
    return lines


def generate_index(root: Path) -> Path:
    ensure_initialized(root)
    tasks = list(iter_tasks(root))
    lines = [
        "# Agent implementation ledger",
        "",
        "Generated by `repo-ledger`. Do not edit this file manually.",
        "",
        "| Updated | Status | Task | Files | Tags |",
        "|---|---|---|---:|---|",
    ]
    for task in tasks:
        metadata = task.metadata
        updated = str(metadata.get("updated") or "")
        updated = updated[:10]
        status = str(metadata.get("status") or "unknown")
        title = str(metadata.get("title") or metadata.get("id") or task.path.stem)
        rel = f"tasks/{task.path.name}"
        file_count = len(metadata.get("files") or [])
        tags = ", ".join(str(tag) for tag in metadata.get("tags") or [])
        safe_title = title.replace("|", r"\|")
        safe_tags = tags.replace("|", r"\|")
        lines.append(
            f"| {updated} | {status} | [{safe_title}]({rel}) | {file_count} | {safe_tags} |"
        )
    path = root / "index.md"
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def cmd_init(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path(args.repo or os.getcwd()))
    root = ledger_root(repo)
    ensure_initialized(root)
    index = generate_index(root)
    print(f"Initialized repo ledger at {root}")
    print(f"Index: {index}")


def cmd_start(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path(args.repo or os.getcwd()))
    root = ledger_root(repo)
    ensure_initialized(root)
    state = load_active(root)
    if state and not args.force:
        raise LedgerError(
            f"An active task already exists: {state['task']}. "
            "Finish it or pass --force to replace the local pointer."
        )

    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    task_id = f"{timestamp}-{slugify(args.title)}"
    path = root / "tasks" / f"{task_id}.md"
    suffix = 2
    while path.exists():
        path = root / "tasks" / f"{task_id}-{suffix}.md"
        suffix += 1

    branch = run_git(repo, "branch", "--show-current")
    if branch == "":
        branch = "detached"
    metadata = {
        "id": path.stem,
        "title": args.title.strip(),
        "status": "active",
        "updated": now_iso(),
        "base_commit": run_git(repo, "rev-parse", "HEAD"),
        "branch": branch,
        "agent": args.agent or os.environ.get("REPO_LEDGER_AGENT"),
        "tags": sorted(set(args.tags or [])),
        "files": [],
    }
    task = TaskDocument(path=path, metadata=metadata, body=default_body(args.title, args.goal))
    write_task(task)
    save_active(root, path)
    generate_index(root)
    print(f"Started: {path.relative_to(repo) if path.is_relative_to(repo) else path}")


def cmd_note(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path(args.repo or os.getcwd()))
    root = ledger_root(repo)
    task = get_active_task(root)
    section_map = {
        "scope": "Scope",
        "discoveries": "Discoveries",
        "handoff": "Handoff",
        "risks": "Remaining risks",
        "validation": "Validation",
    }
    section = section_map[args.section]
    task.body = append_to_section(task.body, section, f"- {args.text.strip()}")
    write_task(task)
    print(f"Updated {task.path.name}: {section}")


def cmd_decision(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path(args.repo or os.getcwd()))
    root = ledger_root(repo)
    task = get_active_task(root)
    lines = [f"- **Decision:** {args.text.strip()}"]
    if args.reason:
        lines.append(f"  - **Reason:** {args.reason.strip()}")
    if args.tradeoff:
        lines.append(f"  - **Trade-off:** {args.tradeoff.strip()}")
    task.body = append_to_section(task.body, "Decisions", "\n".join(lines))
    write_task(task)
    print(f"Updated {task.path.name}: Decisions")


def compact_error(value: str, max_chars: int = 800) -> str:
    value = value.strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rstrip() + "…"


def cmd_failure(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path(args.repo or os.getcwd()))
    root = ledger_root(repo)
    task = get_active_task(root)
    lines = [f"- **Approach:** {args.summary.strip()}"]
    if args.command:
        lines.append(f"  - **Command:** `{args.command.strip()}`")
    if args.error:
        error = compact_error(args.error).replace("\n", "\n    ")
        lines.append(f"  - **Evidence:** {error}")
    if args.lesson:
        lines.append(f"  - **Lesson:** {args.lesson.strip()}")
    task.body = append_to_section(task.body, "Failures", "\n".join(lines))
    write_task(task)
    print(f"Updated {task.path.name}: Failures")


def cmd_sync(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path(args.repo or os.getcwd()))
    root = ledger_root(repo)
    task = get_active_task(root)
    files = update_changed_files(task, repo)
    generate_index(root)
    print(f"Synchronized {len(files)} changed file(s).")
    for path in files:
        print(path)


def tokenize(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9][a-z0-9._/-]*", value.lower())
        if len(token) > 1
    }


def score_task(task: TaskDocument, query: str, file_queries: list[str]) -> float:
    metadata = task.metadata
    title = str(metadata.get("title") or "").lower()
    tags = " ".join(str(x) for x in metadata.get("tags") or []).lower()
    files = [str(x).lower() for x in metadata.get("files") or []]
    body = task.body.lower()

    terms = tokenize(query)
    score = 0.0
    for term in terms:
        if term in title:
            score += 7
        if term in tags:
            score += 5
        if any(term in path for path in files):
            score += 6
        if term in body:
            score += min(3, body.count(term) * 0.5)

    for requested in file_queries:
        requested = requested.lower().strip()
        if not requested:
            continue
        for path in files:
            if requested == path:
                score += 14
            elif requested in path or path in requested:
                score += 9

    status = str(metadata.get("status") or "")
    if status == "active":
        score += 0.5
    return score


def context_excerpt(task: TaskDocument) -> str:
    metadata = task.metadata
    parts = []
    for section in ["Goal", "Discoveries", "Decisions", "Failures", "Remaining risks", "Handoff"]:
        content = section_content(task.body, section)
        excerpt = first_nonempty_lines(content, 2)
        if excerpt:
            parts.append(f"**{section}:** " + " ".join(excerpt))
    return "\n\n".join(parts)


def cmd_context(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path(args.repo or os.getcwd()))
    root = ledger_root(repo)
    if not root.exists():
        print("No .agent-ledger directory exists.")
        return

    ranked = []
    for task in iter_tasks(root):
        score = score_task(task, args.query or "", args.files or [])
        if score > 0 or (not args.query and not args.files):
            ranked.append((score, task))
    ranked.sort(
        key=lambda item: (
            item[0],
            str(item[1].metadata.get("updated") or ""),
        ),
        reverse=True,
    )
    ranked = ranked[: args.limit]

    if not ranked:
        print("No relevant ledger entries found.")
        return

    for score, task in ranked:
        metadata = task.metadata
        rel = task.path.relative_to(repo) if task.path.is_relative_to(repo) else task.path
        print(f"## {metadata.get('title', task.path.stem)}")
        print(
            f"`{rel}` · status: `{metadata.get('status', 'unknown')}` "
            f"· score: `{score:.1f}`"
        )
        files = metadata.get("files") or []
        if files:
            shown = ", ".join(f"`{path}`" for path in files[:8])
            if len(files) > 8:
                shown += f", … (+{len(files) - 8})"
            print(f"\nFiles: {shown}")
        excerpt = context_excerpt(task)
        if excerpt:
            print("\n" + excerpt)
        print()


def add_many(body: str, section: str, values: list[str]) -> str:
    for value in values:
        body = append_to_section(body, section, f"- {value.strip()}")
    return body


def cmd_finish(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path(args.repo or os.getcwd()))
    root = ledger_root(repo)
    task = get_active_task(root)

    if args.status not in VALID_STATUSES - {"active"}:
        raise LedgerError(f"Invalid final status: {args.status}")

    task.metadata["files"] = changed_files(repo, task.metadata.get("base_commit"))
    task.metadata["status"] = args.status
    task.body = add_many(task.body, "Validation", args.validation or [])
    task.body = add_many(task.body, "Remaining risks", args.risk or [])
    task.body = add_many(task.body, "Handoff", args.next_steps or [])
    write_task(task)
    clear_active(root)
    generate_index(root)

    print(f"Finished {task.path.name} with status `{args.status}`.")
    print(f"Changed files: {len(task.metadata.get('files') or [])}")


def cmd_status(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path(args.repo or os.getcwd()))
    root = ledger_root(repo)
    state = load_active(root) if root.exists() else None
    if not state:
        print("No active ledger task.")
        return
    task = get_active_task(root)
    metadata = task.metadata
    print(f"Active: {metadata.get('title')}")
    print(f"File: {task.path}")
    print(f"Base commit: {metadata.get('base_commit')}")
    print(f"Changed files recorded: {len(metadata.get('files') or [])}")


def cmd_index(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path(args.repo or os.getcwd()))
    root = ledger_root(repo)
    path = generate_index(root)
    print(f"Generated {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-ledger",
        description="Maintain a compact implementation ledger for coding agents.",
    )
    parser.add_argument(
        "--repo",
        help="Repository path. Defaults to the current directory.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize .agent-ledger.")
    init.set_defaults(func=cmd_init)

    start = sub.add_parser("start", help="Start a new task entry.")
    start.add_argument("title")
    start.add_argument("--goal")
    start.add_argument("--tags", nargs="*", default=[])
    start.add_argument("--agent")
    start.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing local active-task pointer.",
    )
    start.set_defaults(func=cmd_start)

    note = sub.add_parser("note", help="Append a concise task note.")
    note.add_argument("text")
    note.add_argument(
        "--section",
        choices=["scope", "discoveries", "handoff", "risks", "validation"],
        default="discoveries",
    )
    note.set_defaults(func=cmd_note)

    decision = sub.add_parser("decision", help="Record an implementation decision.")
    decision.add_argument("text")
    decision.add_argument("--reason")
    decision.add_argument("--tradeoff")
    decision.set_defaults(func=cmd_decision)

    failure = sub.add_parser("failure", help="Record a reusable failed approach.")
    failure.add_argument("summary")
    failure.add_argument("--command")
    failure.add_argument("--error")
    failure.add_argument("--lesson")
    failure.set_defaults(func=cmd_failure)

    sync = sub.add_parser("sync", help="Derive changed files from Git.")
    sync.set_defaults(func=cmd_sync)

    context = sub.add_parser("context", help="Search relevant previous tasks.")
    context.add_argument("--query", default="")
    context.add_argument("--files", nargs="*", default=[])
    context.add_argument("--limit", type=int, default=5)
    context.set_defaults(func=cmd_context)

    finish = sub.add_parser("finish", help="Finalize the active task.")
    finish.add_argument(
        "--status",
        choices=sorted(VALID_STATUSES - {"active"}),
        default="completed",
    )
    finish.add_argument("--validation", action="append", default=[])
    finish.add_argument("--risk", action="append", default=[])
    finish.add_argument("--next", dest="next_steps", action="append", default=[])
    finish.set_defaults(func=cmd_finish)

    status = sub.add_parser("status", help="Show the active task.")
    status.set_defaults(func=cmd_status)

    index = sub.add_parser("index", help="Regenerate index.md.")
    index.set_defaults(func=cmd_index)

    return parser


def main() -> int:
    # Force UTF-8 output so non-ASCII separators render correctly on
    # Windows consoles (cp1252/cp437) instead of appearing as mojibake.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except LedgerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
