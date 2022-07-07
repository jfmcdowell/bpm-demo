import aws_cdk as core
import aws_cdk.assertions as assertions

from bpm_demo.bpm_demo_stack import BpmDemoStack

# example tests. To run these tests, uncomment this file along with the example
# resource in bpm_demo/bpm_demo_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = BpmDemoStack(app, "bpm-demo")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
