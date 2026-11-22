# Security policy

## Supported versions

Only the latest version on `main` is supported. It is the one `/plugin marketplace update michele-kummer` installs. Fixes are not made to older versions.

## What counts as a security problem

media-date-organizer runs on your own computer and works only on the folder you point it at. It makes no network connections. It runs ExifTool and ffmpeg, if they are installed, to read and write dates.

Please report anything that could:

- delete, overwrite or change a file outside the folder you gave it, or change any file during a preview (without `--apply`);
- lose a photo or video, rather than moving it aside into a `_` folder;
- run a command or code taken from a file's name, its metadata or its contents;
- send a file, or anything about your files, anywhere.

A wrong date, a slow step or a step that stops with an error is a bug rather than a security problem. Please report those with the [Bug form](https://github.com/Michele-Kummer/media-date-organizer/issues/new/choose).

## How to report one

Report it privately, so it can be fixed before anyone else learns of it:

1. Go to the repository's **Security** tab and choose **[Report a vulnerability](https://github.com/Michele-Kummer/media-date-organizer/security/advisories/new)**.
2. Say what happens, the steps to reproduce it, and your version of Windows, Python and the plugin.

Please don't open a public issue, pull request or discussion about it.

## What happens next

- The report is read and answered as soon as possible.
- Once the problem is confirmed, it is fixed on `main` and a security advisory is published with the fix.
- You are credited in the advisory, unless you would rather not be.
