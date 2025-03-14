# Git Lab Assignment: Library Catalogue Post-Mortem

**Course:** 26RA2308 Git for Software Development and Collaboration
**Builds on:** Experiments 1 to 5. **Based on:** Experiment 6 (Viewing Commit History and Undoing Changes)
**Time allowed:** 1 hour 30 minutes. **Marks:** 100

---

## The story

The team's small library catalogue tool (C, C++ and Python) shipped a release, and now the
report prints the wrong number of copies. Three teammates worked on it, the history is already
**published** on GitHub (`origin/main`), and you have to find out what went wrong and repair it
**without rewriting anything that was already published**.

You will use every command from Experiment 6: `git log` (with filters), `git show`, `git blame`,
`git restore`, `git reset` (all three modes), `git reflog`, `git revert` and `git stash`. Along the
way you will also reuse what you learnt earlier: `git config` and aliases (Experiment 3),
`git clone`, `.gitignore`, `git rm --cached` and `git check-ignore` (Experiment 4), and
`git add -p`, `git diff` and Conventional Commit messages (Experiment 5), plus the terminal
skills from Experiments 1 and 2 (`cat`, `echo >>`, `cp`, `ls -l`, pipes with `sort`, `uniq`, `wc`).

## What you need

`git`, `make`, `gcc`, `g++` and `python3` (the lab machines have them all). Check with
`git --version && make --version && gcc --version && g++ --version && python3 --version`.

## Rules

1. Work **only inside your own clone**. Do not push anything (`git push` is not part of this lab).
2. Never rewrite the published commits. The only history-changing commands allowed are the
   `git reset` steps that Task 4 tells you to run on your *own* scratch commits.
3. Type the commands yourself. The grader checks that your pasted output matches what is really
   in your repository, so output copied from a classmate is detected.
4. Keep the commit messages exactly as written where the task gives one.

## How you hand in your work

1. In Task 1 you copy `submission/outputs.template.txt` to `submission/outputs.txt`.
2. After **each step** (they are numbered **1.1**, **1.2**, ...), paste what the terminal printed
   under the matching `--- N.M` line of `submission/outputs.txt`, replacing `(paste output here)`.
   Do not edit or delete the `=== TASK` and `--- N.M` lines.
3. Fill in your name and registration number at the top of the file.
4. Run the automatic grader whenever you want to see where you stand:

   ```bash
   bash tests/run_tests.sh
   ```

   It prints **PASS** or **FAIL** for every task, tells you exactly which check failed, and
   shows your score out of 100. You can fix a mistake and run it again as often as you like.
5. When you are done, show the final grader output to your instructor (it is also saved in
   `submission/results.txt`), and submit `submission/outputs.txt` as instructed.

## Time plan

| Task | Topic | Suggested time | Marks |
|---|---|---|---|
| 1 | Clone, identity, alias | 5 min | 5 |
| 2 | Reading the history | 15 min | 20 |
| 3 | `restore` and `add -p` | 8 min | 10 |
| 4 | `reset` (soft, mixed, hard) and `reflog` | 17 min | 20 |
| 5 | `revert` the published bug | 12 min | 20 |
| 6 | `stash` | 8 min | 10 |
| 7 | Untrack files that should never be committed | 7 min | 10 |
| 8 | Incident report | 3 min | 5 |
| | Buffer for running the grader and fixing mistakes | 15 min | |

---

## Task 1: Setup (5 marks)

Clone the repository (your instructor gives you the URL), enter it, create your submission file
and configure your identity **for this repository only**:

```bash
git clone <REPO-URL> library-catalogue-lab
cd library-catalogue-lab
cp submission/outputs.template.txt submission/outputs.txt
git config user.name "Your Full Name"
git config user.email "your.email@example.com"
git config alias.lg "log --oneline --graph --decorate"
```

Use your own real name and e-mail (not the placeholders above, and not one of the teammates').
Do **not** use `--global` here.

* **1.1** Run `git config --local --list` and paste the output.
* **1.2** Run `git remote -v` and paste the output.
* **1.3** Run `git lg -3` (your new alias) and paste the output.

## Task 2: Reading the history (20 marks)

Investigate the published history with the Experiment 6 `log` options. Paste the output of each
command under its step.

* **2.1** `git log --oneline --graph --decorate --all`
* **2.2** `git log --stat -2`
* **2.3** `git log --oneline --author="Ben"`
* **2.4** `git log --oneline --since="2025-03-07 00:00 +0000" --until="2025-03-10 00:00 +0000"`
* **2.5** `git log --oneline -- tools/report.py`
* **2.6** `git log --oneline --follow -- src/catalog.c`

  Compare 2.6 with the same command without `--follow`. Why are there more commits with it?

Two commits in 2.5 touched `tools/report.py`. **One of them introduced the bug** (in Task 5 you
will see the report print the wrong total). Inspect both with `git show` and decide which one it is.

* **2.7** Run `git show <SHA of the commit that broke total_copies>` and paste the output.
* **2.8** Run `git blame tools/report.py` and paste the output. Find the lines of the loop inside
  `total_copies` and see which commit and author they belong to.
* **2.9** Answer the four questions at the end of the Task 2 block of your file (type each answer
  after the colon):

  | Answer | Question | Hint |
  |---|---|---|
  | `ANSWER-1` | SHA of the commit that broke `total_copies()` (at least 7 characters) | step 2.7 |
  | `ANSWER-2` | How many commits are in the history of `src/catalog.c`, counting those from before it was renamed? | `git log --oneline --follow -- src/catalog.c \| wc -l` |
  | `ANSWER-3` | Full name of the author with the most commits | `git log --format=%an \| sort \| uniq -c \| sort -rn` |
  | `ANSWER-4` | SHA of the commit that added `config.txt` | `git log --oneline -- config.txt` |

## Task 3: Undoing edits with `restore` (10 marks)

Make three careless edits in one go:

```bash
echo "debug: temporary line" >> NOTES.txt
echo "# TODO: tidy later" >> tools/helpers.py
{ echo '<!-- draft -->'; cat README.md; } > README.tmp && mv README.tmp README.md
echo "Draft footer" >> README.md
```

* **3.1** `git status`. All three files should be modified but nothing staged.

> Type the `<!-- draft -->` line with **single quotes**, exactly as shown. In a terminal, bash and zsh treat
> `!` inside double quotes as a history shortcut and fail with `event not found`.

Now stage `tools/helpers.py` completely, but only **part** of `README.md`:

```bash
git add tools/helpers.py
git add -p README.md
```

At the first prompt (the `<!-- draft -->` line at the top) answer `y`; at the second prompt (the
`Draft footer` line at the bottom) answer `n`.

* **3.2** `git status`. Notice that `README.md` appears in *both* lists.
* **3.3** `git diff --staged --stat`

Now take everything back:

```bash
git restore --staged tools/helpers.py README.md
```

* **3.4** `git status`. Nothing should be staged, but the edits are still in the files.

```bash
git restore .
```

* **3.5** `git status`. The working tree should be clean again.

> `git restore` on a modified file cannot be undone. The edits are gone for good.

## Task 4: `reset` and `reflog` (20 marks)

Create three small scratch commits (use exactly these messages):

```bash
echo "scratch 1" >> NOTES.txt && git add NOTES.txt && git commit -m "chore: scratch 1"
echo "scratch 2" >> NOTES.txt && git add NOTES.txt && git commit -m "chore: scratch 2"
echo "scratch 3" >> NOTES.txt && git add NOTES.txt && git commit -m "chore: scratch 3"
```

* **4.1** `git log --oneline -4`

**Soft.** Undo the last commit but keep its change **staged**:

```bash
git reset --soft HEAD~1
```

* **4.2** `git status`, then `git log --oneline -3` (paste both outputs).

Commit it again with a new message, then do the **mixed** reset, which keeps the change in the
working directory but **unstaged**:

```bash
git commit -m "chore: scratch 3 again"
git reset --mixed HEAD~1
```

* **4.3** `git status`, then `git log --oneline -3` (paste both outputs).

**Hard.** Throw the commit **and** the change away:

```bash
git reset --hard HEAD~1
```

* **4.4** `git status`, then `git log --oneline -3`, then `tail -n 3 NOTES.txt` (paste all three).

Oh no, you wanted "scratch 3 again" back! The reflog remembers where `HEAD` has been:

* **4.5** `git reflog -8`. Find the line `commit: chore: scratch 3 again` and note its SHA.

```bash
git reset --hard <SHA of "chore: scratch 3 again">
```

* **4.6** `git log --oneline -4`, then `tail -n 3 NOTES.txt` (paste both). Scratch 3 is back.

Finally, return to the published state. Your scratch commits were never published, so resetting
them away is fine:

```bash
git reset --hard origin/main
```

* **4.7** `git status`. It should say the branch is up to date with `origin/main`.

## Task 5: Undo a published commit with `revert` (20 marks)

* **5.1** Run `make test` and paste the output. It is **supposed to fail**: the Python tests catch
  the bug (you should see `30 != 34`) and `make` stops there.

The buggy commit from `ANSWER-1` is already published, so you must **not** reset it away.
Undo it with a new commit that reverses it:

```bash
git revert --no-edit <SHA from ANSWER-1>
```

(`--no-edit` keeps Git's default message so that no editor opens.)

* **5.2** Paste the output of the `git revert` command, then run `git log --oneline -3` and paste
  that too.
* **5.3** Run `make test` again and paste the output. It must end with `ALL TESTS PASSED`.
* **5.4** `git status`. It should say your branch is **ahead of `origin/main` by 1 commit**.
  Do not push.

## Task 6: Shelving work with `stash` (10 marks)

You start a new feature, then an urgent fix lands on your desk.

```bash
echo "# WIP: add sort by year" >> tools/report.py
```

* **6.1** `git status`

Shelve the unfinished work:

```bash
git stash push -m "wip: sort by year"
```

* **6.2** Paste the output of `git stash push ...`, then `git status`, then `git stash list`.

Make the urgent fix on the clean tree (add a line to the changelog and commit it with your own
Conventional Commit message):

```bash
echo "- Fix: report totals are correct again" >> CHANGELOG.md
git add CHANGELOG.md
git commit -m "docs: note the report fix in the changelog"
```

* **6.3** `git log --oneline -2`

Bring the unfinished work back:

```bash
git stash pop
```

* **6.4** Paste the output of `git stash pop`, then `git status`, then `git stash list | wc -l`
  (this counts the stashes left; it should print `0`).

Now discard the experiment:

```bash
git restore tools/report.py
```

* **6.5** `git status`. The tree should be clean.

## Task 7: Untrack files that should never be committed (10 marks)

Teammate Chitra committed some build output and a local configuration file with a password in it.
Experiment 4 taught you the cure: stop tracking them, ignore them, keep them on disk.

* **7.1** `git ls-files`. Spot the four files that do not belong: `a.out`, `catalog.o`,
  `search.o` and `config.txt`.

```bash
git rm --cached a.out catalog.o search.o config.txt
```

* **7.2** Paste the output of the `git rm --cached` command.

Now add ignore rules so they cannot be added again by accident, and stage the change:

```bash
printf 'a.out\n*.o\nconfig.txt\n' >> .gitignore
git add .gitignore
```

* **7.3** `git status`. The four files should be staged as *deleted*, `.gitignore` as *modified*,
  and none of them should appear as untracked.

```bash
git commit -m "chore: stop tracking build output and local config"
```

* **7.4** `git log --oneline -1`
* **7.5** `git check-ignore -v a.out catalog.o search.o config.txt`
* **7.6** `ls -l a.out catalog.o search.o config.txt`. The files must still exist on disk.
* **7.7** `git log --oneline -- config.txt`. The commit that added the password is **still in the
  history**. Untracking a file does not remove it from old commits, which is why a leaked password
  must always be changed, not just deleted.

## Task 8: Incident report (5 marks)

Write a short report and commit it. Replace the text in angle brackets with your own words:

```bash
cat > INCIDENT_REPORT.md << 'EOF'
# Incident report

Culprit commit: <the SHA from ANSWER-1>

Cause: <one sentence: what was wrong in the code>

Fix: <one sentence: how you undid it, mention the word revert>
EOF
git add INCIDENT_REPORT.md
git commit -m "docs: add incident report"
```

* **8.1** `git log --oneline --graph --decorate -12`

## Finish

```bash
bash tests/run_tests.sh
```

You want to see `PASS` for all eight tasks and `TOTAL: 100/100`. Anything marked `FAIL` is listed
with the reason; fix it and run the grader again.

## Marks

| Task | Marks | How it is checked |
|---|---|---|
| 1 | 5 | your pasted config matches the repository's real local configuration |
| 2 | 20 | the pasted `log`, `show` and `blame` output is correct; four answers |
| 3 | 10 | pasted `status` output shows each stage of staging and restoring |
| 4 | 20 | pasted output shows the effect of each reset mode; the repository's reflog proves you really ran them |
| 5 | 20 | a real `Revert` commit exists, the published history is intact, and the tests pass |
| 6 | 10 | a real stash was made and popped, and the urgent fix was committed |
| 7 | 10 | the four files are untracked, ignored and still on disk |
| 8 | 5 | the report is committed and names the culprit |

A task shows **PASS** only when every check in it passes, and you earn marks for each check that
passes even if the task as a whole fails.

## If something goes wrong

* **Nothing printed / wrong branch.** Run `git status` and `git log --oneline -5` and read them.
* **An editor opened** (usually vim) during a command: type `:q!` and Enter, then repeat the
  command with the `--no-edit` or `-m` option.
* **`git add -p` shows only one hunk.** Make sure you ran all four lines of the Task 3 setup; the
  first edit goes at the top of `README.md` and the second at the bottom.
* **You made a mistake early on.** `git reflog` shows everything `HEAD` did. You can return to any
  line of it with `git reset --hard <sha>`. If the repository is beyond repair, delete the folder,
  clone again and redo the tasks (your pasted outputs must be produced in the new clone).
* **`make: command not found` / `gcc: command not found`.** Use a lab machine, or install
  `build-essential` (Ubuntu) or the Xcode command line tools (macOS).
