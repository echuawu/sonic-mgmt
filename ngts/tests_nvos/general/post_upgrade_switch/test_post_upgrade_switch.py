from ngts.tests_nvos.general.post_upgrade_switch.constants import UPGRADE_STATUS_FILE_PATH, UPGRADE_STATUS_FAIL_PREFIX
from ngts.tools.test_utils import allure_utils as allure


def test_post_upgrade_switch(engines):
    """
    This test is to perform checks after the Install step of regression, such that if the checks fail, do not fail
        the entire regression
    """
    with allure.step('check upgrade with saved config status'):
        out = engines.dut.run_cmd(f'cat {UPGRADE_STATUS_FILE_PATH}')
        assert UPGRADE_STATUS_FAIL_PREFIX not in out, f'upgrade with saved config failed\n{out}'
