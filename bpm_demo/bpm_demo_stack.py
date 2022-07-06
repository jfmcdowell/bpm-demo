from aws_cdk import Duration, Stack
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_logs as logs
from aws_cdk import aws_stepfunctions as stepfunctions
from aws_cdk import aws_stepfunctions_tasks as sftasks
from aws_solutions_constructs.aws_lambda_stepfunctions import LambdaToStepfunctions
from constructs import Construct


class BpmDemoStack(Stack):
    """Supress Linting"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # AWS Lambda Powertools Layer definition

        powertools_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            id="lambda-powertools",
            layer_version_arn=f"arn:aws:lambda:{self.region}:017000801446:layer:AWSLambdaPowertoolsPython:21",
        )

        # Pricing - Submit Price appeal mock lambda definition

        submit_price_appeal_lambda = _lambda.Function(
            self,
            "mockSubmitPriceAppeal",
            description="Submit Price Appeal Lambda function",
            runtime=_lambda.Runtime.PYTHON_3_9,  # type: ignore
            handler="submit_price_appeal_lambda.lambda_handler",
            code=_lambda.Code.from_asset("./lambda/"),
            architecture=_lambda.Architecture.ARM_64,  # type: ignore
            log_retention=logs.RetentionDays("TWO_WEEKS"),
            tracing=_lambda.Tracing.ACTIVE,
            layers=[powertools_layer],
        )

        # Status Check Lambda definition

        status_lambda = _lambda.Function(
            self,
            "statusCheckLambda",
            description="Check Status in Stepfunction",
            runtime=_lambda.Runtime.PYTHON_3_9,  # type: ignore
            handler="status_lambda.lambda_handler",
            code=_lambda.Code.from_asset("./lambda/"),
            architecture=_lambda.Architecture.ARM_64,  # type: ignore
            log_retention=logs.RetentionDays("TWO_WEEKS"),
            tracing=_lambda.Tracing.ACTIVE,
            layers=[powertools_layer],
        )

        # State machine definitons

        submit_price_appeal_step = sftasks.LambdaInvoke(
            self,
            "Submit Price Appeal",
            lambda_function=submit_price_appeal_lambda,  # type: ignore
            output_path="$.Payload",
        )

        wait_step = stepfunctions.Wait(
            self, "Wait 30 seconds", time=stepfunctions.WaitTime.duration(Duration.seconds(30))
        )

        status_step = sftasks.LambdaInvoke(
            self,
            "Get Status",
            lambda_function=status_lambda,  # type: ignore
            output_path="$.Payload",
        )

        fail_step = stepfunctions.Fail(
            self,
            "Fail",
            cause="Data Producer Failed",
            error="Job returned as failed",
        )

        succeed_step = stepfunctions.Succeed(self, "Succeeded", comment="Job Succeded")

        # Create Chain

        definition = (
            submit_price_appeal_step.next(wait_step)
            .next(status_step)
            .next(
                stepfunctions.Choice(self, "Job Complete?")
                .when(stepfunctions.Condition.string_equals("$.status", "FAILED"), fail_step)
                .when(stepfunctions.Condition.string_equals("$.status", "SUCCEDED"), succeed_step)
                .otherwise(wait_step)
            )
        )

        event_producer_lambda = LambdaToStepfunctions(
            self,
            "EventProducerLambda",
            lambda_function_props=_lambda.FunctionProps(
                description="Event Producer Lambda Function",
                runtime=_lambda.Runtime.PYTHON_3_9,  # type: ignore
                handler="event_producer_lambda.lambda_handler",
                code=_lambda.Code.from_asset("./lambda/"),
                architecture=_lambda.Architecture.ARM_64,  # type: ignore
                log_retention=logs.RetentionDays("TWO_WEEKS"),
                tracing=_lambda.Tracing.ACTIVE,
                layers=[powertools_layer],
            ),
            state_machine_props=stepfunctions.StateMachineProps(
                definition=definition, timeout=Duration.minutes(5)
            ),
        )

        # Define API Gateway REST API resource backed by producer lambda function

        api = apigw.LambdaRestApi(
            self,
            "SampleAPI to trigger Event Producer",
            description=" API Gateway REST API resource backed by producer lambda function",
            handler=event_producer_lambda.lambda_function,  # type: ignore
            proxy=False,
        )

        items = api.root.add_resource("items")
        items.add_method("POST")  # POST /items
