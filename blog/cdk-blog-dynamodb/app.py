
from aws_cdk import core

from cdk_blog_dynamodb.cdk_blog_dynamodb_stack import CdkBlogDynamodbStack

env_CA = core.Environment(region="ca-central-1")
env_US_Gov = core.Environment(region="us-gov-east-1")

app = core.App()

CdkBlogDynamodbStack(app, "cdk-blog-dynamodb", env=env_US_Gov)

app.synth()
