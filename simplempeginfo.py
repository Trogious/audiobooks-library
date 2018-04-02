#!/usr/bin/env python3
from collections import namedtuple

SMI_TIME_BASE = 1000000.0
SMI_DURATION_CONSTANT_MP4 = 5.0
SMI_MAX_READ_ID3V2 = 512
SOI = b'\xFF\xD8'
APP0MARKER = b'\xFF\xE0'
IDENTIFIER = b'JFIF\x00'
EOI = b'\xFF\xD9'


class Mpeg:
    def __init__(self):
        self.title = None
        self.author = None
        self.length_in_milliseconds = None
        self.duration = None
        self.timescale = None
        self.comment = None
        self.chapters = []

    def named_tuple(self):
        MpegTuple = namedtuple('MpegTuple', ['title', 'author', 'length_in_milliseconds', 'duration', 'timescale', 'comment', 'chapters', 'length_str'])
        return MpegTuple(self.title, self.author, self.length_in_milliseconds, self.duration, self.timescale, self.comment, self.chapters, self.get_length_str())

    def tuple(self):
        return tuple(self.named_tuple()._asdict().values())

    def get_int_big_endian(self, b):
        return b[3] | (b[2] << 8) | (b[1] << 16) | (b[0] << 24)


class Mpeg4(Mpeg):
    def __init__(self, filename):
        super().__init__()
        self.meta_read = False
        self.chpl_read = False
        self.mvhd_read = False
        with open(filename, 'rb') as file:
            self.read_cover_image(file)
            file.tell()
            self.read_atoms(file, 0, file.seek(0, 2))
            self.length_in_milliseconds = (self.duration / self.timescale) * 1000.0

    def read_cover_image(self, f):
        # mov_write_video_tag
        data = f.read()
        s = data.find(SOI)
        e = data.find(EOI)
        # with open('out.jpg', 'wb') as o:
        #    o.write(data[s:e])

    def get_int_big_endian(self, b):
        return b[3] | (b[2] << 8) | (b[1] << 16) | (b[0] << 24)

    def read_chapters(self, a):
        a = a[8:]
        chapters_count = int(a[0])
        a = a[1:]
        while chapters_count > 0:
            a = a[8:]
            titleLen = int(a[0])
            a = a[1:]
            t = a[:titleLen]
            a = a[titleLen:]
            self.chapters.append(t.decode('utf8'))
            chapters_count -= 1

    def verify_tag(self, tag, name):
        return tag == b'\xa9'.decode('iso8859-1') + name

    def add_tag(self, tag, value):
        if self.verify_tag(tag, 'nam'):
            self.title = value
        elif self.verify_tag(tag, 'ART'):
            self.author = value
        elif self.verify_tag(tag, 'cmt'):
            self.comment = value

    def read_meta(self, f, pos, end):
        if pos + 8 < end:
            f.seek(pos + 4)  # skips always 0 byte
            bytesRead = f.read(4)
            atomSize = self.get_int_big_endian(bytesRead)
            pos = f.seek(pos + 8 + atomSize + 4)  # skips hdlr atom
            while pos < end:
                pos = f.seek(pos + 4)
                bytesRead = f.read(4)
                tag = bytesRead.decode('iso8859-1')
                bytesRead = f.read(4)
                dataSize = self.get_int_big_endian(bytesRead)
                f.seek(pos + 20)
                bytesRead = f.read(dataSize - 16)
                pos = f.tell()
                self.add_tag(tag, bytesRead.decode('utf-8'))

    def get_length_str(self):
        length = self.duration / self.timescale
        ms = (100 * ((self.duration * 1000.0) % SMI_TIME_BASE)) / SMI_TIME_BASE
        s = length % 60
        length /= 60
        m = length % 60
        h = length / 60
        return '%.2d:%.2d:%.2d.%.2d' % (h, m, s, ms)

    def get_duration_str(self):
        return 'duration: %d, timescale: %d => %s' % (self.duration, self.timescale, self.get_length_str())

    def read_mvhd(self, a):
        version = int(a[0])
        if version == 1:
            vshift = 8
        else:
            vshift = 4
        a = a[4:]
        a = a[vshift * 2:]
        self.timescale = float(self.get_int_big_endian(a[:4]))
        a = a[4:]
        self.duration = float(self.get_int_big_endian(a[:vshift])) + SMI_DURATION_CONSTANT_MP4

    def read_atoms(self, f, pos, end):
        if pos < end:
            f.seek(pos)
            bytesRead = f.read(4)
            nRead = len(bytesRead)
            pos = pos + nRead
            while nRead > 0:
                atom_size = self.get_int_big_endian(bytesRead)
                if atom_size < 1:
                    break
                bytesRead = f.read(4)
                nRead = len(bytesRead)
                pos = pos + nRead
                atom_name = bytesRead.decode('utf-8')
                print('atom name: %s' % atom_name)
                if atom_name in ['moov', 'udta', 'mdat']:
                    self.read_atoms(f, pos, pos + atom_size - 8)
                elif atom_name == 'meta' and not self.meta_read:
                    self.read_meta(f, pos, pos + atom_size - 8)
                    self.meta_read = True
                elif atom_name == 'chpl' and not self.chpl_read:
                    self.read_chapters(f.read(atom_size - 8))
                    self.chpl_read = True
                elif atom_name in ['mvhd'] and not self.mvhd_read:
                    self.read_mvhd(f.read(atom_size - 8))
                    self.mvhd_read = True
                pos = f.seek(pos + atom_size - 8)
                bytesRead = f.read(4)
                nRead = len(bytesRead)
                pos = pos + nRead


class Mpeg3(Mpeg):
    def __init__(self, filename):
        super().__init__()
        with open(filename, 'rb') as file:
            self.bytes = file.read(SMI_MAX_READ_ID3V2)
        self.process_id3v2()

    def process_id3v2(self):
        if self.bytes is not None:
            pos = 0
            if self.bytes[:3].decode('utf8') == 'ID3':
                pos += 6
                id3v2_size = self.get_int_big_endian(self.bytes[pos:pos+4]) - 10
                pos += 4
                while pos < min(SMI_MAX_READ_ID3V2, id3v2_size):
                    pos = self.process_frame(pos)

    def process_frame(self, pos):
        frame = self.bytes[pos:pos+4]
        pos += 4
        size = self.get_int_big_endian(self.bytes[pos:pos+4])
        pos += 6
        if size > 0:
            content = self.bytes[pos+1:pos+size]
            if frame == b'TIT2':
                self.title = content.decode('utf8')
            elif frame == b'TPE1':
                self.author = content.decode('utf8')
            elif frame == b'COMM':
                self.comment = content.decode('utf8')
            elif frame == b'TLEN':
                self.duration = float(content.decode('utf8'))
                self.length_in_milliseconds = self.duration * 10
                self.timescale = 1.0
            elif frame == b'TRCK':
                pass
            elif frame == b'TXXX':
                pass
            pos += size
        return pos

    def get_length_str(self):
        length = self.duration
        ms = length % 100
        length /= 100
        s = length % 60
        length /= 60
        m = length % 60
        h = length / 60
        return '%.2d:%.2d:%.2d.%.2d' % (h, m, s, ms)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = './sq.mp4'
    if filename.endswith('.mp4'):
        mpeg = Mpeg4(filename)
    else:
        mpeg = Mpeg3(filename)
    print(mpeg.tuple())
