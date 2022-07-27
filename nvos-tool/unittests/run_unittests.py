import shlex
import subprocess
import os
import sys


def run_command(cmd):
    res = subprocess.run(shlex.split(cmd))
    if res.returncode and res.returncode > 1:
        print("Command execution failed")
        exit(1)


def create_pytest_environment():
    print("Update working directory")
    os.chdir("nvos/src/nvue-app/nvue")

    print("Prepare the environment")
    subprocess.Popen(shlex.split("./startenv.sh"))

    print("Build the API")
    run_command("scripts/build_dist.sh nvos test")

    print("setting TEST_ENV=test")
    os.environ['TEST_ENV'] = "test"

    print("Apply configuration")
    run_command("touch env/lib/python3.7/site-packages/ruamel/__init__.py")
    run_command("sed -i 's/) as f/, encoding=\"utf8\") as f/g' env/lib/python3.7/site-packages/yamllint/cli.py")


def run_nvue_unittests():
    print("--- Run NVUE Unittests ---")

    print("Validate all the main specs (openapi.yaml files)")
    run_command("pytest -k test_verify_spec")

    print("Validate the python and yaml linting")
    run_command("pytest --pyargs cue -k test_static_analysis")

    print("--- Execution of NVUE Unittests is completed ---")


def main():
    create_pytest_environment()
    run_nvue_unittests()
    exit(0)


if __name__ == '__main__':
    sys.exit(main())
