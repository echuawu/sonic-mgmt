import pytest
import allure
import os
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.ConfigTool import ConfigTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.constants.constants_nvos import SystemConsts, ConfigConsts, OutputFormat
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort


@pytest.mark.nvos_ci
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


@pytest.mark.general
def test_apply_assume(engines):
    """
        Test flow:
            1. run nv set system hostname <hostname> without apply
            2. run nv --assume-yes config apply
            3. verify output includes "applied"
            4. run nv config show
            5. verify the show command output includes set/system/hostname
            6. run nv unset system hostname without apply
            7. run nv --assume-no config apply
            8. verify output includes "Declined apply after warnings"
            9. run nv config diff
            10. verify the diff command output includes unset/system/hostname
            11. run nv -y config apply
    """
    system = System(None)
    new_hostname = 'TESTINGAPPLY'
    with allure.step('set system hostname to {hostname} - without apply'.format(
            hostname=new_hostname)):
        system.set(new_hostname, engines.dut, SystemConsts.HOSTNAME, False)

    with allure.step('apple system hostname change using {opt}'.format(opt=ConfigConsts.APPLY_ASSUME_YES)):
        apply_output = NvueGeneralCli.apply_config(engines.dut, False, ConfigConsts.APPLY_ASSUME_YES)
        assert 'applied' in apply_output, "failed to apply new system hostname"

    with allure.step('verify the show command output includes set/system/hostname'):
        show_after_apply = TestToolkit.GeneralApi[TestToolkit.tested_api].show_config(engines.dut)
        ConfigTool.verify_show_after_apply(show_after_apply, 'set', 'system/hostname', new_hostname).get_returned_value()

    with allure.step('unset system hostname - without apply'):
        system.unset(engines.dut, SystemConsts.HOSTNAME, False)

    with allure.step('apple system hostname change using {opt}'.format(opt=ConfigConsts.APPLY_ASSUME_NO)):
        apply_output = NvueGeneralCli.apply_config(engines.dut, False, ConfigConsts.APPLY_ASSUME_NO)
        assert 'Declined apply after warnings' in apply_output, "expected warning message wasn't found"

    with allure.step('verify output includes "Declined apply after warnings"'):
        diff_after_apply = TestToolkit.GeneralApi[TestToolkit.tested_api].diff_config(engines.dut)
        ConfigTool.verify_diff_after_config(diff_after_apply, 'unset', 'system/hostname').get_returned_value()

    with allure.step('apply system hostname change using {opt}'.format(opt=ConfigConsts.APPLY_YES)):
        NvueGeneralCli.apply_config(engines.dut, True, ConfigConsts.APPLY_YES)
