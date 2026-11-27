# Contributing

Thank you for helping with media-date-organizer. This guide explains how to report a problem, how the work is organised, and how to make a change.

Everyone taking part is expected to follow the [code of conduct](CODE_OF_CONDUCT.md).

## Report a bug or ask for a feature

Use **[New issue](https://github.com/Michele-Kummer/media-date-organizer/issues/new/choose)** and pick a form:

- **Bug:** something gives a wrong result, stops, or loses a file. Give the steps to reproduce it, what you expected and what happened.
- **User story:** something the tool should do. Write it as "As a media owner, I want …, so that …", with the acceptance criteria that would show it is done.

For a security problem, don't open an issue. Follow the [security policy](SECURITY.md) instead.

## How the work is organised

All work is tracked in [GitHub Issues](https://github.com/Michele-Kummer/media-date-organizer/issues) and on the [project board](https://github.com/users/Michele-Kummer/projects/1).

- **Epics** group the work by area of the tool. Every user story and bug is a sub-issue of its epic, and each bug names the user story it affects. When the last of them is closed, a GitHub workflow closes the epic. A story that is partly done names the issues it waits on in its **Status:** line, such as `**Status:** Partly done. One unreadable file stops the whole step (#57).` When every issue named there is closed as completed, the same workflow sets the line to `**Status:** Done` and closes the story. An issue closed as not planned leaves the story open for someone to check.
- **Titles** start with the area, such as `Dates:`, `Flatten:` or `Thumbnails:`.
- **Types:** stories have the **Feature** type and bugs the **Bug** type.
- **Labels** give the priority (`P1: Critical` to `P4: Low`), a bug's severity (`S1: Blocker` to `S4: Trivial`) and who found a bug (`Found by: …`). Epics have the `epic` label.
- **Status** (Todo, In Progress, Done) is kept on the project board. Closing an issue moves it to Done.
- The requirements were first gathered in [docs/user-stories-and-bugs.md](../docs/user-stories-and-bugs.md). It is kept as a record, and new work goes into issues.

## Set up

1. Install Python 3.9 or later on Windows, then the packages: `py -m pip install -r requirements.txt`.
2. Optional: [ExifTool](https://exiftool.org/) and ffmpeg on `PATH`. The video tests need ffmpeg, and the ones that write video dates also need ExifTool. They are skipped when these are missing.
3. To try the plugin without installing it, start Claude Code in the repository with `claude --plugin-dir .`.

## Run the tests

```
py -m unittest discover tests -v
```

The tests make their own photos and videos in temporary folders, so they never need real ones. Run them before every pull request. GitHub also runs them on Windows, with Python 3.9 and 3.12, for every push and pull request, and the badge at the top of the README shows the latest result.

## Rules for changes

These keep the tool safe to run on a real photo library:

- **Preview first.** Every step that changes files lists what it would do, and changes them only with `--apply`. `tests/test_dry_run.py` checks this for every step.
- **Never delete.** Move files aside into a holding folder such as `_junk` or `_converted` instead. Only a step whose purpose is deleting may delete, and it must say so.
- **Add tests** for new and changed code, on generated files.
- **Update the docs** that a change affects: the README, the [cheat sheet](../docs/project-cheatsheet.md), and the skills and commands Claude reads.
- **Write clearly:** proper casing in names, headings and output text, and no double spaces or stray dashes.

## Make a change

1. Pick an issue, or open one first, so the change is agreed before the work starts.
2. Create a branch from `main`.
3. Make the change, with its tests and docs, and run the tests.
4. Write commit messages as a short summary in the imperative ("Skip hidden folders when flattening"), with more detail below it if needed.
5. Open a pull request and fill in the template. Write `Fixes #<issue number>` for a bug or `Closes #<issue number>` for a user story, so merging it closes the issue and the project board moves it to Done. Use `Part of #<issue number>` when a story needs more pull requests after this one.
