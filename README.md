
# Repo/Pipeline factory with boilerplate SAM project

This is an example of how to create a CodeCommit repo, CodePipeline pipeline with CodeBuild and CloudFormation deployment of a sample SAM project using CDK and Python. It creates a CodeCommit repo, pushes boilerplate code into it and sets up a CodePipeline job to deploy the code on commits to the `main` branch.

## Installation

First, install the AWS CDK by following the install steps [here](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html).

Then, clone this repo and `cd` into the project's root directory.

>This project is set up like a standard Python project.  The initialization process creates a virtualenv within this project, stored under the `.venv` directory.  To create the virtualenv it assumes that there is a `python3` (or `python` for Windows) executable in your path with access to the `venv` package. 

To create the virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the virtualenv is created, you can use the following step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

To deploy it to your account, make sure you have credentials available to the CLI, eg via AWS SSO:

```
aws sso login --profile yourprofile
```
or by using `aws configure` 

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth [--profile yourprofile]
```

To deploy it to your account, make sure you have credentials available to the CLI, then

```
$ cdk deploy [--profile yourprofile]
```

To deploy a particular config stanza from `parameters.properties`:
```
$ cdk deploy -c app=myapp -c env=dev [--profile yourprofile]
```
where the matching config stanza looks like
```
[myapp-dev]
awsRegion=ap-southeast-2
awsAccount=
appDesc=A description of this microservice
createGitUser=no
```

If not supplied, the AWS account and region will be taken from the environment variables `CDK_DEFAULT_REGION` and `CDK_DEFAULT_ACCOUNT`, which are created as part of the credential process.

## To run tests

Tests live in the `tests` directory. They use assertions to check for the presence of resources and their desired configurations.

```
$ pip install -r requirements-dev.txt
$ python -m pytest
```

## SAM Developer experience

Deploy the stack as above and give the repo cloning command to the developer (these are exported from the CloudFormation stack). The developer should update the SAM project and commit their changes. On commit to the `main` branch, the pipeline will run to deploy the SAM project.


## Other useful CDK commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation