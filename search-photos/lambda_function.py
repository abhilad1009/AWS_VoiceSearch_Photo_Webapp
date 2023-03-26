import json
import boto3
# import requests
from botocore.vendored import requests
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth


def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)


def lambda_handler(event, context):
    print((event))
    print(event['queryStringParameters']['q'])

    client = boto3.client('lexv2-runtime')
    searchquery = event['queryStringParameters']['q']

    response = client.recognize_text(botId='LCISKB6Q4C',
                                     botAliasId='Q3BOF5V2X9',
                                     localeId='en_US',
                                     sessionId="test0",
                                     text=searchquery)
    print(response)
    lex_response = response['sessionState']['intent']
    keys = []
    if "key1" in lex_response["slots"] and lex_response["slots"]["key1"] != None:
        keys.append(lex_response["slots"]["key1"]['value']['interpretedValue'])
    if "key2" in lex_response["slots"] and lex_response["slots"]["key2"] != None:
        keys.append(lex_response["slots"]["key2"]['value']['interpretedValue'])

    print(keys)

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

    results = []
    for k in keys:

        q = {'size': 100, 'query': {'multi_match': {'query': k}}}
        res = client.search(index=INDEX, body=q)
        hits = res['hits']['hits']
        for hit in hits:
            results.append(hit['_source']['objectKey'])

    return {
        'statusCode': 200,
        'headers': {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*"},
        'body': json.dumps({"files": results})
    }
