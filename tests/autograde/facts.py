"""Ground truth about the repository: the published history and the student's live repo."""
from __future__ import annotations

import os
import subprocess
from collections import Counter
from typing import Dict, List, NamedTuple, Optional, Set, Tuple

CULPRIT_SUBJECT = "feat(report): speed up total_copies loop"
CONFIG_SUBJECT = "chore: add build output and local config"
DATE_ARGS = ["--since=2025-03-07 00:00 +0000", "--until=2025-03-10 00:00 +0000"]
JUNK_FILES = ["a.out", "catalog.o", "search.o", "config.txt"]


class GitError(RuntimeError):
    """Raised when the repository is not set up the way the grader expects."""


class Commit(NamedTuple):
    """A published commit."""

    sha: str
    author: str
    email: str
    subject: str


def run_git(repo: str, *args: str) -> str:
    """Run git in 'repo' and return stdout ('' on failure)."""
    return run_git_rc(repo, *args)[1]


def run_git_rc(repo: str, *args: str) -> Tuple[int, str]:
    """Run git in 'repo' and return (exit code, stdout)."""
    env = dict(os.environ, LC_ALL="C", GIT_PAGER="cat", GIT_TERMINAL_PROMPT="0")
    proc = subprocess.run(
        ["git", *args], cwd=repo, env=env, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, encoding="utf-8", errors="replace",
    )
    return proc.returncode, proc.stdout


class Facts:
    """Everything the grader needs to know about the repository."""

    def __init__(self, repo: str) -> None:
        self.repo = repo
        if run_git_rc(repo, "rev-parse", "--verify", "-q", "origin/main^{commit}")[0] != 0:
            raise GitError(
                "origin/main not found. Run the grader inside your clone of the lab "
                "repository (a clone made with 'git clone ...')."
            )
        raw = run_git(repo, "log", "origin/main", "--format=%H%x1f%an%x1f%ae%x1f%s")
        self.published: List[Commit] = [
            Commit(*line.split("\x1f")) for line in raw.splitlines() if line.strip()
        ]
        self.full_shas: List[str] = [c.sha for c in self.published]
        self.origin_tip: str = self.published[0].sha
        self.culprit: str = self._sha_for(CULPRIT_SUBJECT)
        self.config_commit: str = self._sha_for(CONFIG_SUBJECT)

    # -- published history ------------------------------------------------
    def _sha_for(self, subject: str) -> str:
        for commit in self.published:
            if commit.subject == subject:
                return commit.sha
        raise GitError(f"published history has no commit with subject '{subject}'")

    def culprit_author(self) -> str:
        """Author name of the buggy commit."""
        return next(c.author for c in self.published if c.sha == self.culprit)

    def _log_shas(self, *args: str) -> List[str]:
        out = run_git(self.repo, "log", "origin/main", "--format=%H", *args)
        return [line for line in out.splitlines() if line.strip()]

    def commits_by_author_containing(self, text: str) -> List[str]:
        """Published commits whose author name or e-mail contains 'text' (as git --author does)."""
        return self._log_shas(f"--author={text}")

    def top_author(self) -> str:
        """Name of the author with the most published commits."""
        counts = Counter(c.author for c in self.published)
        return counts.most_common(1)[0][0]

    def date_range_shas(self) -> List[str]:
        """Commits selected by the --since/--until pair used in step 2.4."""
        return self._log_shas(*DATE_ARGS)

    def report_py_shas(self) -> List[str]:
        """Commits that touched tools/report.py."""
        return self._log_shas("--", "tools/report.py")

    def follow_shas(self) -> List[str]:
        """Commits in the history of src/catalog.c, followed across the rename."""
        return self._log_shas("--follow", "--", "src/catalog.c")

    def published_emails(self) -> Set[str]:
        """E-mail addresses of the people who wrote the published history."""
        return {c.email.lower() for c in self.published}

    def published_names(self) -> Set[str]:
        """Names of the people who wrote the published history."""
        return {c.author.lower() for c in self.published}

    # -- the student's live repository ------------------------------------
    def config_value(self, key: str) -> str:
        """Value of a repository-local config key ('' if unset)."""
        return run_git(self.repo, "config", "--local", "--get", key).strip()

    def reflog(self) -> List[Dict[str, str]]:
        """HEAD reflog, newest first: [{'sha': ..., 'msg': ...}]."""
        out = run_git(self.repo, "log", "-g", "--format=%H%x1f%gs", "HEAD")
        entries = []
        for line in out.splitlines():
            sha, _, msg = line.partition("\x1f")
            entries.append({"sha": sha, "msg": msg})
        return entries

    def commit_exists(self, token: str) -> bool:
        """True if 'token' names a commit object in this repository."""
        return run_git_rc(self.repo, "cat-file", "-e", f"{token}^{{commit}}")[0] == 0

    def all_exist(self, tokens: List[str]) -> bool:
        """True if every token names a commit in this repository (and there is at least one)."""
        return bool(tokens) and all(self.commit_exists(token) for token in tokens)

    def subject_of(self, token: str) -> str:
        """Subject line of the commit named by 'token' ('' if unknown)."""
        return run_git(self.repo, "show", "-s", "--format=%s", token).strip()

    def local_commits(self) -> List[Dict[str, str]]:
        """Commits in origin/main..HEAD, newest first: sha, subject, body, files."""
        out = run_git(self.repo, "log", "origin/main..HEAD", "--format=%H")
        commits = []
        for sha in out.split():
            commits.append({
                "sha": sha,
                "subject": self.subject_of(sha),
                "body": run_git(self.repo, "show", "-s", "--format=%B", sha),
                "files": run_git(
                    self.repo, "diff-tree", "--no-commit-id", "--name-only", "-r", sha
                ).split(),
            })
        return commits

    def head_sha(self) -> str:
        """Full SHA of HEAD ('' if unborn)."""
        return run_git(self.repo, "rev-parse", "HEAD").strip()

    def origin_is_ancestor_of_head(self) -> bool:
        """True if the published history is still part of HEAD's history."""
        return run_git_rc(self.repo, "merge-base", "--is-ancestor", "origin/main", "HEAD")[0] == 0

    def is_reachable_from_head(self, sha: str) -> bool:
        """True if commit 'sha' is an ancestor of (or equal to) HEAD."""
        return run_git_rc(self.repo, "merge-base", "--is-ancestor", sha, "HEAD")[0] == 0

    def tracked_files(self) -> Set[str]:
        """Paths currently tracked in the index."""
        return set(run_git(self.repo, "ls-files").splitlines())

    def is_ignored(self, path: str) -> bool:
        """True if git ignores 'path' (it must not be tracked, or this is always False)."""
        return run_git_rc(self.repo, "check-ignore", "-q", path)[0] == 0

    def file_at_head(self, path: str) -> Optional[str]:
        """Content of 'path' in the HEAD commit (None if absent)."""
        code, out = run_git_rc(self.repo, "show", f"HEAD:{path}")
        return out if code == 0 else None

    def worktree_file(self, path: str) -> Optional[str]:
        """Content of 'path' in the working directory (None if absent)."""
        full = os.path.join(self.repo, path)
        if not os.path.isfile(full):
            return None
        with open(full, encoding="utf-8", errors="replace") as handle:
            return handle.read()

    def stash_evidence(self, message_substring: str) -> bool:
        """True if a stash entry (current or already dropped/popped) carries the message."""
        if message_substring in run_git(self.repo, "stash", "list"):
            return True
        out = run_git(self.repo, "fsck", "--unreachable", "--no-reflogs", "--no-progress")
        for line in out.splitlines():
            parts = line.split()
            if len(parts) == 3 and parts[0] == "unreachable" and parts[1] == "commit":
                if message_substring in self.subject_of(parts[2]):
                    return True
        return False
