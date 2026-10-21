"""The slash commands preview by default and change files only when --apply
is typed after them (US-26), and no doc still tells anyone to use the
retired --dry-run or -WhatIf (US-27). Run with: py -m unittest discover tests -v"""

import pathlib
import re
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
COMMANDS = REPO / 'commands'

# organize.py flags whose phase changes files
CHANGING_FLAGS = ('--all', '--fill-blanks', '--convert-png', '--apply-moves', '--sync-timestamps',
                  '--flatten', '--final-check', '--quarantine-ads', '--move-incomplete', '--delete-junk')

# Docs that tell users and Claude what to run. docs/case-study.md and
# docs/user-stories-and-bugs.md record history and are left out.
CURRENT_DOCS = [REPO / 'README.md', REPO / 'docs' / 'project-cheatsheet.md',
                *sorted(REPO.glob('skills/*/SKILL.md')), *sorted(COMMANDS.glob('*.md'))]


def front_matter(text):
    m = re.match(r'---\n(.*?)\n---\n', text, re.S)
    return dict(line.split(': ', 1) for line in m[1].splitlines()) if m else {}


def script_steps(text):
    """The script command lines in text, leaving out the "With --apply"
    bullet, which is where the applied form is meant to appear."""
    text = re.sub(r'^- \*\*With `--apply`\*\*.*$', '', text, flags=re.M)
    return re.findall(r'`([^`]*(?:organize\.py --root|\.ps1 -Path)[^`]*)`', text)


def changes_files(text):
    """True when the command runs a script step that changes files."""
    return any('.ps1' in step or any(re.search(rf'{re.escape(f)}(?![\w-])', step) for f in CHANGING_FLAGS)
               for step in script_steps(text))


class SlashCommandTests(unittest.TestCase):

    def test_commands_that_change_files_preview_unless_apply(self):
        changing = []
        for path in sorted(COMMANDS.glob('*.md')):
            text = path.read_text(encoding='utf-8')
            if not changes_files(text):
                continue
            changing.append(path.stem)
            with self.subTest(command=path.stem):
                meta = front_matter(text)
                self.assertIn('[--apply]', meta.get('argument-hint', ''),
                              'the argument hint must show --apply as optional')
                self.assertIn('dry run', text.lower())
                self.assertIn(f'/{path.stem} <folder> --apply', text,
                              'a dry run must end by telling the user what to type to apply')
                # Each script line is written without --apply, so as written it previews
                for line in script_steps(text):
                    self.assertNotRegex(line, r'(?i)(^|\s)-{1,2}apply(?![\w-])',
                                        f'step runs for real as written: {line}')
        self.assertIn('fix-media-dates', changing)
        self.assertIn('flatten-media', changing)

    def test_fix_media_dates_has_all_and_all_apply(self):
        text = (COMMANDS / 'fix-media-dates.md').read_text(encoding='utf-8')
        self.assertIn('[--all', front_matter(text)['argument-hint'])
        # --all previews and points the user at --all --apply
        self.assertIn('/fix-media-dates <folder> --all --apply', text)
        all_section = text.split('## All in one go', 1)[1].split('\n## ', 1)[0]
        # The same as organize.py --all: one command, with ads and flatten
        # only when opted in
        steps = script_steps(all_section)
        self.assertEqual(len(steps), 1, steps)
        self.assertRegex(steps[0], r'organize\.py --root "<folder>" --all$')
        self.assertIn('--quarantine-ads', all_section)
        self.assertIn('--flatten', all_section)
        self.assertIn('**`--all --apply`**', all_section)

    def test_report_commands_need_no_apply(self):
        text = (COMMANDS / 'report-opposite-type.md').read_text(encoding='utf-8')
        self.assertFalse(changes_files(text))
        self.assertNotIn('[--apply]', front_matter(text).get('argument-hint', ''))

    def test_help_shows_both_forms(self):
        text = (COMMANDS / 'media-help.md').read_text(encoding='utf-8')
        for cmd in ('/fix-media-dates', '/flatten-media'):
            self.assertRegex(text, re.escape(cmd) + r' D:\\Pictures\\2026`')
            self.assertRegex(text, re.escape(cmd) + r' D:\\Pictures\\2026 --apply`')
        self.assertIn('`/fix-media-dates D:\\Pictures\\2026 --all`', text)
        self.assertIn('`/fix-media-dates D:\\Pictures\\2026 --all --apply`', text)

    def test_no_doc_mentions_the_old_preview_flags(self):
        for path in CURRENT_DOCS:
            with self.subTest(doc=str(path.relative_to(REPO))):
                text = path.read_text(encoding='utf-8')
                self.assertNotIn('--dry-run', text, 'previewing is the default; say --apply instead')
                self.assertNotIn('-WhatIf', text, 'previewing is the default; say -Apply instead')


if __name__ == '__main__':
    unittest.main()
