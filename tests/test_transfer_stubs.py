"""Tests for phone transfer stubs: MTP object property lists that Windows
leaves under a photo's name when a copy from a phone fails. They hold the
photo's properties (date created, file name, size) but none of its bytes,
and --move-incomplete sets them aside.

Run from the repository root:
    py -m unittest discover tests -v
"""
import pathlib
import shutil
import struct
import tempfile
import unittest

from test_smoke import make_image, names, organize, run


def mtp_entry(handle, code, dtype, value):
    """One property list entry: handle, property code, data type, value."""
    return struct.pack('<IHH', handle, code, dtype) + value


def mtp_string(text):
    """An MTP string: a character count (with the closing null), then UTF-16."""
    if not text:
        return b'\x00'
    return bytes([len(text) + 1]) + (text + '\x00').encode('utf-16-le')


def mtp_list(*entries):
    return struct.pack('<I', len(entries)) + b''.join(entries)


# The three shapes found in a real failed transfer (E:\Pictures\2018\Temp)
ONE_SIZE = mtp_list(mtp_entry(0x1A17, 0xDC89, 0x0006, struct.pack('<I', 0x2EDE)))
TWO_ZEROS = mtp_list(mtp_entry(0x1E86C2, 0xDC87, 0x0006, b'\0' * 4),
                     mtp_entry(0x1E86C2, 0xDC88, 0x0006, b'\0' * 4))
FULL = mtp_list(
    mtp_entry(0x133D, 0xDC01, 0x0006, struct.pack('<I', 0x10001)),
    mtp_entry(0x133D, 0xDC03, 0x0004, b'\0\0'),
    mtp_entry(0x133D, 0xDC08, 0xFFFF, mtp_string('20180501T093923.')),
    mtp_entry(0x133D, 0xDC44, 0xFFFF, mtp_string('img_2018_05_01_09_39_23.jpg')),
    mtp_entry(0x133D, 0xDC4F, 0x0002, b'\0'),
    mtp_entry(0x133D, 0xD901, 0x0002, b'\0'),
)


class TransferStubTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write(self, name, data):
        path = self.root / name
        path.write_bytes(data)
        return str(path)

    def test_recognises_each_stub_shape(self):
        for i, data in enumerate((ONE_SIZE, TWO_ZEROS, FULL)):
            path = self.write(f"stub{i}.jpg", data)
            self.assertTrue(organize._is_mtp_prop_list(path), i)
            self.assertEqual(organize._incomplete_kind(path), 'transfer-stub')

    def test_rejects_real_photos_and_near_misses(self):
        photo = self.root / 'photo.jpg'
        make_image(photo)
        near_misses = {
            'trailing.jpg': FULL + b'\x01',                                      # extra byte
            'short.jpg': FULL[:-1],                                              # cut short
            'zero.jpg': struct.pack('<I', 0) + b'\0' * 12,                       # no entries
            'code.jpg': mtp_list(mtp_entry(1, 0x1234, 0x0006, b'\0' * 4)),       # not an MTP property
            'type.jpg': mtp_list(mtp_entry(1, 0xDC89, 0x0042, b'\0' * 4)),       # unknown data type
            'big.jpg': struct.pack('<I', 0x10000000) + b'\0' * 12,               # count far too large
        }
        self.assertFalse(organize._is_mtp_prop_list(str(photo)))
        self.assertIsNone(organize._incomplete_kind(str(photo)))
        for name, data in near_misses.items():
            self.assertFalse(organize._is_mtp_prop_list(self.write(name, data)), name)

    def test_fix_extensions_names_stubs_instead_of_unknown_format(self):
        self.write('stub.jpg', FULL)

        code, out = run(self.root, '--fix-extensions')

        self.assertEqual(code, 0)
        self.assertIn('TRANSFER STUB (no picture, left for --move-incomplete): stub.jpg', out)
        self.assertNotIn('UNKNOWN FORMAT', out)

    def test_move_incomplete_sets_stubs_aside_with_folder_date(self):
        day = self.root / '2018-05-01'
        day.mkdir()
        make_image(day / 'good.jpg')
        (day / 'img_2018_05_01_09_39_23.jpg').write_bytes(FULL)
        (day / 'homescreenPreview.png').write_bytes(TWO_ZEROS)

        code, out = run(self.root, '--move-incomplete')
        self.assertEqual(code, 0)
        self.assertIn('WOULD MOVE (transfer-stub)', out)
        self.assertEqual(len(names(day)), 3, 'a dry run must not move anything')

        code, out = run(self.root, '--move-incomplete', '--apply')

        self.assertEqual(code, 0)
        self.assertEqual(names(day), ['good.jpg'])
        self.assertEqual(names(self.root / '_incomplete'),
                         ['homescreenpreview_2018-05-01.png', 'img_2018_05_01_09_39_23.jpg'])


if __name__ == '__main__':
    unittest.main()
