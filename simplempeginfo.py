#!/usr/bin/env python3
from collections import namedtuple

SMI_TIME_BASE = 1000000.0
SMI_DURATION_CONSTANT_MP4 = 5.0


class Mpeg:
    def __init__(self):
        self.read_meta = False
        self.read_chpl = False
        self.read_mvhd = False
        self.title = None
        self.author = None
        self.length_in_milliseconds = None
        self.duration = None
        self.timescale = None
        self.comment = None
        self.chapters = []

    def named_tuple(self):
        MpegTuple = namedtuple('MpegTuple', ['title', 'author', 'length_in_milliseconds', 'duration', 'timescale', 'comment', 'chapters', 'length_str'])
        return MpegTuple(self.title, self.author, self.length_in_milliseconds, self.duration, self.timescale, self.comment, self.chapters, self.getLengthStr())

    def tuple(self):
        return tuple(self.named_tuple()._asdict().values())


class Mpeg4(Mpeg):
    def __init__(self, filename):
        super().__init__()
        with open(filename, 'rb') as file:
            self.readAtoms(file, 0, file.seek(0, 2))
            self.length_in_milliseconds = (self.duration / self.timescale) * 1000.0

    def getIntBE(self, b):
        return b[3] | (b[2] << 8) | (b[1] << 16) | (b[0] << 24)

    def readChapters(self, a):
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

    def readMeta(self, f, pos, end):
        if pos + 8 < end:
            f.seek(pos + 4)  # skips always 0 byte
            bytesRead = f.read(4)
            atomSize = self.getIntBE(bytesRead)
            pos = f.seek(pos + 8 + atomSize + 4)  # skips hdlr atom
            while pos < end:
                pos = f.seek(pos + 4)
                bytesRead = f.read(4)
                tag = bytesRead.decode('iso8859-1')
                bytesRead = f.read(4)
                dataSize = self.getIntBE(bytesRead)
                f.seek(pos + 20)
                bytesRead = f.read(dataSize - 16)
                pos = f.tell()
                self.add_tag(tag, bytesRead.decode('utf-8'))

    def getLengthStr(self):
        length = self.duration / self.timescale
        ms = (100 * ((self.duration * 1000.0) % SMI_TIME_BASE)) / SMI_TIME_BASE
        s = length % 60
        length /= 60
        m = length % 60
        h = length / 60
        return '%.2d:%.2d:%.2d.%.2d' % (h, m, s, ms)

    def getDurationStr(self):
        return 'duration: %d, timescale: %d => %s' % (self.duration, self.timescale, self.getLengthStr())

    def readMvhd(self, a):
        version = int(a[0])
        if version == 1:
            vshift = 8
        else:
            vshift = 4
        a = a[4:]
        a = a[vshift * 2:]
        self.timescale = float(self.getIntBE(a[:4]))
        a = a[4:]
        self.duration = float(self.getIntBE(a[:vshift])) + SMI_DURATION_CONSTANT_MP4

    def readAtoms(self, f, pos, end):
        if pos < end:
            f.seek(pos)
            bytesRead = f.read(4)
            nRead = len(bytesRead)
            pos = pos + nRead
            while nRead > 0:
                atomSize = self.getIntBE(bytesRead)
                if atomSize < 1:
                    break
                bytesRead = f.read(4)
                nRead = len(bytesRead)
                pos = pos + nRead
                atomName = bytesRead.decode('utf-8')
                # print('atom name: %s' % atomName)
                if atomName in ['moov', 'udta']:
                    self.readAtoms(f, pos, pos + atomSize - 8)
                elif atomName == 'meta' and not self.read_meta:
                    self.readMeta(f, pos, pos + atomSize - 8)
                    self.read_meta = True
                elif atomName == 'chpl' and not self.read_chpl:
                    self.readChapters(f.read(atomSize - 8))
                    self.read_chpl = True
                elif atomName in ['mvhd'] and not self.read_mvhd:
                    self.readMvhd(f.read(atomSize - 8))
                    self.read_mvhd = True
                pos = f.seek(pos + atomSize - 8)
                bytesRead = f.read(4)
                nRead = len(bytesRead)
                pos = pos + nRead


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = './h.mp4'
    mp4 = Mpeg4(filename)
    print(mp4.getLengthStr())
    print(mp4.tuple())
