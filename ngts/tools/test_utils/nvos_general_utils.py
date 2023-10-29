import logging
from contextlib import contextmanager
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.constants.constants import LinuxConsts
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.authentication_restrictions.constants import RestrictionsConsts
from ngts.tests_nvos.system.clock.ClockConsts import ClockConsts


def set_base_configurations(dut_engine, timezone=LinuxConsts.JERUSALEM_TIMEZONE, apply=False, save_conf=False):
    """
    @summary: Set base configurations.
        Used in:
            - nvos post installation steps
            - nvos clear config (post test) function
    """
    logging.info('Set base configurations')
    orig_api = TestToolkit.tested_api

    try:
        logging.info('Change tested api to NVUE')
        TestToolkit.tested_api = ApiType.NVUE

        logging.info(f'Set switch timezone: {timezone}')
        system = System()
        system.set(ClockConsts.TIMEZONE, LinuxConsts.JERUSALEM_TIMEZONE, dut_engine=dut_engine).verify_result()

        logging.info('Set authentication restrictions configurations')
        system.aaa.authentication.restrictions.set(RestrictionsConsts.LOCKOUT_STATE,
                                                   RestrictionsConsts.DISABLED, dut_engine=dut_engine).verify_result()
        system.aaa.authentication.restrictions.set(RestrictionsConsts.FAIL_DELAY, 0,
                                                   dut_engine=dut_engine).verify_result()

        if apply:
            logging.info('Apply configurations')
            NvueGeneralCli.apply_config(engine=dut_engine, option='--assume-yes')

        if save_conf:
            logging.info('Save configurations')
            NvueGeneralCli.save_config(dut_engine)
    finally:
        logging.info(f'Change tested api back to {orig_api}')
        TestToolkit.tested_api = orig_api


@contextmanager
def loganalyzer_ignore(cond: bool = True):
    """
    @summary:
        Context manager that wraps code chunks with loganalyzer disabling at the beginning, and enabling in the end
    @param cond: boolean condition; log analyzer will be disabled for the code section only if cond is True (optional)
    """
    cond = False
    try:
        if cond:
            TestToolkit.start_code_section_loganalyzer_ignore()
        yield
    finally:
        if cond:
            TestToolkit.end_code_section_loganalyzer_ignore()
