from aws_cdk import Stage, Tags
from bpm_demo.bpm_demo_stack import BpmDemoStack
from constructs import Construct


class PipelineStage(Stage):
    """DocString"""

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        stack = BpmDemoStack(self, "Pipeline")

        Tags.of(stack).add("Purpose", "bpm-demo")
