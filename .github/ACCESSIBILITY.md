# Accessibility statement

media-date-organizer should be usable by everyone who has photos and videos to organise, including people who use a screen reader, a keyboard only, or high-contrast or magnified displays. This statement says how accessible it is today, where it falls short, and how to report a problem.

It covers the command-line tool, the Claude Code plugin, the audit workbook and this repository's documentation. It was written on 2026-11-22.

## How accessible it is

**The command-line tool and the plugin**

- Everything is done by typing. Nothing needs a mouse.
- All output is plain text, so a screen reader can read it in the terminal.
- Every line that reports on a file starts with a word that says what happened, such as `WOULD MOVE`, `FAILED` or `KEPT`, followed by the file. The cleanup script also colours some lines, but the words carry the meaning, so nothing depends on colour alone.
- A preview ends with a line saying nothing was changed and how to make the changes.
- With the plugin, you can ask for each step in plain English, and Claude explains each preview before anything changes.

**The documentation**

- The README and the documents use headings in order, lists and tables, so they can be navigated by heading with a screen reader.
- Every screenshot has alt text that describes what it shows, and the text around it explains the before and after.

## Known limits

- The tool has not been tested with a screen reader or other assistive technology, and has not been audited against a standard.
- The screenshots show Windows Explorer and are not a substitute for the text. Their detail, such as each file's date, is only described in summary.
- The audit workbook is an ordinary Excel file. Its accessibility has not been checked.
- Long runs produce a lot of output. To review it, send it to a file, for example `... > run.txt`, and read the summary at the end first.

## The planned desktop app

The desktop app in the Desktop app epic is planned to meet WCAG 2.2 Level A, so it can be used with a keyboard and a screen reader. The requirements are in [issue #81](https://github.com/Michele-Kummer/media-date-organizer/issues/81).

## Report a problem

If something is hard or impossible to use with the way you work, please open an issue with the **[Bug form](https://github.com/Michele-Kummer/media-date-organizer/issues/new/choose)**. Say "accessibility" under **Affects**, and describe what you were trying to do, what assistive technology you use, if any, and what happened. Issues about accessibility get the `accessibility` label.
