"""Close the user stories that were waiting only on an issue that has just been closed.

A story that is not finished says why in its Status line, naming the issues it waits on:

    **Status:** Partly done. One unreadable file stops the whole step (BUG-02 (#57)).

GitHub's Actions workflow .github/workflows/close-epics.yml runs this each time an issue is
closed. It finds the open user stories whose Status line names that issue. When every issue
named there is closed as completed, it changes the line to **Status:** Done, closes the story
as completed with a comment saying which issue finished it, and then closes the story's epic
if that was its last open story or bug (see close_finished_epics.py). An issue closed as not
planned or as a duplicate does not count, so its story stays open for someone to look at.

It uses the GitHub CLI (gh), signed in, or given a token in GH_TOKEN.

Previews by default. Nothing is changed unless --apply is given.

    py scripts/close_finished_stories.py --issue 57              preview
    py scripts/close_finished_stories.py --issue 57 --apply      close the stories that are done
"""

import argparse
import json
import re
import sys

from close_finished_epics import DEFAULT_REPO, close_finished_epics, run_gh

STORY_LABEL = 'user story'
STATUS_RE = re.compile(r'^\*\*Status:\*\*[^\n]*$', re.MULTILINE)
ISSUE_RE = re.compile(r'#(\d+)\b')
DONE_LINE = '**Status:** Done'
COMMENT = ('Every issue this story was waiting on is closed ({issues}), the last being #{closed}, '
           'so its status is now Done and it is closed too.')


def status_line(body):
    """The story's Status line, or None when it has none."""
    match = STATUS_RE.search(body or '')
    return match.group(0) if match else None


def waiting_on(body):
    """The issue numbers named in a Status line that is not Done, in order, without repeats.
    Empty when the story is Done or has no Status line."""
    line = status_line(body)
    if line is None or line.startswith(DONE_LINE):
        return []
    numbers = []
    for n in ISSUE_RE.findall(line):
        if int(n) not in numbers:
            numbers.append(int(n))
    return numbers


def mark_done(body):
    """The body with its Status line changed to Done."""
    return STATUS_RE.sub(DONE_LINE, body, count=1)


def open_stories(repo, gh=run_gh):
    """Every open user story, as dicts with number, title, and body."""
    out = gh(['issue', 'list', '--repo', repo, '--state', 'open', '--label', STORY_LABEL,
              '--limit', '1000', '--json', 'number,title,body'])
    return json.loads(out or '[]')


def issue_state(repo, number, gh=run_gh):
    """(state, stateReason) of an issue, such as ('CLOSED', 'COMPLETED')."""
    out = gh(['issue', 'view', str(number), '--repo', repo, '--json', 'state,stateReason'])
    data = json.loads(out)
    return data.get('state'), data.get('stateReason')


def close_finished_stories(repo, number, apply=False, gh=run_gh, out=print):
    """Close each open story whose Status line names issue NUMBER and whose named issues are
    all closed as completed. Returns the numbers of the stories closed (or that would be
    closed, in a preview)."""
    closed = []
    states = {}
    waiting = [s for s in open_stories(repo, gh) if number in waiting_on(s['body'])]
    if not waiting:
        out(f'No open story is waiting on #{number}. Nothing to do.')
    for story in waiting:
        label = f"#{story['number']} {story['title']}"
        issues = waiting_on(story['body'])
        for n in issues:
            if n not in states:
                states[n] = issue_state(repo, n, gh)
        still_open = [n for n in issues if states[n][0] != 'CLOSED']
        not_completed = [n for n in issues if states[n][0] == 'CLOSED' and states[n][1] != 'COMPLETED']
        if still_open:
            out(f"{label} stays open: still waiting on {', '.join(f'#{n}' for n in still_open)}.")
            continue
        if not_completed:
            out(f"{label} stays open: {', '.join(f'#{n}' for n in not_completed)} was closed "
                'without being completed, so check the story by hand.')
            continue
        named = ', '.join(f'#{n}' for n in issues)
        if apply:
            gh(['issue', 'edit', str(story['number']), '--repo', repo, '--body', mark_done(story['body'])])
            gh(['issue', 'close', str(story['number']), '--repo', repo, '--reason', 'completed',
                '--comment', COMMENT.format(issues=named, closed=number)])
            out(f'CLOSED {label}: {named} closed, status set to Done.')
            # An issue closed by the workflow's own token starts no new workflow run, so the
            # story's epic is checked here
            close_finished_epics(repo, story['number'], apply=True, gh=gh, out=out)
        else:
            out(f'WOULD CLOSE {label}: {named} closed, status would be set to Done.')
        closed.append(story['number'])
    return closed


def main(argv=None):
    ap = argparse.ArgumentParser(description='Close the user stories that were waiting only on an issue that has just been closed.')
    ap.add_argument('--issue', type=int, required=True, help='The issue that was just closed.')
    ap.add_argument('--repo', default=DEFAULT_REPO, help=f'OWNER/NAME (default {DEFAULT_REPO}).')
    ap.add_argument('--apply', action='store_true', help='Close the stories. Without it, only preview.')
    args = ap.parse_args(argv)
    try:
        close_finished_stories(args.repo, args.issue, apply=args.apply)
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
