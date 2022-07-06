from aws_lambda_powertools import Logger, Tracer

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context(log_event=True)  # type:ignore
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    if event["status"] == "SUCCEEDED":
        return {"status": "SUCCEEDED", "event": event}
    else:
        return {"status": "FAILED", "event": event}
