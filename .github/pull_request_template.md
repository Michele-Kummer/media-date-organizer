Fixes #

<!-- Use "Fixes #N" for a bug, "Closes #N" for a user story, or "Part of #N" when the story needs more pull requests after this one. -->

## What and why

<!-- What was wrong or missing, and why this change is the answer. -->

## Changes

<!-- One bullet per file or area changed. -->
-

## Tests

<!-- What you ran and what it showed. -->
- [ ] `py -m unittest discover tests -v` passes
- [ ] New or changed code has tests on generated files (never real photos)

## Checklist

- [ ] A phase that changes files only previews unless `--apply` is given, and is listed in `CHANGING` and `CHANGING_FLAGS`
- [ ] Nothing is deleted; files are moved to a holding folder
- [ ] The docs are updated (`organize.py` docstring and `--help`, README, cheat sheet, `SKILL.md`, slash commands)
- [ ] Proper casing and no double spaces or stray dashes in names and output text
