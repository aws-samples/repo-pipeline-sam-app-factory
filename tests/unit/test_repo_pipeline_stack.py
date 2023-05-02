import aws_cdk as cdk
import aws_cdk.assertions as assertions
import configparser
import os

from stacks.repo_pipeline_stack import RepoPipelineStack


# example tests. To run these tests, uncomment this file along with the example
# resource in transport_nsw_lambda_factory/transport_nsw_lambda_factory_stack.py
def test_sqs_queue_created():
    config = configparser.ConfigParser()
    config.read("parameters.properties")
    app = cdk.App()
    params = {}
    params["environment"] = app.node.try_get_context("env") or config["default"]["env"]
    params["app_name"] = app.node.try_get_context("app") or config["default"]["app"]
    params["user"] = app.node.try_get_context("user") or config["default"]["user"]
    params["app_env"] = env_config = params["app_name"] + "-" + params["environment"]

    params["app_desc"] = config[env_config]["appDesc"]
    params["create_git_user"] = bool(config[env_config]["createGitUser"] == "yes")

    stack = RepoPipelineStack(app, "repo-pipeline-stack", params)
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::CodePipeline::Pipeline", {"RestartExecutionOnUpdate": True}
    )
