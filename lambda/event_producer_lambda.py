import datetime
import json
import os
import uuid

import boto3
from aws_lambda_powertools import Logger, Tracer

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context(log_event=True)  # type:ignore
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    client = boto3.client("stepfunctions")
    state_machine_arn = os.environ["STATE_MACHINE_ARN"]
    transaction_id = str(uuid.uuid1())
    request_body = event["body"]
    if request_body is None:
        request_body = ""
    # Structure of Event
    event = {
        "TransctionID": transaction_id,
        "Time": json.dumps(datetime.datetime.now(), default=str),
        "Source": "com.mycompany.myapp",
        "Detail": request_body,
        "DetailType": "service_status",
    }

    # Send event to Stepfunction

    response = client.start_execution(
        stateMachineArn=state_machine_arn, name=transaction_id, input=json.dumps(event)
    )

    logger.info(response)

    # Returns success reponse to API Gateway
    return {
        "statusCode": 200,
        "body": json.dumps({"result": "from Producer"}),
    }
