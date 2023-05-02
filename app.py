#!/usr/bin/env python3
import os
import configparser

import aws_cdk as cdk
from aws_cdk import Aspects

from stacks.repo_pipeline_stack import RepoPipelineStack


config = configparser.ConfigParser()
config.read("parameters.properties")

app = cdk.App()

params = {}
params["environment"] = app.node.try_get_context("env") or config["default"]["env"]
params["app_name"] = app.node.try_get_context("app") or config["default"]["app"]
params["user"] = app.node.try_get_context("user") or config["default"]["user"]
params["app_env"] = env_config = params["app_name"] + "-" + params["environment"]

params["aws_region"] = (
    config[env_config]["awsRegion"] or os.environ["CDK_DEFAULT_REGION"]
)
params["aws_account"] = (
    config[env_config]["awsAccount"] or os.environ["CDK_DEFAULT_ACCOUNT"]
)
params["app_desc"] = config[env_config]["appDesc"]
params["create_git_user"] = bool(config[env_config]["createGitUser"] == "yes")

deploy_environment = cdk.Environment(
    account=params["aws_account"], region=params["aws_region"]
)

RepoPipelineStack(
    app,
    "RepoPipelineStack",
    params=params,
    env=deploy_environment,
)

if params["app_name"]:
    Aspects.of(app).add(cdk.Tag("app-name", params["app_name"]))

if params["environment"]:
    Aspects.of(app).add(cdk.Tag("environment", params["environment"]))

Aspects.of(app).add(cdk.Tag("created-by", params["user"]))

app.synth()
