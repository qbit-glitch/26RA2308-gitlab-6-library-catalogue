"""Graders for Tasks 5-8 (revert, stash, untracking files, incident report)."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from typing import Dict, List, Optional

from .context import Ctx
from .facts import CULPRIT_SUBJECT, JUNK_FILES, Facts, run_git
from .framework import Task
from .textutil import (
    CC_SUBJECT_RE, LINE_SHA_RE, all_shas, line_shas, oneline_entries, parse_status,
    sha_matches, strip_decoration,
)

STASH_MESSAGE = "wip: sort by year"


# -- Task 5 -----------------------------------------------------------------
def _revert_commit(facts: Facts) -> Optional[Dict[str, str]]:
    """The local commit that reverts the culprit (or None)."""
    needle = f"This reverts commit {facts.culprit}"
    for commit in facts.local_commits():
        if needle in commit["body"]:
            return commit
    return None


def _revert_is_clean(facts: Facts) -> bool:
    commit = _revert_commit(facts)
    return commit is not None and commit["files"] == ["tools/report.py"]


def _code_env() -> Dict[str, str]:
    return dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def _python_tests_pass(facts: Facts) -> bool:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=facts.repo, env=_code_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return proc.returncode == 0


def _report_matches_expected(facts: Facts) -> bool:
    proc = subprocess.run(
        [sys.executable, "-m", "tools.report", "data/books.txt"],
        cwd=facts.repo, env=_code_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding="utf-8",
    )
    with open(os.path.join(facts.repo, "tests", "expected_report.txt"), encoding="utf-8") as handle:
        return proc.returncode == 0 and proc.stdout == handle.read()


def grade_task5(ctx: Ctx) -> Task:
    """Task 5: undo a published commit with git revert."""
    t = Task(5, "Undo a published commit with git revert", 20, ctx.repo_mode)
    f = ctx.facts
    s51 = ctx.step("5.1")
    t.check(2, "5.1 'make test' output shows the failing Python test (30 != 34)",
            lambda: re.search(r"\bFAIL", s51) is not None and re.search(r"30\s*!=\s*34", s51) is not None)
    s52 = ctx.step("5.2")
    entries52 = oneline_entries(s52)
    t.check(1, "5.2 revert output names the reverted commit",
            lambda: f'Revert "{CULPRIT_SUBJECT}"' in s52)
    t.check(1, "5.2 revert output reports '1 file changed'",
            lambda: re.search(r"\b1 file changed", s52) is not None)
    t.check(1, "5.2 log: the Revert commit sits directly on top of the published tip",
            lambda: (len(entries52) >= 2 and "Revert" in entries52[0].subject
                     and sha_matches(entries52[1].sha, f.origin_tip)))
    s53 = ctx.step("5.3")
    t.check(1, "5.3 'make test' prints ALL TESTS PASSED", lambda: "ALL TESTS PASSED" in s53)
    t.check(1, "5.3 no FAIL lines and no make errors in the output",
            lambda: bool(s53.strip()) and re.search(r"\bFAIL|\*\*\*", s53) is None)
    t.check(1, "5.4 status says the branch is ahead of origin/main by 1 commit",
            lambda: parse_status(ctx.step("5.4")).ahead == 1)
    t.check(4, "live repo: the Revert commit you pasted exists, reverts the culprit and changes only tools/report.py",
            lambda: _revert_is_clean(f) and bool(entries52)
            and sha_matches(entries52[0].sha, _revert_commit(f)["sha"]), needs_repo=True)
    t.check(3, "live repo: you committed on top of the published history without rewriting it "
               "(origin/main and the culprit are still in HEAD's history)",
            lambda: (f.head_sha() != f.origin_tip and f.origin_is_ancestor_of_head()
                     and f.is_reachable_from_head(f.culprit)), needs_repo=True)
    t.check(3, "live repo: the Python unit tests pass", lambda: _python_tests_pass(f), needs_repo=True)
    t.check(2, "live repo: python3 -m tools.report prints the expected report",
            lambda: _report_matches_expected(f), needs_repo=True)
    return t


# -- Task 6 -----------------------------------------------------------------
def _urgent_commit_exists(facts: Facts, pasted_top_sha: str) -> bool:
    """The pasted 6.3 top commit is a real local Conventional Commit that changes only CHANGELOG.md."""
    for commit in facts.local_commits():
        if CC_SUBJECT_RE.match(commit["subject"]) and commit["files"] == ["CHANGELOG.md"]:
            return sha_matches(pasted_top_sha, commit["sha"])
    return False


def grade_task6(ctx: Ctx) -> Task:
    """Task 6: shelve work in progress with git stash."""
    t = Task(6, "Shelving work with git stash", 10, ctx.repo_mode)
    f = ctx.facts
    st61 = parse_status(ctx.step("6.1"))
    t.check(1, "6.1 only tools/report.py is modified (the WIP edit)",
            lambda: set(st61.unstaged) == {"tools/report.py"} and not st61.staged)
    s62 = ctx.step("6.2")
    t.check(1, "6.2 stash list shows 'stash@{0}: On <branch>: wip: sort by year'",
            lambda: re.search(r"stash@\{0\}: On \S+: " + re.escape(STASH_MESSAGE), s62) is not None)
    t.check(1, "6.2 the working tree is clean after stashing", lambda: parse_status(s62).clean)
    entries63 = oneline_entries(ctx.step("6.3"))
    t.check(1, "6.3 newest commit has a Conventional Commit subject",
            lambda: bool(entries63) and CC_SUBJECT_RE.match(strip_decoration(entries63[0].subject)) is not None)
    t.check(1, "6.3 the commit below it is the Revert commit from Task 5",
            lambda: len(entries63) >= 2 and "Revert" in entries63[1].subject)
    s64 = ctx.step("6.4")
    st64 = parse_status(s64)
    t.check(1, "6.4 after stash pop: tools/report.py is modified again",
            lambda: set(st64.unstaged) == {"tools/report.py"} and not st64.staged)
    t.check(1, "6.4 the stash list is empty after the pop (count 0)",
            lambda: re.search(r"^\s*0\s*$", s64, re.M) is not None)
    t.check(1, "6.5 after restore: working tree clean", lambda: parse_status(ctx.step("6.5")).clean)
    t.check(1, "live repo: a stash called 'wip: sort by year' was really created",
            lambda: f.stash_evidence(STASH_MESSAGE), needs_repo=True)
    t.check(1, "live repo: the urgent fix is a Conventional Commit that changes only CHANGELOG.md",
            lambda: bool(entries63) and _urgent_commit_exists(f, entries63[0].sha), needs_repo=True)
    return t


# -- Task 7 -----------------------------------------------------------------
def grade_task7(ctx: Ctx) -> Task:
    """Task 7: untrack committed junk and ignore it."""
    t = Task(7, "Untracking files that should never be committed", 10, ctx.repo_mode)
    f = ctx.facts
    s71 = ctx.step("7.1")
    t.check(1, "7.1 git ls-files shows the four junk files",
            lambda: set(JUNK_FILES) <= {line.strip() for line in s71.split("\n")})
    s72 = ctx.step("7.2")
    t.check(1, "7.2 git rm --cached removed all four from the index",
            lambda: all(re.search(r"rm ['\"]" + re.escape(name) + r"['\"]", s72) for name in JUNK_FILES))
    st73 = parse_status(ctx.step("7.3"))
    t.check(1, "7.3 status: the four files are staged as deleted",
            lambda: all(st73.staged.get(name) == "deleted" for name in JUNK_FILES))
    t.check(1, "7.3 status: .gitignore is modified and none of the four show as untracked",
            lambda: ".gitignore" in {**st73.staged, **st73.unstaged}
            and not set(JUNK_FILES) & {u.split()[-1] for u in st73.untracked})
    entries74 = oneline_entries(ctx.step("7.4"))
    t.check(1, "7.4 the commit has a Conventional Commit subject",
            lambda: bool(entries74) and CC_SUBJECT_RE.match(strip_decoration(entries74[0].subject)) is not None)
    s75 = ctx.step("7.5")
    t.check(1, "7.5 check-ignore -v names a .gitignore rule for each of the four files",
            lambda: all(re.search(r"^\.gitignore:\d+:\S+\s+" + re.escape(name) + r"$", s75, re.M)
                        for name in JUNK_FILES))
    s76 = ctx.step("7.6")
    t.check(1, "7.6 ls -l shows all four files still exist on disk",
            lambda: "No such file" not in s76 and all(
                re.search(r"\s" + re.escape(name) + r"$", s76, re.M) for name in JUNK_FILES))
    s77 = ctx.step("7.7")
    t.check(1, "7.7 the history of config.txt still contains the commit that added it",
            lambda: len(line_shas(s77)) >= 2 and any(sha_matches(s, f.config_commit) for s in line_shas(s77)))
    t.check(1, "live repo: none of the four is tracked any more, and all four still exist on disk",
            lambda: (not set(JUNK_FILES) & f.tracked_files() and bool(entries74)
                     and f.commit_exists(entries74[0].sha)
                     and all(os.path.exists(os.path.join(f.repo, n)) for n in JUNK_FILES)),
            needs_repo=True)
    t.check(1, "live repo: git ignores all four files",
            lambda: all(f.is_ignored(n) for n in JUNK_FILES), needs_repo=True)
    return t


# -- Task 8 -----------------------------------------------------------------
def _tip_line(lines: List[str], facts: Facts) -> int:
    for index, line in enumerate(lines):
        match = LINE_SHA_RE.match(line)
        if match and sha_matches(match.group(1), facts.origin_tip):
            return index
    return -1


def _report_mentions_culprit(facts: Facts) -> bool:
    content = facts.file_at_head("INCIDENT_REPORT.md")
    if content is None:
        return False
    has_sha = any(sha_matches(tok, facts.culprit) for tok in all_shas(content))
    return has_sha and "revert" in content.lower()


def _report_commit_message_ok(facts: Facts) -> bool:
    subject = run_git(facts.repo, "log", "-1", "--format=%s", "--", "INCIDENT_REPORT.md").strip()
    return CC_SUBJECT_RE.match(subject) is not None


def grade_task8(ctx: Ctx) -> Task:
    """Task 8: commit the incident report."""
    t = Task(8, "Incident report and final history", 5, ctx.repo_mode)
    f = ctx.facts
    lines = [line for line in ctx.step("8.1").split("\n") if line.strip()]
    tip = _tip_line(lines, f)
    t.check(1, "8.1 the graph shows the published tip labelled origin/main",
            lambda: tip >= 0 and "origin/main" in lines[tip])
    t.check(1, "8.1 at least four of your own commits sit above origin/main",
            lambda: tip >= 0 and sum(1 for line in lines[:tip] if LINE_SHA_RE.match(line)) >= 4)
    t.check(2, "live repo: INCIDENT_REPORT.md is committed, names the culprit SHA and says 'revert'",
            lambda: _report_mentions_culprit(f) and f.all_exist(line_shas("\n".join(lines))), needs_repo=True)
    t.check(1, "live repo: the incident report commit has a Conventional Commit subject",
            lambda: _report_commit_message_ok(f), needs_repo=True)
    return t
