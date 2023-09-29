# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import constructs
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_codebuild as codebuild,
    aws_codecommit as codecommit,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_s3 as s3,
    aws_iam as iam,
    aws_logs as logs,
)


class RepoPipelineStack(Stack):
    def __init__(
        self, scope: constructs.Construct, id: str, params: map, **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        repo_name = params["app_env"] + "-repo"

        # create the code repo we'll be using for the source stage
        boilerplate_code = "default-repo"
        if os.path.exists(os.path.join(os.curdir, "boilerplate", repo_name)):
            boilerplate_code = repo_name

        code_repo = codecommit.Repository(
            self,
            "Repository",
            repository_name=repo_name,
            description=params["app_desc"],
            code=codecommit.Code.from_directory(
                directory_path=os.path.join(os.curdir, "boilerplate", boilerplate_code),
                branch="main",
            ),
        )

        if params["create_git_user"]:
            # create a git user and attach least privileges inline policy
            git_user = iam.User(
                self, "GitIamUser", user_name=params["app_env"] + "-git-user"
            )
            policy_statement = iam.PolicyStatement(
                actions=["codecommit:GitPull", "codecommit:GitPush"],
                effect=iam.Effect.ALLOW,
                resources=[code_repo.repository_arn],
            )
            custom_policy_document = iam.PolicyDocument(statements=[policy_statement])

            git_policy = iam.Policy(self, "GitPolicy", document=custom_policy_document)
            git_user.attach_inline_policy(git_policy)

        # Create the artifacts bucket we'll use
        artifacts_bucket = s3.Bucket(
            self,
            "PipelineArtifactsBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # create the pipeline and tell it to use the artifacts bucket
        pipeline = codepipeline.Pipeline(
            self,
            "Pipeline-" + params["app_env"],
            artifact_bucket=artifacts_bucket,
            pipeline_name="pipeline-" + params["app_env"],
            cross_account_keys=True,
            restart_execution_on_update=True,
        )

        # create the source stage, which grabs the code from the repo and outputs it as an artifact
        source_output = codepipeline.Artifact()

        pipeline.add_stage(
            stage_name="Source",
            actions=[
                codepipeline_actions.CodeCommitSourceAction(
                    action_name="GetSource",
                    repository=codecommit.Repository.from_repository_name(
                        self, "Repo", repo_name
                    ),
                    output=source_output,
                    branch="main",
                )
            ],
        )

        # create the build stage which takes the source artifact and outputs the built artifact
        # to allow use of docker, need privileged flag to be set to True
        build_output = codepipeline.Artifact()
        build_project = codebuild.PipelineProject(
            self,
            "Build",
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml"),
            logging=codebuild.LoggingOptions(
                cloud_watch=codebuild.CloudWatchLoggingOptions(
                    enabled=True,
                    log_group=logs.LogGroup(
                        self,
                        "PipelineLogs",
                    ),
                )
            ),
            environment={
                "build_image": codebuild.LinuxBuildImage.AMAZON_LINUX_2_4,
                "privileged": True,
            },
            environment_variables={
                "PACKAGE_BUCKET": codebuild.BuildEnvironmentVariable(
                    value=artifacts_bucket.bucket_name
                ),
            },
        )
        pipeline.add_stage(
            stage_name="Build",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="Build",
                    project=build_project,
                    input=source_output,
                    outputs=[build_output],
                )
            ],
        )

        # create the deployment stages that take the built artifact and create a change set then deploy it

        ##########################################################
        # CLOUDFORMATION DEPLOYMENT
        ##########################################################

        stack_name = params["app_env"] + "-stack"

        pipeline.add_stage(
            stage_name="CreateChangeSet",
            actions=[
                codepipeline_actions.CloudFormationCreateReplaceChangeSetAction(
                    change_set_name=stack_name + "-changeset",
                    action_name="CreateChangeSet",
                    template_path=build_output.at_path("packaged.yaml"),
                    stack_name=stack_name,
                    cfn_capabilities=[
                        cdk.CfnCapabilities.NAMED_IAM,
                        cdk.CfnCapabilities.AUTO_EXPAND,
                    ],
                    admin_permissions=True,
                ),
            ],
        )

        pipeline.add_stage(
            stage_name="DeployChangeSet",
            actions=[
                codepipeline_actions.CloudFormationExecuteChangeSetAction(
                    change_set_name=stack_name + "-changeset",
                    stack_name=stack_name,
                    action_name="Deploy",
                ),
            ],
        )

        cdk.CfnOutput(
            self, "GitRepoCloneUrlSsh", value=code_repo.repository_clone_url_ssh
        )
        cdk.CfnOutput(
            self, "GitRepoCloneUrlHttp", value=code_repo.repository_clone_url_http
        )
        cdk.CfnOutput(
            self, "GitRepoCloneUrlGrc", value=code_repo.repository_clone_url_grc
        )

        if params["create_git_user"]:
            cdk.CfnOutput(self, "GitUser", value=git_user.user_name)
