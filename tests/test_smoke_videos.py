"""Smoke tests for how organize.py handles videos. Small test videos are
generated with ffmpeg, so these are skipped when ffmpeg is not available
(pip install imageio-ffmpeg); the date-writing test also needs exiftool.

Run from the repository root:
    py -m unittest discover tests -v
"""
import datetime
import pathlib
import shutil
import subprocess
import tempfile
import unittest

from test_smoke import names, organize, run

FFMPEG = organize._find_ffmpeg()
EXIFTOOL = organize._find_exiftool()

# Media Created of the dated test video, as stored (UTC) and as Explorer and
# organize.py show it (local time)
CREATED_UTC = datetime.datetime(2020, 2, 2, 18, 0, 0, tzinfo=datetime.timezone.utc)
CREATED_LOCAL = CREATED_UTC.astimezone().replace(tzinfo=None)
CREATED_DAY = CREATED_LOCAL.date().isoformat()


def make_video(path, pattern='testsrc', seconds=2, created=None):
    """Generate a small MP4 of an ffmpeg test pattern, with Media Created
    set if created (an aware datetime) is given, else blank."""
    cmd = [FFMPEG, '-hide_banner', '-loglevel', 'error', '-y',
           '-f', 'lavfi', '-i', f"{pattern}=duration={seconds}:size=160x120:rate=10",
           '-pix_fmt', 'yuv420p']
    if created is not None:
        cmd += ['-metadata', 'creation_time=' + created.strftime('%Y-%m-%dT%H:%M:%SZ')]
    subprocess.run(cmd + [str(path)], check=True, capture_output=True)


def media_created(path):
    return organize.read_metadata(str(path), organize.detect_type(str(path)))['date_taken']


@unittest.skipUnless(FFMPEG, 'ffmpeg is needed to generate test videos (pip install imageio-ffmpeg)')
class VideoSmokeTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Generated once, copied into each test's folder
        cls.samples = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-videos-'))
        cls.addClassCleanup(shutil.rmtree, cls.samples, ignore_errors=True)
        cls.dated = cls.samples / 'dated.mp4'
        cls.blank = cls.samples / 'blank.mp4'
        cls.other = cls.samples / 'other.mp4'
        cls.longer = cls.samples / 'longer.mp4'
        cls.retagged = cls.samples / 'retagged.mp4'
        make_video(cls.dated, created=CREATED_UTC)
        make_video(cls.blank)
        make_video(cls.other, pattern='smptebars', created=CREATED_UTC)
        make_video(cls.longer, seconds=4, created=CREATED_UTC)
        # The dated video again with only its metadata changed: same
        # pictures, different bytes
        subprocess.run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(cls.dated),
                        '-c', 'copy', '-map_metadata', '0', '-metadata', 'title=a copy', str(cls.retagged)],
                       check=True, capture_output=True)

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def put(self, sample, *parts):
        """Copy a sample video to root/<parts> and return the new path."""
        dst = self.root.joinpath(*parts)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(sample, dst)
        return dst

    def test_reads_media_created_and_moves_to_its_day(self):
        self.put(self.dated, '2019-01-01', 'clip.mp4')
        self.assertEqual(media_created(self.root / '2019-01-01' / 'clip.mp4'), CREATED_LOCAL)
        self.assertIsNone(media_created(self.blank))

        code, _ = run(self.root, '--apply-moves')

        self.assertEqual(code, 0)
        self.assertEqual(names(self.root / CREATED_DAY), ['clip.mp4'])
        self.assertEqual(names(self.root / '2019-01-01'), [])

    @unittest.skipUnless(EXIFTOOL, 'exiftool is needed to write video dates')
    def test_fill_blanks_writes_media_created_from_name_then_folder(self):
        from_name = self.put(self.blank, 'misc', '20190630_090136.mp4')
        from_folder = self.put(self.blank, '2019-08-30', 'deeper', 'clip.mp4')
        no_source = self.put(self.blank, '2014', 'clip.mp4')        # a year is not a date
        already = self.put(self.dated, '2019-08-30', 'dated.mp4')

        code, out = run(self.root, '--fill-blanks', '--dry-run')
        self.assertEqual(code, 0)
        self.assertIsNone(media_created(from_name), 'a dry run must not write anything')

        code, out = run(self.root, '--fill-blanks')

        self.assertEqual(code, 0)
        self.assertEqual(media_created(from_name), datetime.datetime(2019, 6, 30, 9, 1, 36))
        self.assertEqual(media_created(from_folder), datetime.datetime(2019, 8, 30, 12, 0, 0))
        self.assertIsNone(media_created(no_source))
        self.assertIn('SKIPPED (no date in filename or folder names)', out)
        self.assertEqual(media_created(already), CREATED_LOCAL, 'an existing date must be left alone')

    def test_move_incomplete_sets_aside_broken_videos_only(self):
        day = self.root / '2020-02-02'
        self.put(self.dated, '2020-02-02', 'good.mp4')
        (day / 'stub.mp4').write_bytes(b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom')   # header, no video
        (day / 'nulls.mp4').write_bytes(b'\x00' * 4096)
        (day / 'empty.mov').write_bytes(b'')

        code, out = run(self.root, '--move-incomplete')

        self.assertEqual(code, 0)
        self.assertEqual(names(day), ['good.mp4'])
        self.assertEqual(names(self.root / '_incomplete' / '2020-02-02'), ['empty.mov', 'nulls.mp4', 'stub.mp4'])
        for kind in ('no-video-header', 'null-filled', 'empty'):
            self.assertIn(f"MOVED ({kind})", out)

    def test_quarantine_ads_moves_ad_named_videos(self):
        day = self.root / '2020-02-02'
        ads = ['vuyyzy0brvod5gcaocnv.mp4', 'd5a210d011c47b8300bb8034048719a9.mp4',
               '55d58970f6cd4574f635d6e3_568-1443241239.mp4']
        for name in ads:
            self.put(self.blank, '2020-02-02', name)
        self.put(self.dated, '2020-02-02', '20200202_100000.mp4')

        code, _ = run(self.root, '--quarantine-ads')

        self.assertEqual(code, 0)
        self.assertEqual(names(day), ['20200202_100000.mp4'])
        self.assertEqual(names(self.root / '_ads' / '2020-02-02'), sorted(ads))

    def test_flatten_moves_videos_camcorder_files_and_sidecars(self):
        self.put(self.dated, CREATED_DAY, 'clip.mp4')
        self.put(self.blank, 'misc', 'undated.mp4')
        cam = self.root / '2018-01-16'
        cam.mkdir()
        (cam / '20180116122434.m2ts').write_bytes(b'camcorder video data')
        (cam / '20180116122434.m2ts.modd').write_bytes(b'sidecar')
        (cam / 'holiday.m2ts').write_bytes(b'camcorder video data')      # no date in its name

        code, _ = run(self.root, '--flatten')

        self.assertEqual(code, 0)
        for moved in ('clip.mp4', '20180116122434.m2ts', '20180116122434.m2ts.modd'):
            self.assertIn(moved, names(self.root))
        self.assertFalse((self.root / CREATED_DAY).exists())
        self.assertEqual(names(self.root / 'misc'), ['undated.mp4'])
        self.assertEqual(names(cam), ['holiday.m2ts'])

    def test_visual_compare_judges_video_pairs(self):
        # Name clashes as --flatten leaves them: <name>.mp4 and <name>_<date>.mp4
        pairs = {'copy': self.dated, 'retagged': self.retagged, 'other': self.other, 'longer': self.longer}
        for name, sample in pairs.items():
            self.put(self.dated, f"{name}.mp4")
            self.put(sample, f"{name}_{CREATED_DAY}.mp4")
        before = names(self.root)

        code, out = run(self.root, '--visual-compare', '--dry-run')

        self.assertEqual(code, 0)
        verdict = {ln.split(': ', 1)[1].split('_')[0]: ln for ln in out.splitlines() if ' | ' in ln}
        self.assertTrue(verdict['copy'].startswith('IDENTICAL (confidence certain'), verdict['copy'])
        self.assertTrue(verdict['retagged'].startswith('DUPLICATE (confidence high)'), verdict['retagged'])
        self.assertTrue(verdict['other'].startswith('DIFFERENT (confidence high)'), verdict['other'])
        self.assertTrue(verdict['longer'].startswith('DIFFERENT (confidence high)'), verdict['longer'])
        self.assertIn('video lengths differ', verdict['longer'])
        self.assertEqual([n for n in names(self.root) if not n.endswith('.xlsx')], before)


if __name__ == '__main__':
    unittest.main()
