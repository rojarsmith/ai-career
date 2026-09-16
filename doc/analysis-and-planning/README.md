# Design and Planning Documents

**This is the working original.** Edit directly here.

This directory is in `.gitignore` (line 12 of the file at the repo root), so it never reaches the public repo.
Per the **B3 ruling** in `17-decisions.md`: the repo is PUBLIC, and design documents do not go into git.

## The One Thing To Be Careful About

`.gitignore` stops `git add -A`; it **does not stop `git add -f`**.
Do not use `-f` on this directory. `15-target-tsmc.md` holds a submission playbook for a named employer.

The third line of defense is the content scan in `scripts/hooks/pre-commit` (tested: it does block national ID numbers,
API tokens and denylist words), but what it scans is content, not paths — do not rely on it to save you here.

## Where To Start Reading

`00-overview.md`. For the ruling record, see `17-decisions.md` (when it conflicts with any other document, it wins).
