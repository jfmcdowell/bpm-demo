import constants
from aws_cdk import Stack
from aws_cdk import pipelines as pipelines
from constructs import Construct

import code_pipeline.pipeline_stage as stage


class PipelineStack(Stack):
    """DocString"""

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Pipeline code goes here

        codepipeline = pipelines.CodePipeline(
            self,
            "CodePipeline",
            docker_enabled_for_synth=True,
            synth=pipelines.ShellStep(
                "Synth",
                input=pipelines.CodePipelineSource.connection(  # Preferred Method
                    constants.DEV_GITHUB_REPO,
                    constants.DEV_GITHUB_BRANCH,
                    connection_arn="arn:aws:codestar-connections:us-east-1:586358791471:connection/1154d26b-d213-4052-b814-73548ef0ddb8",
                ),
                commands=[
                    "npm install -g aws-cdk && pip install -r requirements.txt",
                    "cdk synth",
                ],  # TODO add "pytest unittests"
            ),
        )

        # Add deployment stages for Development and Production accounts.
        development_stage = codepipeline.add_stage(
            stage.PipelineStage(
                self, f"{constants.CDK_APP_NAME}-Development", env=constants.DEV_ENV
            ),
        )
