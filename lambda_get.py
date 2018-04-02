#!/usr/bin/env python3
import boto3


def item_to_json(item):
    json_data = {}
    for k, v in item.items():
        if 'N' in v.keys():
            json_data[k] = int(v['N'])
        else:
            json_data[k] = next(iter(v.values()))
    return json_data


def lambda_handler(event, context):
    audiobooks = []
    dynamo = boto3.client('dynamodb')
    resp = dynamo.scan(TableName='audiobooks')
    if resp is not None and 'Items' in resp.keys():
        for item in resp['Items']:
            audiobooks.append(item_to_json(item))
    return audiobooks


if __name__ == '__main__':
    resp = lambda_handler({}, {})
    print(resp)
