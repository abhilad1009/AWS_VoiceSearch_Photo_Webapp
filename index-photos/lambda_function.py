import logging
import base64
import json
import boto3
import os
import time
import requests
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from pattern.en import singularize


def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)


def lambda_handler(event, context):

    print("Lambda Index Photos")
    print("event:", event)

    s3_metadata = event['Records'][0]['s3']
    s3_bucket = s3_metadata['bucket']['name']
    s3_key = s3_metadata['object']['key']
    # print(s3_bucket)
    # print(s3_key)

    client = boto3.client('rekognition')
    img_obj = {'S3Object': {'Bucket': s3_bucket, 'Name': s3_key}}
    print("img_obj", img_obj)

    labels_resp = client.detect_labels(Image=img_obj)
    print("rekognition response:", labels_resp)
    timestamp = time.time()

    labels = []

    for i in range(len(labels_resp['Labels'])):
        try:
            labels.append(singularize(labels_resp['Labels'][i]['Name'].lower()))
        except:
            labels.append(labels_resp['Labels'][i]['Name'].lower())

    s3 = boto3.client('s3')
    img_s3_data = s3.head_object(Bucket=s3_bucket, Key=s3_key)

    if img_s3_data["Metadata"]:
        customlabels = img_s3_data["Metadata"]["customlabels"]
        print("customlabels : ", customlabels)
        customlabels = customlabels.split(',')
        customlabels = list(map(lambda x: x.lower(), customlabels))
        for cl in customlabels:
            print(cl)
            try:
                cl = singularize(cl.lower().strip())
            except:
                cl = cl.lower().strip()
            if cl not in label_names:
                labels.append(cl)

    print(labels)

    elastic_data = {'objectKey': s3_key,
                    'bucket': s3_bucket,
                    'createdTimestamp': timestamp,
                    'labels': labels}

    REGION = 'us-east-1'
    HOST = "search-photos-zurqo2mqy4mfjloidzi62aoxsq.us-east-1.es.amazonaws.com"  # add host here
    INDEX = "photos"  # add index
    client = OpenSearch(hosts=[{
        'host': HOST,
        'port': 443
    }],
        http_auth=get_awsauth(REGION, 'es'),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection)

    resp = client.index(index='photos', id=s3_key, body=elastic_data)
    print(resp)
    # add elastic url here for indexing
    # url = "https://search-photos-zurqo2mqy4mfjloidzi62aoxsq.us-east-1.es.amazonaws.com/photos"
    # headers = {"Content-Type": "application/json"}

    # service = 'es'
    # credentials = boto3.Session().get_credentials()
    # awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
    #                REGION, service, session_token=credentials.token)

    # r = requests.put(url, auth=awsauth ,data=json.dumps(elastic_data).encode("utf-8"),headers=headers)  # requests.get, post, and delete have similar syntax
    # print(r.text)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Request-Headers': '*',
            'Access-Control-Allow-Headers': '*'

        },
        'body': json.dumps('Index Photos Executed')
    }
