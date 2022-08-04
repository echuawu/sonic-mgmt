import pytest
import allure
import os
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.constants.constants_nvos import SystemConsts, ConfigConsts, OutputFormat
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort


def test_detach(engines):
    """
        Test flow:
            1. run nv set system hostname <new_hostname>
            2. run nv config detach
            3. run nv config diff save as diff_output
            4. verify diff_output is empty
        """
    with allure.step('Run show system command and verify that each field has a value'):
        system = System()
        new_hostname_value = 'TestingConfigCmds'
        with allure.step('set hostname to be {hostname} - without apply'.format(hostname=new_hostname_value)):
            system.set(new_hostname_value, engines.dut, SystemConsts.HOSTNAME, False)

            TestToolkit.GeneralApi[TestToolkit.tested_api].detach_config(engines.dut)

        diff_output = OutputParsingTool.parse_json_str_to_dictionary(
            NvueGeneralCli.diff_config(engines.dut)).get_returned_value()

        with allure.step('verify the pending list is empty'):
            assert diff_output == {}, "pending revision should be empty, detach command should clean the last revision"
