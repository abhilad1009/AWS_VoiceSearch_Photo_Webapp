import json
import boto3
# import requests
# from botocore.vendored import requests
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from nltk.stem.porter import *

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

    response = client.recognize_text(botId='YW3ZEYEMOT',
                                     botAliasId='NB14OMR44L',
                                     localeId='en_US',
                                     sessionId="test0",
                                     text=searchquery)
    print(response)
    lex_response = response['sessionState']['intent']
    keys = []

    stemmer = PorterStemmer()

    if "key1" in lex_response["slots"] and lex_response["slots"]["key1"] != None:
        try:
            keys.append(stemmer.stem(lex_response["slots"]["key1"]['value']['interpretedValue'].lower()))
        except:
            keys.append(lex_response["slots"]["key1"]['value']['interpretedValue'].lower())
    if "key2" in lex_response["slots"] and lex_response["slots"]["key2"] != None:
        try:
            keys.append(stemmer.stem(lex_response["slots"]["key2"]['value']['interpretedValue'].lower()))
        except:
            keys.append(lex_response["slots"]["key2"]['value']['interpretedValue'].lower())

    print(keys)
# https://search-photos-tyo2a2wcxqrw4ntex5gzhk5oya.us-east-1.es.amazonaws.com/
    REGION = 'us-east-1'
    HOST = "search-photos-tyo2a2wcxqrw4ntex5gzhk5oya.us-east-1.es.amazonaws.com"  # add host here
    INDEX = "photos"  # add index
    client = OpenSearch(hosts=[{
        'host': HOST,
        'port': 443
    }],
        http_auth=get_awsauth(REGION, 'es'),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection)

    results = set()
    for k in keys:

        q = {'size': 100, 'query': {'multi_match': {'query': k}}}
        res = client.search(index=INDEX, body=q)
        hits = res['hits']['hits']
        for hit in hits:
            results.add(hit['_source']['objectKey'])

    return {
        'statusCode': 200,
        'headers': {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*"},
        'body': json.dumps({"files": list(results)})
    }
