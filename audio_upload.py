#!/usr/bin/env python3
import boto3
import os
import sys
from simplempeginfo import Mpeg4

AU_S3_BUCKET = os.getenv('AU_S3_BUCKET', 'mybucket')
AU_DB_TABLE = os.getenv('AU_DB_TABLE', 'mytable')


class ProgressMonitor:
    def __init__(self, size):
        self.size = size
        self.transfered_so_far = 0
        self.completed = False
        try:
            import progressbar
            self.progress_bar = progressbar.ProgressBar(max_value=size, widgets=[
                ' [', progressbar.Timer(), '] ',
                progressbar.Bar(),
                ' (', progressbar.ETA(), ') ',
            ])
        except Exception:
            self.progress_bar = None

    def __call__(self, bytes_transfered):
        self.transfered_so_far += bytes_transfered
        if self.transfered_so_far >= self.size:
            self.completed = True
        if self.progress_bar is not None:
            if self.completed:
                self.progress_bar.update(self.size)
            else:
                self.progress_bar.update(self.transfered_so_far)


def upload_file(s3, filename, progress_monitor):
    with open(filename, 'rb') as file:
        s3.upload_fileobj(file, AU_S3_BUCKET, os.path.basename(filename), Callback=progress_monitor)
        if progress_monitor.completed:
            return True
    return False


def register_file(db, filename, size, mpeg):
    put_item = {'name': {'S': mpeg.title}, 'filename': {'S': filename}, 'author': {'S': mpeg.author}, 'comment': {'S': mpeg.comment},
                'size': {'N': str(size)}, 'length': {'N': str(mpeg.length_in_milliseconds)}, 'chapters_len': {'N': str(len(mpeg.chapters))}}
    resp = db.put_item(TableName=AU_DB_TABLE, Item=put_item)
    return resp['ResponseMetadata']['HTTPStatusCode'] == 200


def upload(filename, size, mpeg):
    resp = []
    s3 = boto3.client('s3')
    uploaded = upload_file(s3, filename, ProgressMonitor(size))
    if uploaded:
        db = boto3.client('dynamodb')
        registered = register_file(db, os.path.basename(filename), size, mpeg)
        resp.append((uploaded, registered))
    return resp


def usage():
    sys.stderr.write('Usage: ' + sys.argv[0] + ' <audio_filename>\n\n')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)
    else:
        try:
            filename = sys.argv[1]
            size = os.stat(filename).st_size
            mp4 = Mpeg4(filename)
        except Exception:
            usage()
            sys.exit(1)
        resp = upload(filename, size, mp4)
        print(resp)
