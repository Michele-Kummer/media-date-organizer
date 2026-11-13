"""Plist and XMP files saved under a photo name (IMG_E5239.JPG) are reported,
never failed on, renamed or deleted (US-28, BUG-25), and --move-junk moves
them, and loose .plist and .xmp files, into _junk (US-14).
Run with: py -m unittest discover tests -v"""

import datetime
import pathlib
import shutil
import tempfile
import unittest

from test_dry_run import snapshot
from test_smoke import make_image, names, organize, run

# What an iPhone .AAE edit file holds
AAE = (b'<?xml version="1.0" encoding="UTF-8"?>\n'
       b'<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
       b'"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
       b'<plist version="1.0"><dict><key>adjustmentFormatIdentifier</key>'
       b'<string>com.apple.photo</string></dict></plist>\n')
XMP = (b'<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
       b'<x:xmpmeta xmlns:x="adobe:ns:meta/"></x:xmpmeta>\n<?xpacket end="w"?>')
BINARY_PLIST = b'bplist00\xd1\x01\x02Qa\x10\x01\x08\x0b\r\x00\x00\x00\x00\x00\x00\x01\x01'


class PlistTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.day = self.root / '2023-08-07'
        make_image(self.day / 'IMG_5239.JPG', taken=datetime.datetime(2023, 8, 7, 9, 0, 0))
        make_image(self.day / 'undated.jpg')
        (self.day / 'IMG_E5239.JPG').write_bytes(AAE)
        (self.day / 'IMG_E6230.jpg').write_bytes(XMP)
        (self.day / 'shot.png').write_bytes(BINARY_PLIST)

    def test_kinds(self):
        self.assertEqual(organize.not_media_kind(str(self.day / 'IMG_E5239.JPG')), 'plist')
        self.assertEqual(organize.not_media_kind(str(self.day / 'IMG_E6230.jpg')), 'XMP')
        self.assertEqual(organize.not_media_kind(str(self.day / 'shot.png')), 'binary plist')
        self.assertIsNone(organize.not_media_kind(str(self.day / 'IMG_5239.JPG')))
        self.assertIsNone(organize.not_media_kind(str(self.day / 'undated.jpg')))

    def test_find_plists_lists_them_and_changes_nothing(self):
        before = snapshot(self.root)
        code, out = run(self.root, '--find-plists', '--apply')
        self.assertEqual(code, 0, out)
        self.assertIn('NOT MEDIA (plist file named .JPG): 2023-08-07/IMG_E5239.JPG', out)
        self.assertIn('NOT MEDIA (XMP file named .jpg): 2023-08-07/IMG_E6230.jpg', out)
        self.assertIn('NOT MEDIA (binary plist file named .png): 2023-08-07/shot.png', out)
        self.assertIn('"not-media": 3', out)
        self.assertEqual(snapshot(self.root), before)

    def test_other_phases_report_them_and_leave_them_alone(self):
        plists = {n: (self.day / n).read_bytes() for n in ('IMG_E5239.JPG', 'IMG_E6230.jpg', 'shot.png')}
        code, out = run(self.root, '--fill-blanks', '--convert-png', '--apply-moves', '--apply')
        self.assertEqual(code, 0, out)
        self.assertNotIn('FAILED', out)
        self.assertIn('NOT MEDIA (plist file named .JPG, left for --move-junk): 2023-08-07/IMG_E5239.JPG', out)
        self.assertIn('NOT MEDIA (binary plist file named .png, left for --move-junk)', out)
        # Not written to, converted, moved or given a date suffix
        for n, content in plists.items():
            self.assertEqual((self.day / n).read_bytes(), content, n)
        self.assertNotIn('shot.jpg', names(self.day))
        self.assertNotIn('img_e5239_2023-08-07.jpg', names(self.day))
        # The real undated photo still got its date
        self.assertIn('undated.jpg', names(self.day))

    def test_fix_extensions_reports_them_as_not_media(self):
        code, out = run(self.root, '--fix-extensions', '--apply')
        self.assertEqual(code, 0, out)
        self.assertIn('NOT MEDIA (plist file named .JPG, left for --move-junk)', out)
        self.assertIn('NOT MEDIA (XMP file named', out)
        self.assertNotIn('UNKNOWN', out)
        self.assertIn('img_e5239.jpg', names(self.day))

    def test_move_junk_previews_then_moves_them_into_junk(self):
        (self.day / 'IMG_5239.xmp').write_bytes(XMP)
        (self.day / 'Info.plist').write_bytes(AAE)
        before = snapshot(self.root)

        code, out = run(self.root, '--move-junk')
        self.assertEqual(code, 0, out)
        self.assertEqual(snapshot(self.root), before, 'a dry run must not move anything')
        self.assertIn('WOULD MOVE (plist file named .JPG): ', out)

        contents = {n: (self.day / n).read_bytes()
                    for n in ('IMG_E5239.JPG', 'IMG_E6230.jpg', 'shot.png', 'IMG_5239.xmp', 'Info.plist')}
        code, out = run(self.root, '--move-junk', '--apply')
        self.assertEqual(code, 0, out)
        self.assertIn('MOVED (XMP file named .jpg): ', out)
        self.assertIn('MOVED (binary plist file named .png): ', out)
        self.assertIn('MOVED (XMP file): ', out)
        self.assertIn('MOVED (PLIST file): ', out)
        self.assertIn('"moved-not-media": 3', out)
        self.assertIn('"moved-plist-xmp": 2', out)
        # Moved unchanged, not deleted; the real photos stay
        junk = self.root / '_junk'
        for n, content in contents.items():
            self.assertEqual((junk / n).read_bytes(), content, n)
        self.assertEqual(names(self.day), ['img_5239.jpg', 'undated.jpg'])

    def test_all_moves_them_before_the_date_steps_see_them(self):
        code, out = run(self.root, '--all', '--apply')
        self.assertEqual(code, 0, out)
        # --fix-extensions runs first and lists them; no step after
        # --move-junk sees them
        after_junk = out.split('----- move_incomplete -----')[1].split('Summary of this run')[0]
        self.assertNotIn('NOT MEDIA', after_junk)
        self.assertEqual(names(self.root / '_junk'), ['img_e5239.jpg', 'img_e6230.jpg', 'shot.png'])


if __name__ == '__main__':
    unittest.main()
