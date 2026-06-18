# Aegis-Red Mistakes Log

## 2026-06-18
- **Context**: Drafting files and commits for features.
- **Missed Context**: Ran `git add` and `git commit` directly when the user only asked to "draft" the commits and the files group.
- **Correction**: Reset the commit using `git reset HEAD~1` to restore the original modified/unstaged files, and wrote the drafted file groupings and messages for user review.
