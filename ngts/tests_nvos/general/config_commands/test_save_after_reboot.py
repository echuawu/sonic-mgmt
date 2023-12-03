import pytest
from ngts.tools.test_utils import allure_utils as allure
import logging
from ngts.nvos_tools.infra.Fae import Fae
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_constants.constants_nvos import SystemConsts, NvosConst
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort
from infra.tools.redmine.redmine_api import is_redmine_issue_active
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import IbInterfaceConsts
from ngts.nvos_constants.constants_nvos import FastRecoveryConsts
from ngts.tools.test_utils.allure_utils import step as allure_step


logger = logging.getLogger()


@pytest.mark.general
def test_save_reboot(engines, devices):
    """
        Test flow:
            1. run nv set system hostname <new_hostname> with apply
            2. Run 'nv set fae fast-recovery state disabled' and apply config
            3. run nv config save
            4. run nv set interface ib0 description <new_description> with apply
            5. Run 'nv set fae fast-recovery trigger credit-watchdog event warning' and apply config
            6. run nv action reboot system
            7. run nv show system after reload
            8. verify hostname is new_hostname
            9. Verify fae fast-recovery state is Disabled
            10. Run nv show interface ib0
            11. Verify the applied description value is ''
            12. Verify fae fast-recovery trigger event for trigger-id is Error
            13. cleanup - run nv unset system hostname & reboot
    """
    if devices.dut.ASIC_TYPE == 'Quantum' and is_redmine_issue_active([3292179]):
        pytest.skip("Test skipped due to an open bug: https://redmine.mellanox.com/issues/3292179")

    fae = Fae()

    with allure.step('Run show system command and verify that each field has a value'):
        logger.info('Run show system command and verify that each field has a value')
        system = System()
        old_hostname = OutputParsingTool.parse_json_str_to_dictionary(system.show()).get_returned_value()[SystemConsts.HOSTNAME]
        new_hostname_value = 'TestingConfigCmds'

        '''with allure_step('Run set fae fast-recovery state command to set to disable and apply config'):
            fae.fast_recovery.set(FastRecoveryConsts.STATE,
                                  FastRecoveryConsts.STATE_DISABLED, apply=True, dut_engine=engines.dut)'''

        with allure.step('set hostname to be {hostname} - with apply'.format(hostname=new_hostname_value)):
            logger.info('set hostname to be {hostname} - with apply'.format(hostname=new_hostname_value))
            system.set(SystemConsts.HOSTNAME, new_hostname_value, apply=True, ask_for_confirmation=True)
            TestToolkit.GeneralApi[TestToolkit.tested_api].save_config(engines.dut)

        try:
            ib0_port = MgmtPort('ib0')
            new_ib0_description = '"ib0description"'
            trigger_id = FastRecoveryConsts.TRIGGER_CREDIT_WATCHDOG

            with allure.step('set ib0 description to be {description} - with apply'.format(description=new_ib0_description)):
                logger.info('set ib0 description to be {description} - with apply'.format(description=new_ib0_description))
                ib0_port.interface.set(NvosConst.DESCRIPTION, new_ib0_description, apply=True).verify_result()

            '''with allure_step('Run set fae fast-recovery trigger trigger-id event command and apply config'):
                fae.fast_recovery.trigger.set(trigger_id + ' ' + FastRecoveryConsts.TRIGGER_EVENT,
                                              FastRecoveryConsts.SEVERITY_WARNING, apply=True,
                                              dut_engine=engines.dut).verify_result()'''

            with allure.step('Run nv action reboot system'):
                logger.info('Run nv action reboot system')
                system.reboot.action_reboot()

            with allure.step('verify the hostname is {hostname}'.format(hostname=new_hostname_value)):
                logger.info('verify the hostname is {hostname}'.format(hostname=new_hostname_value))
                system_output = OutputParsingTool.parse_json_str_to_dictionary(system.show()).get_returned_value()
                ValidationTool.verify_field_value_in_output(system_output, SystemConsts.HOSTNAME,
                                                            new_hostname_value).verify_result()

            '''with allure_step('Verify fae fast-recovery state is Disabled'):
                fast_recovery_output = OutputParsingTool.parse_json_str_to_dictionary(
                    fae.fast_recovery.show()).get_returned_value()
                ValidationTool.verify_field_value_in_output(fast_recovery_output, FastRecoveryConsts.STATE,
                                                            FastRecoveryConsts.STATE_DISABLED).verify_result()'''

            with allure.step('verify the ib0 description is empty'):
                logger.info('verify the ib0 description is empty')
                output_dictionary = OutputParsingTool.parse_show_interface_output_to_dictionary(
                    ib0_port.interface.show()).get_returned_value()
                assert IbInterfaceConsts.DESCRIPTION not in output_dictionary.keys(), \
                    "Expected not to have description field after unset command, but we still have this field."

        finally:
            with allure.step('Cleanup - set hostname to be {hostname} - with apply'.format(hostname=old_hostname)):
                logger.info('Cleanup - set hostname to be {hostname} - with apply'.format(hostname=old_hostname))
                system.unset(SystemConsts.HOSTNAME, apply=True, ask_for_confirmation=True)
                TestToolkit.GeneralApi[TestToolkit.tested_api].save_config(engines.dut)
                with allure.step('Run nv action reboot system'):
                    logger.info('Run nv action reboot system')
                    system.reboot.action_reboot()
