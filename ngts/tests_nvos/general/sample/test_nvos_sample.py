import logging
import allure
import pytest

from ngts.cli_wrappers.nvue.nvue_chassis_clis import NvueChassisCli

logger = logging.getLogger()


@pytest.mark.general
def test_nvos_show(engines):
    """
    Sample test for NVOS
    NOTE: currently using SONiC CLI
    """
    try:
        logger.info('Sample Test Started')

        with allure.step('Run: show_platform_summary'):
            show_com = NvueChassisCli.show_platform_summary(engines.dut)
            assert 'Platform: x86_64-mlnx_mqm' in show_com, "Command Failed"

        logger.info('Sample Test Completed')

    except Exception as err:
        raise AssertionError(err)
