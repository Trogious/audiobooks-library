#!/usr/bin/env python3
import boto3
import os
import sys


def upload_file(s3, filename):
    body = None
    with open(filename, 'rb') as f:
        body = f.read()
    if body is not None:
        resp = s3.put_object(Bucket='aswmudnet', Key='files/' + filename, Body=body)
        if resp['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
    return False


def register_file(db, filename, name, size, length):
    put_item = {'name': {'S': name}, 'filename': {'S': filename}, 'size': {'N': str(size)}, 'length': {'N': str(length)}}
    resp = db.put_item(TableName='audiobooks', Item=put_item)
    return resp['ResponseMetadata']['HTTPStatusCode'] == 200


def upload(filename, name, size, length):
    resp = []
    s3 = boto3.client('s3')
    uploaded = upload_file(s3, filename)
    if uploaded:
        db = boto3.client('dynamodb')
        registered = register_file(db, filename, name, size, length)
        resp.append((uploaded, registered))
    return resp


def usage():
    sys.stderr.write('Usage: ' + sys.argv[0] + ' <audio_filename>\n\n')


if __name__ == '__main__':
    from Mpeg4 import Mpeg4
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)
    else:
        try:
            filename = sys.argv[1]
            size = os.stat(filename).st_size
            mp4 = Mpeg4(filename)
            milliseconds = mp4.duration
            name = mp4.title
        except Exception:
            usage()
            sys.exit(1)
        resp = upload(filename, name, size, milliseconds)
        print(resp)
