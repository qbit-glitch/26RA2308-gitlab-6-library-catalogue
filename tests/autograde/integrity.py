"""Detects pasted output that does not belong to the repository being graded."""
from __future__ import annotations

from typing import List, Set

from .context import Ctx
from .tasks_a import REFLOG_LINE_RE
from .textutil import line_shas, parse_config_list, sha_matches


def integrity_warnings(ctx: Ctx) -> List[str]:
    """Return human-readable warnings; an empty list means the pasted text matches this repo."""
    if not ctx.repo_mode:
        return []
    facts = ctx.facts
    warnings: List[str] = []

    pasted = parse_config_list(ctx.step("1.1"))
    for key in ("user.name", "user.email"):
        live = facts.config_value(key)
        if pasted.get(key) and live and pasted[key] != live:
            warnings.append(f"pasted {key} is '{pasted[key]}' but this repo is configured with '{live}'")

    foreign: Set[str] = set()
    for text in ctx.steps.values():
        tokens = line_shas(text) + [sha for sha, _ in REFLOG_LINE_RE.findall(text)]
        for token in tokens:
            if any(sha_matches(token, full) for full in facts.full_shas):
                continue
            if not facts.commit_exists(token):
                foreign.add(token)
    if foreign:
        shown = ", ".join(sorted(foreign)[:6])
        warnings.append(f"{len(foreign)} commit SHA(s) in the pasted text do not exist in this repository "
                        f"(e.g. {shown}); the outputs were not produced in this clone")
    return warnings
