# T4-CICD Project

Project to build a CI/CD System.

# User Set Up Instruction for Using the Application

t4-cicd cli application requires the following external services:

- a MongoDB service,
- a Docker Engine service, and
- an AWS S3 Service (user must use their own AWS account)

## Setting up the Docker Engine Service

Install Docker Desktop from the [Official Website](https://www.docker.com/products/docker-desktop/). Docker Engine is included in the Docker Desktop installation. t4-cicd cli application will automatically use the Docker Engine running in your computer background.

## Setting up the MongoDB Service

You can use a local or remote MongoDB Service. You will need to save the URL to the MongoDB service
into a .env file in your project folder, or in your environment variable. Example below shows the
MONGO_DB_URL set up for local and remote MongoDB service.

```shell
# Local
export MONGO_DB_URL="mongodb://localhost:27017/"

# Remote, replace the <db_username>, <db_password> and <cluster_address>
export MONGO_DB_URL="mongodb+srv://<db_username>:<db_password>@<cluster_address>/"
```

Instructions for setting up local MongoDB service.
Download the MongoDB Community Server from
https://www.mongodb.com/try/download/community-kubernetes-operator

Follow the instructions for self-managed deployments
https://www.mongodb.com/docs/manual/administration/install-community/

To view the database, use MongoDB Compass (came together with MongoDB installation)

## Setting up the AWS S3 Service

S3 bucket names must be globally unique across all AWS accounts. In order for `Upload Artifact` feature to work, developer needs to specify a unique name in their configuration file `artifact_upload_path: "<UNIQUE_BUCKET_NAME>"`.

```yml
global:
  pipeline_name: "cicd_pipeline"
  docker: #...
  artifact_upload_path: <UNIQUE_BUCKET_NAME>
```

You need to copy and paste the following AWS credentials into ~/.aws/credentials file.
The credentials you provided must be able to create a bucket and upload into S3.

```shell
aws_access_key_id=<your_id>
aws_secret_access_key=<your_secret_access_key>
aws_session_token=<your_session_token> #if applicable
```

You also need to set up the target region in your .env file or set it as environment variable.

```shell
DEFAULT_S3_LOC=<AWS_REGION>
# example set to us-west-2
DEFAULT_S3_LOC='us-west-2'
```

## Installing the Program

You can install directly from pypi using pip. Recommendation is to install it under a virtual environment. See the section under Developer set up for how to activate a virtual environment.

```shell
pip install t4-cicd
```

## Basic Usage

You can run the program in a git repository you want to perform CICD action, or run the program in an empty directory and supply the repository information.

Note you will need a valid pipelines.yml file created in the .cicd-pipelines directory of your repository. Check [here](https://drive.google.com/file/d/1Mj3mnk20G5_Zj8X6bcFSnPRqY0stA-zu/view?usp=sharing) for the syntax required to write the yml file, check [here](https://drive.google.com/file/d/17vtjnLadMs-ItmI6e787_bvmH_j2YPVa/view?usp=sharing) for sample pipeline configuration.

List of the main commands you can run are as follow, use the --help flag to check for the details.

```shell
# Checking pipeline configuration file,
# only work within a git repository
cid config

# Setting up repository
cid config set-repo

# Getting repository info
cid config get-repo

# Override pipeline configuration value in Datastore (MongoDB)
# only work within a git repository
cid config override

# Running a pipeline run
cid pipeline run

# Retrieve pipeline report
cid pipeline report
```

## Errors and Debug Information

- When errors occur, the program stdout and stderr will give a brief summary of what went wrong.

- For error details to help in debugging, you can look for the debug.log file created.
  - By default a debug.log file will be created at a parent directory where your run the command
  - ie, if you run the command under directory `/temp/t4-cicd`, a debug.log will be at `/temp`

# Developer Set Up Instruction

First, follow the [User Set Up Instruction](#user-set-up-instruction-for-using-the-application) to set the Docker Engine service, MongoDB service and AWS S3 service.

## Installation Instruction from Project GitHub Folder

Reference for Poetry and Click [here](https://medium.com/@chinsj/develop-and-deploy-cli-tool-on-python-with-poetry-and-click-ab62f4341c45)

## Prerequisite:

0. Installed Python 3.12 from official [website](https://www.python.org/downloads/)
1. Installed pipx and poetry

```shell
# Install pipx
python -m pip install --user pipx
python -m pipx ensurepath

# Then go to your environment variable on windows/OS, check the path added and
# update lowercase to uppercase if necessary
# restart your window/OS.

# installation of poetry using pipx
pipx install poetry
```

2. Activated Virtual Environment

```shell
# navigate to the project directory
# First create your virtual environment using venv,
# Give it a name like myenv, if you use other name, add it to the .gitignore file
# venv come with standard python package
python -m venv myenv

# Activate your virtual environment. For bash terminal
source <your_venv_dir>/Scripts/activate

# Example when you name venv as myenv
# for Windows
source myenv/Scripts/activate
# for Mac / Unix
source myenv/bin/activate
```

The alternative way to activate the virtual environment is to run poetry shell.
This is less recommended as the downside of this approach is any command not starting with poetry
will run using your background environment package instead from the virtual environment.

```sh
poetry shell
```

## Installation, Lint & Test

```shell
# This will install all dependencies, and the project itself into your venv
poetry install

# Run pylint for src directory, --fail-under score to be 9.5
poetry run pylint ./src --fail-under=9.5

# Run pytest with coverage, note current passing coverage score is set at 50%
poetry run pytest

# Run pydoctor to generate the API documentation. This will generate a folder name 'apidocs/'
# in the repository.
# This required Administrative right. To link the file
poetry run pydoctor

# to test if you can run the command
poetry run cid --help
# or
cid --help
```

## Development - Managing Dependencies

[Reference](https://python-poetry.org/docs/managing-dependencies/#installing-group-dependencies) for dependencies management.

Remember to check the pyproject.toml file to ensure the dependency is added/removed

```shell
# Adding new dependency for general
poetry add <dependency/lib/package>

# Adding new dependency for development environment only
poetry add <dependency/lib/package> --group dev

# Remove dependencies
poetry remove <dependency/lib/package>
# Remove dependencies from development environment
poetry remove <dependency/lib/package> --group dev
```

## Development - Using Logging

### Steps:

- Use the `get_logger()` function from `util.common_utils`
- Provide arguments to change the logging level and/or directory
- By default a debug.log file will be created at a parent directory where your run the command, you can change its location.
  ie, if you run the command under directory `/temp/t4-cicd`, a debug.log will be at `/temp`

## Development - Other

Check out the list of documents under [dev-docs/design-docs](dev-docs/design-docs) folder for the following:
- CLI documentation
- Component Design
- Configuration File Docs
- Data Store Design
- High Level System Design
- Readme for Program Test
