import pytest
import allure
import os
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.ConfigTool import ConfigTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_constants.constants_nvos import SystemConsts, ConfigConsts, OutputFormat
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort


@pytest.mark.general
def test_save_reboot(engines):
    """
        Test flow:
            1. run nv set system hostname <new_hostname> with apply
            2. run nv config save
            3. run nv set interface ib0 description <new_description> with apply
            4. run nv action reboot system
            5. run nv show system after reload
            6. verify hostname is new_hostname
            7. run nv show interface ib0
            8. verify the applied description value is ''
            9. run nv unset system hostname
        """
    with allure.step('Run show system command and verify that each field has a value'):
        system = System()
        new_hostname_value = 'TestingConfigCmds'
        with allure.step('set hostname to be {hostname} - with apply'.format(hostname=new_hostname_value)):
            system.set(new_hostname_value, engines.dut, SystemConsts.HOSTNAME)

            TestToolkit.GeneralApi[TestToolkit.tested_api].save_config(engines.dut)

        ib0_port = MgmtPort('ib0')
        new_ib0_description = '"ib0description"'
        with allure.step('set ib0 description to be {description} - with apply'.format(
                description=new_ib0_description)):
            ib0_port.interface.description.set(value=new_ib0_description, apply=False).verify_result()

        with allure.step('Run nv action reboot system'):
            system.reboot.action_reboot()

        with allure.step('verify the hostname is {hostname}'.format(hostname=new_hostname_value)):
            system_output = OutputParsingTool.parse_json_str_to_dictionary(system.show()).get_returned_value()
            ValidationTool.verify_field_value_in_output(system_output, SystemConsts.HOSTNAME,
                                                        new_hostname_value).verify_result()

            output_dictionary = OutputParsingTool.parse_show_interface_output_to_dictionary(
                ib0_port.show()).get_returned_value()

            ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                        field_name=ib0_port.interface.description.label,
                                                        expected_value='').verify_result()
