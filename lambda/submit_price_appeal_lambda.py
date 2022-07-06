import json

from aws_lambda_powertools import Logger, Tracer

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context(log_event=True)  # type:ignore
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    logger.info(event)

    return {
        "statusCode": 200,
        "status": "SUCCEEDED",
        "body": json.dumps({"result": "testing..."}),
    }
