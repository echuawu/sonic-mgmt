import pytest
import allure
import logging
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_constants.constants_nvos import SystemConsts, NvosConst
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort
from infra.tools.redmine.redmine_api import is_redmine_issue_active

logger = logging.getLogger()


@pytest.mark.general
def test_save_reboot(engines, devices):
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
            9. cleanup - run nv unset system hostname & reboot
        """
    if devices.dut.ASIC_TYPE == 'Quantum' and is_redmine_issue_active([3292179]):
        pytest.skip("Test skipped due to an open bug: https://redmine.mellanox.com/issues/3292179")

    with allure.step('Run show system command and verify that each field has a value'):
        logger.info('Run show system command and verify that each field has a value')
        system = System()
        old_hostname = OutputParsingTool.parse_json_str_to_dictionary(system.show()).get_returned_value()[SystemConsts.HOSTNAME]
        new_hostname_value = 'TestingConfigCmds'
        with allure.step('set hostname to be {hostname} - with apply'.format(hostname=new_hostname_value)):
            logger.info('set hostname to be {hostname} - with apply'.format(hostname=new_hostname_value))
            system.set(SystemConsts.HOSTNAME, new_hostname_value, apply=True, ask_for_confirmation=True)
            TestToolkit.GeneralApi[TestToolkit.tested_api].save_config(engines.dut)

        try:
            ib0_port = MgmtPort('ib0')
            new_ib0_description = '"ib0description"'
            with allure.step('set ib0 description to be {description} - with apply'.format(description=new_ib0_description)):
                logger.info('set ib0 description to be {description} - with apply'.format(description=new_ib0_description))
                ib0_port.interface.set(NvosConst.DESCRIPTION, new_ib0_description, apply=True).verify_result()

            with allure.step('Run nv action reboot system'):
                logger.info('Run nv action reboot system')
                system.reboot.action_reboot()

            with allure.step('verify the hostname is {hostname}'.format(hostname=new_hostname_value)):
                logger.info('verify the hostname is {hostname}'.format(hostname=new_hostname_value))
                system_output = OutputParsingTool.parse_json_str_to_dictionary(system.show()).get_returned_value()
                ValidationTool.verify_field_value_in_output(system_output, SystemConsts.HOSTNAME,
                                                            new_hostname_value).verify_result()

            with allure.step('verify the ib0 description is empty'):
                logger.info('verify the ib0 description is empty')
                output_dictionary = OutputParsingTool.parse_show_interface_output_to_dictionary(
                    ib0_port.interface.show()).get_returned_value()
                ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                            field_name=NvosConst.DESCRIPTION,
                                                            expected_value='').verify_result()
        finally:
            with allure.step('Cleanup - set hostname to be {hostname} - with apply'.format(hostname=old_hostname)):
                logger.info('Cleanup - set hostname to be {hostname} - with apply'.format(hostname=old_hostname))
                system.unset(SystemConsts.HOSTNAME, apply=True, ask_for_confirmation=True)
                TestToolkit.GeneralApi[TestToolkit.tested_api].save_config(engines.dut)
                with allure.step('Run nv action reboot system'):
                    logger.info('Run nv action reboot system')
                    system.reboot.action_reboot()
