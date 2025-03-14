"""Graders for Tasks 1-4 (setup, history forensics, restore, reset and reflog)."""
from __future__ import annotations

import re
from typing import List, Sequence

from .context import Ctx
from .facts import Facts
from .framework import Task
from .textutil import (
    all_shas, get_answer, last_nonblank_line, oneline_entries,
    parse_config_list, parse_status, resolve, sha_matches, sha_set_equals,
)

PLACEHOLDER_NAMES = {"your full name", "your name", "name", "student", "student name", "full name"}
PLACEHOLDER_EMAILS = {"you@example.com", "yourname@dsu.edu.in", "yourname@example.com",
                      "email@example.com", "student@example.com"}
ALIAS_LG = "log --oneline --graph --decorate"


def _valid_identity(name: str, email: str, facts: Facts) -> bool:
    """A real identity: not blank, not a template value, not one of the repo's authors."""
    if not name or "@" not in email:
        return False
    if name.lower() in PLACEHOLDER_NAMES or email.lower() in PLACEHOLDER_EMAILS:
        return False
    return name.lower() not in facts.published_names() and email.lower() not in facts.published_emails()


def grade_task1(ctx: Ctx) -> Task:
    """Task 1: clone, local identity, alias."""
    t = Task(1, "Setup and configuration", 5, ctx.repo_mode)
    facts = ctx.facts
    cfg = parse_config_list(ctx.step("1.1"))
    name, email = cfg.get("user.name", ""), cfg.get("user.email", "")
    t.check(1, "1.1 local user.name and user.email are shown and are your own",
            lambda: _valid_identity(name, email, facts))
    t.check(1, f"1.1 alias.lg = '{ALIAS_LG}' is shown", lambda: cfg.get("alias.lg") == ALIAS_LG)
    t.check(1, "live repo: local name, email and alias.lg match what you pasted",
            lambda: (bool(name) and bool(email) and facts.config_value("user.name") == name
                     and facts.config_value("user.email") == email
                     and facts.config_value("alias.lg") == ALIAS_LG), needs_repo=True)
    remote = ctx.step("1.2")
    t.check(1, "1.2 'git remote -v' shows origin with (fetch) and (push)",
            lambda: bool(re.search(r"^origin\s+\S+\s+\(fetch\)", remote, re.M)
                         and re.search(r"^origin\s+\S+\s+\(push\)", remote, re.M)))
    lg = ctx.step("1.3")
    t.check(1, "1.3 'git lg -3' shows three commits topped by origin/main",
            lambda: (len(oneline_entries(lg)) >= 3 and sha_matches(oneline_entries(lg)[0].sha, facts.origin_tip)
                     and "origin/main" in lg))
    return t


def _answer_is_sha(answer: str, full_sha: str) -> bool:
    return sha_matches(answer, full_sha)


def grade_task2(ctx: Ctx) -> Task:
    """Task 2: read the history with log, show and blame, then answer four questions."""
    t = Task(2, "Reading the history", 20, ctx.repo_mode)
    f = ctx.facts
    s21 = ctx.step("2.1")
    t.check(2, "2.1 graph shows every published commit",
            lambda: "*" in s21 and resolve(all_shas(s21), f.full_shas)[0] >= set(f.full_shas))
    s22 = ctx.step("2.2")
    t.check(1, "2.2 --stat output covers the two newest commits and shows a 'changed' summary",
            lambda: (resolve(all_shas(s22), f.full_shas)[0] >= set(f.full_shas[:2])
                     and re.search(r"\d+ files? changed", s22) is not None))
    t.check(2, "2.3 --author=\"Ben\" lists exactly Ben's commits",
            lambda: sha_set_equals(ctx.step("2.3"), f.commits_by_author_containing("Ben")))
    t.check(2, "2.4 --since/--until lists exactly the commits of 7-9 March 2025",
            lambda: sha_set_equals(ctx.step("2.4"), f.date_range_shas()))
    t.check(1, "2.5 lists exactly the commits that touched tools/report.py",
            lambda: sha_set_equals(ctx.step("2.5"), f.report_py_shas()))
    t.check(2, "2.6 --follow lists the history of src/catalog.c across the rename",
            lambda: sha_set_equals(ctx.step("2.6"), f.follow_shas()))
    s27 = ctx.step("2.7")
    t.check(1, "2.7 'git show' of the culprit commit (shows total_copies and the range(1 loop)",
            lambda: (any(sha_matches(tok, f.culprit) for tok in all_shas(s27))
                     and "total_copies" in s27 and "range(1" in s27))
    s28 = ctx.step("2.8")
    t.check(1, "2.8 blame attributes the range(1 line to the culprit commit and its author",
            lambda: _blame_ok(s28, f))
    t.check(2, "ANSWER-1 is the SHA of the commit that broke total_copies",
            lambda: _answer_is_sha(get_answer(ctx.text, 1), f.culprit))
    t.check(2, "ANSWER-2 is the number of commits in the --follow history of src/catalog.c",
            lambda: get_answer(ctx.text, 2).isdigit() and int(get_answer(ctx.text, 2)) == len(f.follow_shas()))
    t.check(2, "ANSWER-3 is the author with the most commits",
            lambda: _name_matches(get_answer(ctx.text, 3), f.top_author()))
    t.check(2, "ANSWER-4 is the SHA of the commit that added config.txt",
            lambda: _answer_is_sha(get_answer(ctx.text, 4), f.config_commit))
    return t


def _blame_ok(text: str, facts: Facts) -> bool:
    author = facts.culprit_author()
    for line in text.split("\n"):
        if "range(1" in line:
            sha_tokens = all_shas(line)
            if any(sha_matches(tok, facts.culprit) for tok in sha_tokens) and author in line:
                return True
    return False


def _name_matches(answer: str, expected: str) -> bool:
    answer, expected = answer.lower().strip(), expected.lower()
    return len(answer) >= 3 and (answer in expected or expected in answer)


THREE_FILES = {"NOTES.txt", "README.md", "tools/helpers.py"}
TASK3_MARKERS = {
    "NOTES.txt": ["debug: temporary line"],
    "README.md": ["Draft footer", "<!-- draft -->"],
    "tools/helpers.py": ["tidy later"],
}


def _markers_absent(facts: Facts) -> bool:
    for path, markers in TASK3_MARKERS.items():
        for content in (facts.worktree_file(path), facts.file_at_head(path)):
            if content is not None and any(m in content for m in markers):
                return False
    return True


def grade_task3(ctx: Ctx) -> Task:
    """Task 3: partial staging, restore --staged and restore."""
    t = Task(3, "Undoing edits with restore (and add -p)", 10, ctx.repo_mode)
    st1, st2, st4, st5 = (parse_status(ctx.step(i)) for i in ("3.1", "3.2", "3.4", "3.5"))
    t.check(2, "3.1 three files modified, nothing staged yet",
            lambda: set(st1.unstaged) == THREE_FILES and not st1.staged)
    t.check(3, "3.2 helpers.py staged, README.md half-staged (add -p), NOTES.txt untouched",
            lambda: (set(st2.staged) == {"tools/helpers.py", "README.md"}
                     and set(st2.unstaged) == {"README.md", "NOTES.txt"}))
    s33 = ctx.step("3.3")
    t.check(1, "3.3 diff --staged --stat lists README.md and helpers.py but not NOTES.txt",
            lambda: "README.md" in s33 and "helpers.py" in s33 and "NOTES.txt" not in s33)
    t.check(2, "3.4 after restore --staged: nothing staged, all three still modified",
            lambda: not st4.staged and set(st4.unstaged) == THREE_FILES)
    t.check(1, "3.5 after restore: working tree clean", lambda: st5.clean)
    t.check(1, "live repo: you made the Task 3 edits (3.1) and none of them is in the files or in HEAD now",
            lambda: set(st1.unstaged) == THREE_FILES and _markers_absent(ctx.facts), needs_repo=True)
    return t


def _subsequence(items: Sequence[str], patterns: Sequence[str]) -> bool:
    """True if the regex patterns match items in order (not necessarily adjacent)."""
    idx = 0
    for item in items:
        if idx < len(patterns) and re.search(patterns[idx], item):
            idx += 1
    return idx == len(patterns)


SCRATCH = [r"^commit: chore: scratch 1$", r"^commit: chore: scratch 2$", r"^commit: chore: scratch 3$"]
RESET_HEAD = r"^reset: moving to HEAD[~^]"
AGAIN = r"^commit: chore: scratch 3 again$"
REFLOG_LINE_RE = re.compile(
    r"^([0-9a-fA-F]{7,40})(?:\s+\([^)]*\))?\s+HEAD@\{\d+\}:\s*(.*)$", re.M)


def _reflog_messages_oldest_first(facts: Facts) -> List[str]:
    return [e["msg"] for e in reversed(facts.reflog())]


def _recovered_with_reflog(facts: Facts) -> bool:
    """A real 'reset: moving to <sha>' that points at the 'scratch 3 again' commit."""
    for entry in facts.reflog():
        match = re.match(r"^reset: moving to ([0-9a-fA-F]{7,40})$", entry["msg"])
        if match and facts.commit_exists(match.group(1)):
            if facts.subject_of(match.group(1)) == "chore: scratch 3 again":
                return True
    return False


def grade_task4(ctx: Ctx) -> Task:
    """Task 4: reset --soft/--mixed/--hard, recover with reflog, return to origin/main."""
    t = Task(4, "reset (soft, mixed, hard) and reflog recovery", 20, ctx.repo_mode)
    f = ctx.facts
    msgs = (lambda: _reflog_messages_oldest_first(f))

    s41 = oneline_entries(ctx.step("4.1"))
    t.check(1, "4.1 log shows scratch 3, 2, 1 on top of the published tip",
            lambda: (len(s41) >= 4 and "scratch 3" in s41[0].subject and "again" not in s41[0].subject
                     and "scratch 2" in s41[1].subject and "scratch 1" in s41[2].subject
                     and sha_matches(s41[3].sha, f.origin_tip)))
    t.check(1, "live repo: reflog records the three scratch commits",
            lambda: _subsequence(msgs(), SCRATCH), needs_repo=True)

    text42 = ctx.step("4.2")
    st42, log42 = parse_status(text42), oneline_entries(text42)
    t.check(2, "4.2 after reset --soft: the change is staged, nothing unstaged",
            lambda: set(st42.staged) == {"NOTES.txt"} and not st42.unstaged)
    t.check(1, "4.2 log tip is scratch 2 and scratch 3 is gone",
            lambda: bool(log42) and "scratch 2" in log42[0].subject
            and not any("scratch 3" in e.subject for e in log42))
    t.check(1, "live repo: reflog shows commit x3, a reset, then 'scratch 3 again'",
            lambda: _subsequence(msgs(), SCRATCH + [RESET_HEAD, AGAIN]), needs_repo=True)

    text43 = ctx.step("4.3")
    st43, log43 = parse_status(text43), oneline_entries(text43)
    t.check(2, "4.3 after reset --mixed: the change is in the working directory only",
            lambda: set(st43.unstaged) == {"NOTES.txt"} and not st43.staged)
    t.check(1, "4.3 log tip is scratch 2",
            lambda: bool(log43) and "scratch 2" in log43[0].subject)
    t.check(1, "live repo: reflog shows the second reset after 'scratch 3 again'",
            lambda: _subsequence(msgs(), SCRATCH + [RESET_HEAD, AGAIN, RESET_HEAD]), needs_repo=True)

    text44 = ctx.step("4.4")
    st44, log44 = parse_status(text44), oneline_entries(text44)
    t.check(1, "4.4 after reset --hard: working tree clean", lambda: st44.clean)
    t.check(1, "4.4 log tip is scratch 1", lambda: bool(log44) and "scratch 1" in log44[0].subject)
    t.check(1, "4.4 NOTES.txt ends with 'scratch 1' (scratch 2 and 3 are gone)",
            lambda: (last_nonblank_line(text44) == "scratch 1"
                     and "scratch 2" not in text44 and "scratch 3" not in text44))
    t.check(1, "live repo: reflog shows the third reset",
            lambda: _subsequence(msgs(), SCRATCH + [RESET_HEAD, AGAIN, RESET_HEAD, RESET_HEAD]),
            needs_repo=True)

    text45 = ctx.step("4.5")
    entries45 = REFLOG_LINE_RE.findall(text45)
    t.check(1, "4.5 pasted reflog shows 'scratch 3 again' and at least three resets",
            lambda: (any(m == "commit: chore: scratch 3 again" for _, m in entries45)
                     and sum(1 for _, m in entries45 if m.startswith("reset:")) >= 3))
    t.check(1, "live repo: the pasted reflog is from this repo and you ran 'git reset --hard <sha of scratch 3 again>'",
            lambda: (f.all_exist([sha for sha, _ in entries45])
                     and _recovered_with_reflog(f)), needs_repo=True)

    text46 = ctx.step("4.6")
    log46 = oneline_entries(text46)
    t.check(1, "4.6 after recovery the log tip is 'scratch 3 again'",
            lambda: bool(log46) and "scratch 3 again" in log46[0].subject)
    t.check(1, "4.6 NOTES.txt ends with 'scratch 3' again",
            lambda: last_nonblank_line(text46) == "scratch 3")

    st47 = parse_status(ctx.step("4.7"))
    t.check(1, "4.7 status: up to date with origin/main and clean",
            lambda: st47.up_to_date and st47.clean)
    t.check(1, "live repo: reflog shows 'reset: moving to origin/main'",
            lambda: any(e["msg"] == "reset: moving to origin/main" for e in f.reflog()), needs_repo=True)
    return t
