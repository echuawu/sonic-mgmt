import logging
import pytest
import re

from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure
from ngts.tests.nightly.secure.constants import SonicSecureBootConsts

logger = logging.getLogger()
allure.logger = logger


@pytest.fixture(scope='session')
def mfa_file_name(chip_type):
    """
    Get the correct mfa file, it is different for different platform, currently there are following kinds of mfa files:
    fw-SPC.mfa, fw-SPC2.mfa, fw-SPC3.mfa, fw-SPC4.mfa, for example, ACS-SN5600 should use  fw-SPC4.mfa
    :param platform_params: platform_params fixture
    :return: The mfa file name on the running platform

    """
    yield f"fw-{chip_type}.mfa"


@pytest.fixture(scope='module', autouse=True)
def backup_original_mfa(engines, mfa_file_name):
    """
    Backup the original mfa file, and restore it once the test finish
    :param engines: engines
    :param mfa_file_name: original mfa file name
    """

    original_mfa_file = f"{SonicSecureBootConsts.MFA_FILE_PATH}/{mfa_file_name}"
    backup_mfa_file = f"{SonicSecureBootConsts.MFA_FILE_PATH}/bk_{mfa_file_name}"

    with allure.step("Backup the original mfa file"):
        engines.dut.run_cmd(f"sudo mv {original_mfa_file} {backup_mfa_file}")

    yield

    with allure.step("Restore the original mfa file"):
        engines.dut.run_cmd(f"sudo mv {backup_mfa_file} {original_mfa_file}")


def test_secure_corrupt_fw(engines, mfa_file_name, loganalyzer, dut_secure_type):
    """
    This test is to verify Err msg will be returned from the command and Err msg will be logged to the syslog file
    when using the fw upgrade command /usr/bin/mlnx-fw-upgrade.sh to upgrade a corrupt mfa file.
    :param engines: engines fixture
    :param mfa_file_name: the mfa file name
    :param loganalyzer: loganalyzer fixture
    """
    engine = engines.dut

    for dut in loganalyzer:
        loganalyzer[dut].expect_regex.extend([SonicSecureBootConsts.CORRUPT_MFA_ERR_MSG])

    if dut_secure_type == "prod":
        corrupt_mfa_file = SonicSecureBootConsts.PROD_CORRUPT_MFA_FILE
    else:
        corrupt_mfa_file = SonicSecureBootConsts.DEV_CORRUPT_MFA_FILE

    with allure.step("Copy the corrupt mfa file to the switch"):
        engine.copy_file(source_file=corrupt_mfa_file, dest_file=mfa_file_name, file_system="/tmp",
                         overwrite_file=True, verify_file=False)
        engine.run_cmd(f"sudo mv /tmp/{mfa_file_name} {SonicSecureBootConsts.MFA_FILE_PATH}")

    fw_upgrade_cmd = "sudo /usr/bin/mlnx-fw-upgrade.sh"
    output = engine.run_cmd(fw_upgrade_cmd)
    assert SonicSecureBootConsts.CORRUPT_MFA_ERR_MSG in output, \
        f"The expected err msg: '{SonicSecureBootConsts.CORRUPT_MFA_ERR_MSG}' not shown in the output"
