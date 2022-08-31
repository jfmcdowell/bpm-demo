from aws_cdk import Aspects, Duration, RemovalPolicy, Stack
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_logs as logs
from aws_cdk import aws_stepfunctions as stepfunctions
from aws_cdk import aws_stepfunctions_tasks as sftasks
from aws_solutions_constructs.aws_lambda_stepfunctions import LambdaToStepfunctions
from cdk_nag import AwsSolutionsChecks, NagSuppressions
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

        submit_price_appeal_lambda.apply_removal_policy(RemovalPolicy.DESTROY)

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

        status_lambda.apply_removal_policy(RemovalPolicy.DESTROY)

        # State machine definitons

        submit_price_appeal_step = sftasks.LambdaInvoke(
            self,
            "Submit Price Appeal",
            lambda_function=submit_price_appeal_lambda,  # type: ignore
            input_path="$",
            output_path="$.Payload",
        )

        wait_step = stepfunctions.Wait(
            self, "Wait 10 seconds", time=stepfunctions.WaitTime.duration(Duration.seconds(10))
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
                definition=definition,
                timeout=Duration.minutes(5),
                tracing_enabled=True,
            ),
        )

        event_producer_lambda.state_machine.apply_removal_policy(RemovalPolicy.DESTROY)
        event_producer_lambda.lambda_function.apply_removal_policy(RemovalPolicy.DESTROY)

        # IAM policy for Producer Lambda

        event_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW, resources=["*"], actions=["events:PutEvents"]
        )

        event_producer_lambda.lambda_function.add_to_role_policy(event_policy)

        # Define API Gateway REST API resource backed by producer lambda function

        access_log_group = logs.LogGroup(self, "BPMAccessLogs")
        access_log_group.apply_removal_policy(RemovalPolicy.DESTROY)

        api = apigw.LambdaRestApi(
            self,
            "SampleAPI to trigger Event Producer",
            description=" API Gateway REST API resource backed by producer lambda function",
            handler=event_producer_lambda.lambda_function,  # type: ignore
            proxy=False,
            deploy_options=apigw.StageOptions(
                access_log_destination=apigw.LogGroupLogDestination(access_log_group),
                access_log_format=apigw.AccessLogFormat.json_with_standard_fields(
                    caller=True,
                    http_method=True,
                    ip=True,
                    protocol=True,
                    request_time=True,
                    resource_path=True,
                    response_length=True,
                    status=True,
                    user=True,
                ),
                logging_level=apigw.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
            ),
        )

        api.apply_removal_policy(RemovalPolicy.DESTROY)

        request_validator = apigw.RequestValidator(
            self,
            "MyRequestValidator",
            rest_api=api,
        )
        request_validator.apply_removal_policy(RemovalPolicy.DESTROY)

        items = api.root.add_resource("items")
        items.add_method("POST")  # POST /items

        Aspects.of(self).add(AwsSolutionsChecks())
        NagSuppressions.add_stack_suppressions(
            self, [{"id": "AwsSolutions-IAM4", "reason": "TODO: Stop using AWS managed policies."}]
        )
        NagSuppressions.add_stack_suppressions(
            self, [{"id": "AwsSolutions-IAM5", "reason": "TODO: Remove Wildcards in IAM roles."}]
        )
        NagSuppressions.add_stack_suppressions(
            self, [{"id": "AwsSolutions-SF1", "reason": "TODO: Log all events in Cloudwatch."}]
        )
        NagSuppressions.add_stack_suppressions(
            self, [{"id": "AwsSolutions-APIG4", "reason": "Never going to implement this"}]
        )
        NagSuppressions.add_stack_suppressions(
            self, [{"id": "AwsSolutions-COG4", "reason": "Never going to implement this"}]
        )
