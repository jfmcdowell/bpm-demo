from aws_cdk import Environment

# Application constants to declare your cross account setup and
# any CI/CD stages

CDK_APP_NAME = "BPMDemo"
CDK_APP_PYTHON_VERSION = "3.10"

DEV_GITHUB_REPO = "jfmcdowell/bpm-demo"
DEV_GITHUB_BRANCH = "main"

DEV_ACCOUNT_ID = "586358791471"
DEV_REGION = "us-east-1"
DEV_ENV = Environment(account=DEV_ACCOUNT_ID, region=DEV_REGION)

PROD_ACCOUNT_ID = "123456789012"
PROD_REGION = "us-west-1"
PROD_ENV = Environment(account=PROD_ACCOUNT_ID, region=PROD_REGION)
