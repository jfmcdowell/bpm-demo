import datetime
import json

import boto3
from aws_lambda_powertools import Logger, Tracer

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context(log_event=True)  # type:ignore
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    eventbridge_client = boto3.client("events")
    request_body = event["body"]
    if request_body is None:
        request_body = ""
    # Structure of EventBridge Event
    eventbridge_event = {
        "Time": datetime.datetime.now(),
        "Source": "com.mycompany.myapp",
        "Detail": request_body,
        "DetailType": "service_status",
    }

    # Send event to EventBridge
    response = eventbridge_client.put_events(Entries=[eventbridge_event])

    logger.info(response)

    # Returns success reponse to API Gateway
    return {
        "statusCode": 200,
        "body": json.dumps({"result": "from Producer"}),
    }
