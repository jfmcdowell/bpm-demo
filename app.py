#!/usr/bin/env python3

from aws_cdk import App, Tags

import constants

# from bpm_demo.bpm_demo_stack import BpmDemoStack
from code_pipeline.pipeline_stack import PipelineStack

app = App()
PipelineStack(app, f"{constants.CDK_APP_NAME}-Pipeline", env=constants.DEV_ENV)

# BpmDemoStack(app, f"{constants.CDK_APP_NAME}-Pipeline", env=constants.DEV_ENV)

# Add Tags to all resources
Tags.of(app).add("Purpose", "bpm-demo")

app.synth()
