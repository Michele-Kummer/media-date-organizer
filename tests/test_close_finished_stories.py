"""scripts/close_finished_stories.py closes the user stories whose Status line was waiting only
on issues that are now closed as completed, marks them Done, checks their epic, previews
unless --apply, and leaves every other story alone. Nothing here contacts GitHub.
Run with: py -m unittest discover tests -v"""

import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import close_finished_stories as cs  # noqa: E402

REPO = 'Owner/project'


def body(status):
    return ('**Epic:** Workflow (#2)\n\nAs a media owner, I want a thing.\n\n- It works.\n\n'
            f'{status}\n\n---\n<sub>Imported.</sub>')


class FakeGitHub:
    """Answers gh calls from a list of open stories, a table of issue states, and a table of
    parents (issue number -> epic dict, as in test_close_finished_epics)."""

    def __init__(self, stories, states, parents=None):
        self.stories = stories
        self.states = states
        self.parents = parents or {}
        self.closed = []
        self.edited = {}
        self.calls = []

    def __call__(self, args):
        self.calls.append(args)
        if args[:2] == ['issue', 'list']:
            return json.dumps([s for s in self.stories if s['number'] not in self.closed])
        if args[:2] == ['issue', 'view']:
            state, reason = self.states[int(args[2])]
            return json.dumps({'state': state, 'stateReason': reason})
        if args[:2] == ['issue', 'edit']:
            self.edited[int(args[2])] = args[args.index('--body') + 1]
            return ''
        if args[:2] == ['issue', 'close']:
            self.closed.append(int(args[2]))
            return ''
        if args[:2] == ['api', 'graphql']:
            number = int(next(a for a in args if a.startswith('number=')).split('=', 1)[1])
            parent = self.parents.get(number)
            if parent is not None:
                parent = dict(parent)
                parent['subIssuesSummary'] = {'total': parent.pop('total'), 'completed': parent.pop('completed')}
            return json.dumps({'data': {'repository': {'issue': {'parent': parent}}}})
        raise AssertionError(f'unexpected gh call {args}')


def story(number, status):
    return {'number': number, 'title': f'Story {number}', 'body': body(status)}


DONE = ('CLOSED', 'COMPLETED')
OPEN = ('OPEN', None)
NOT_PLANNED = ('CLOSED', 'NOT_PLANNED')
WAITING_ON_57 = '**Status:** Partly done. One unreadable file stops the whole step (BUG-02 (#57)).'


class StatusLineTests(unittest.TestCase):

    def test_reads_the_issues_a_story_waits_on(self):
        self.assertEqual(cs.waiting_on(body(WAITING_ON_57)), [57])

    def test_reads_several_issues_once_each(self):
        status = '**Status:** Partly done. Slow (BUG-04 (#59)) and wrong (#103), see #59.'
        self.assertEqual(cs.waiting_on(body(status)), [59, 103])

    def test_a_done_story_waits_on_nothing(self):
        self.assertEqual(cs.waiting_on(body('**Status:** Done')), [])

    def test_a_story_without_a_status_line_waits_on_nothing(self):
        self.assertEqual(cs.waiting_on('As a media owner, I want #57 fixed.'), [])

    def test_issues_outside_the_status_line_are_ignored(self):
        text = body('**Status:** Partly done. Slow (#59).').replace('- It works.', '- Dates before 1970 (#104).')
        self.assertEqual(cs.waiting_on(text), [59])

    def test_mark_done_changes_only_the_status_line(self):
        before = body(WAITING_ON_57)
        after = cs.mark_done(before)
        self.assertEqual(after, before.replace(WAITING_ON_57, '**Status:** Done'))


class CloseFinishedStoriesTests(unittest.TestCase):

    def run_it(self, stories, states, issue=57, apply=True, parents=None):
        gh = FakeGitHub(stories, states, parents)
        lines = []
        result = cs.close_finished_stories(REPO, issue, apply=apply, gh=gh, out=lines.append)
        return result, gh, lines

    def test_closes_every_story_waiting_only_on_the_closed_issue(self):
        stories = [story(15, WAITING_ON_57), story(26, WAITING_ON_57)]
        result, gh, lines = self.run_it(stories, {57: DONE})
        self.assertEqual(result, [15, 26])
        self.assertEqual(gh.closed, [15, 26])
        self.assertIn('CLOSED #15 Story 15: #57 closed, status set to Done.', lines)

    def test_the_closed_story_is_marked_done(self):
        _, gh, _ = self.run_it([story(15, WAITING_ON_57)], {57: DONE})
        self.assertIn('**Status:** Done\n', gh.edited[15])
        self.assertNotIn('Partly done', gh.edited[15])

    def test_the_story_is_edited_before_it_is_closed(self):
        _, gh, _ = self.run_it([story(15, WAITING_ON_57)], {57: DONE})
        kinds = [c[:2] for c in gh.calls if c[:2] in (['issue', 'edit'], ['issue', 'close'])]
        self.assertEqual(kinds, [['issue', 'edit'], ['issue', 'close']])

    def test_comment_and_reason(self):
        _, gh, _ = self.run_it([story(15, WAITING_ON_57)], {57: DONE})
        close = next(c for c in gh.calls if c[:2] == ['issue', 'close'])
        self.assertEqual(close[close.index('--reason') + 1], 'completed')
        self.assertEqual(close[close.index('--repo') + 1], REPO)
        comment = close[close.index('--comment') + 1]
        self.assertIn('(#57)', comment)
        self.assertIn('status is now Done', comment)

    def test_preview_changes_nothing(self):
        result, gh, lines = self.run_it([story(15, WAITING_ON_57)], {57: DONE}, apply=False)
        self.assertEqual(result, [15])
        self.assertEqual((gh.closed, gh.edited), ([], {}))
        self.assertTrue(lines[0].startswith('WOULD CLOSE #15'))

    def test_a_story_still_waiting_on_another_issue_stays_open(self):
        status = '**Status:** Partly done. Unreadable files (#57) and slow folders (#103).'
        result, gh, lines = self.run_it([story(15, status)], {57: DONE, 103: OPEN})
        self.assertEqual((result, gh.closed, gh.edited), ([], [], {}))
        self.assertEqual(lines, ['#15 Story 15 stays open: still waiting on #103.'])

    def test_a_story_closes_once_its_last_issue_closes(self):
        status = '**Status:** Partly done. Unreadable files (#57) and slow folders (#103).'
        result, gh, _ = self.run_it([story(15, status)], {57: DONE, 103: DONE}, issue=103)
        self.assertEqual(result, [15])
        self.assertIn('(#57, #103)', next(c for c in gh.calls if c[:2] == ['issue', 'close'])[-1])

    def test_an_issue_closed_as_not_planned_does_not_finish_a_story(self):
        result, gh, lines = self.run_it([story(15, WAITING_ON_57)], {57: NOT_PLANNED})
        self.assertEqual((result, gh.closed), ([], []))
        self.assertIn('closed without being completed', lines[0])

    def test_stories_not_waiting_on_the_issue_are_left_alone(self):
        stories = [story(15, '**Status:** Partly done. Slow (#103).'), story(20, '**Status:** Done')]
        result, gh, lines = self.run_it(stories, {57: DONE, 103: OPEN})
        self.assertEqual((result, gh.closed), ([], []))
        self.assertEqual(lines, ['No open story is waiting on #57. Nothing to do.'])
        self.assertFalse(any(c[:2] == ['issue', 'view'] for c in gh.calls))

    def test_does_not_match_a_longer_number(self):
        result, gh, _ = self.run_it([story(15, '**Status:** Partly done. Slow (#570).')], {57: DONE})
        self.assertEqual((result, gh.closed), ([], []))

    def test_the_story_list_asks_for_open_user_stories(self):
        _, gh, _ = self.run_it([], {})
        listing = next(c for c in gh.calls if c[:2] == ['issue', 'list'])
        self.assertEqual(listing[listing.index('--state') + 1], 'open')
        self.assertEqual(listing[listing.index('--label') + 1], 'user story')

    def test_closes_the_epic_when_the_story_was_its_last_open_child(self):
        parents = {15: {'number': 2, 'title': 'Epic: 2', 'state': 'OPEN', 'total': 3, 'completed': 3}}
        _, gh, lines = self.run_it([story(15, WAITING_ON_57)], {57: DONE}, parents=parents)
        self.assertEqual(gh.closed, [15, 2])
        self.assertIn('CLOSED #2 Epic: 2: all 3 closed.', lines)

    def test_leaves_the_epic_open_while_it_has_other_open_children(self):
        parents = {15: {'number': 2, 'title': 'Epic: 2', 'state': 'OPEN', 'total': 30, 'completed': 20}}
        _, gh, lines = self.run_it([story(15, WAITING_ON_57)], {57: DONE}, parents=parents)
        self.assertEqual(gh.closed, [15])
        self.assertIn('#2 Epic: 2 stays open: 20 of 30 closed.', lines)

    def test_workflow_runs_the_script_when_an_issue_closes(self):
        text = (ROOT / '.github' / 'workflows' / 'close-epics.yml').read_text(encoding='utf-8')
        self.assertIn('types: [closed]', text)
        self.assertIn('scripts/close_finished_stories.py', text)
        self.assertEqual(text.count('$APPLY'), 2)


if __name__ == '__main__':
    unittest.main()
