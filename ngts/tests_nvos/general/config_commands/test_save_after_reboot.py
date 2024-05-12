import pytest
import time

from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.tools.test_utils import allure_utils as allure
import logging
from ngts.nvos_tools.infra.Fae import Fae
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_constants.constants_nvos import SystemConsts, NvosConst, ApiType
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort
from infra.tools.redmine.redmine_api import is_redmine_issue_active
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import IbInterfaceConsts
from ngts.nvos_constants.constants_nvos import FastRecoveryConsts

logger = logging.getLogger()


@pytest.mark.general
def test_save_reboot(engines, devices):
    """
        Test flow:
            1. run nv set system hostname <new_hostname> with apply
            2. Run 'nv set fae fast-recovery state disabled' and apply config
            3. run nv config save
            4. run nv set interface eth0 description <new_description> with apply
            5. Run 'nv set fae fast-recovery trigger credit-watchdog event warning' and apply config
            6. run nv action reboot system
            7. run nv show system after reload
            8. verify hostname is new_hostname
            9. Verify fae fast-recovery state is Disabled
            10. Run nv show interface eth0
            11. Verify the applied description value is ''
            12. Verify fae fast-recovery trigger event for trigger-id is Error
            13. cleanup - run nv unset system hostname & reboot
    """
    fae = Fae()

    with allure.step('Run show system command and verify that each field has a value'):
        system = System()
        sys_info = OutputParsingTool.parse_json_str_to_dictionary(system.show()).get_returned_value()
        old_hostname = sys_info[SystemConsts.HOSTNAME]
        new_hostname_value = 'TestingConfigCmds'

        # TODO: Fix fae recovery
        '''with allure_step('Run set fae fast-recovery state command to set to disable and apply config'):
            fae.fast_recovery.set(FastRecoveryConsts.STATE,
                                  FastRecoveryConsts.STATE_DISABLED, apply=True, dut_engine=engines.dut)'''

        with allure.step('Set system events table-size to 600 and validate'):
            fae.system.events.set(op_param_name='table-size', op_param_value=600, apply=True, dut_engine=engines.dut).\
                verify_result()
            output = OutputParsingTool.parse_json_str_to_dictionary(fae.system.events.show()).get_returned_value()
            ValidationTool.verify_field_value_in_output(output, SystemConsts.EVENTS_TABLE_SIZE, '600').verify_result()

        with allure.step('Simulate 10 system events'):
            output = engines.dut.run_cmd('docker exec eventd events_publish_test.py -c 10')
            assert output == '', 'Error in executing simulate command: {}'.format(output)
            time.sleep(10)

        with allure.step('Extract last system event to verify post reboot'):
            output = OutputParsingTool.parse_json_str_to_dictionary(system.events.show('last 1')).get_returned_value()
            event_time = output[str(list(output.keys())[0])]["time-created"]

        with allure.step('set hostname to be {hostname} - with apply'.format(hostname=new_hostname_value)):
            system.set(SystemConsts.HOSTNAME, new_hostname_value, apply=True, ask_for_confirmation=True)
            TestToolkit.GeneralApi[TestToolkit.tested_api].save_config(engines.dut)

        try:
            eth0_port = MgmtPort('eth0')
            new_eth0_description = 'eth0_test_desc'
            trigger_id = FastRecoveryConsts.TRIGGER_CREDIT_WATCHDOG

            with allure.step(
                    'set eth0 description to be {description} - with apply'.format(description=new_eth0_description)):
                eth0_port.interface.set(NvosConst.DESCRIPTION, new_eth0_description, apply=True).verify_result()

            # TODO: Fix fae recovery
            '''with allure_step('Run set fae fast-recovery trigger trigger-id event command and apply config'):
                fae.fast_recovery.trigger.set(trigger_id + ' ' + FastRecoveryConsts.TRIGGER_EVENT,
                                              FastRecoveryConsts.SEVERITY_WARNING, apply=True,
                                              dut_engine=engines.dut).verify_result()'''

            with allure.step('Run nv action reboot system'):
                system.reboot.action_reboot()

            with allure.step('verify the hostname is {hostname}'.format(hostname=new_hostname_value)):
                system_output = OutputParsingTool.parse_json_str_to_dictionary(system.show()).get_returned_value()
                ValidationTool.verify_field_value_in_output(system_output, SystemConsts.HOSTNAME,
                                                            new_hostname_value).verify_result()

            with allure.step('Verify that system events table-size config was saved'):
                output = OutputParsingTool.parse_json_str_to_dictionary(fae.system.events.show()).get_returned_value()
                ValidationTool.verify_field_value_in_output(output, SystemConsts.EVENTS_TABLE_SIZE, '600').\
                    verify_result()

            with allure.step('Verify that the system event before the reboot is present post reboot as well'):
                output = system.events.show('last 10000')
                assert event_time in output, 'Event {} removed from system events table post reboot'.format(event_time)

            # TODO: Fix fae recovery
            '''with allure_step('Verify fae fast-recovery state is Disabled'):
                fast_recovery_output = OutputParsingTool.parse_json_str_to_dictionary(
                    fae.fast_recovery.show()).get_returned_value()
                ValidationTool.verify_field_value_in_output(fast_recovery_output, FastRecoveryConsts.STATE,
                                                            FastRecoveryConsts.STATE_DISABLED).verify_result()'''

            with allure.step('verify the eth0 description was not saved after reboot'):
                output_dictionary = OutputParsingTool.parse_show_interface_output_to_dictionary(
                    eth0_port.interface.show()).get_returned_value()
                assert IbInterfaceConsts.DESCRIPTION not in output_dictionary.keys() or \
                    output_dictionary[IbInterfaceConsts.DESCRIPTION] != new_eth0_description, \
                    "Description should not be saved after reboot"

        finally:
            with allure.step('Cleanup - set hostname to be {hostname} - with apply'.format(hostname=old_hostname)):
                system.unset(SystemConsts.HOSTNAME, apply=True, ask_for_confirmation=True)
                TestToolkit.GeneralApi[TestToolkit.tested_api].save_config(engines.dut)
                with allure.step('Run nv action reboot system'):
                    system.reboot.action_reboot()


@pytest.mark.cumulus
@pytest.mark.simx
@pytest.mark.general
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_general_auto_save(engines, devices, test_api):

    system = System()
    eth0_port = MgmtPort('eth0')
    new_eth0_description = 'TestingAutoSave'

    try:
        with allure.step('verify nv show system config auto-save enable is off'):
            output = OutputParsingTool.parse_json_str_to_dictionary(system.config.auto_save.show()).verify_result()
            assert SystemConsts.AUTO_SAVE_ENABLE_OFF == output[SystemConsts.AUTO_SAVE_ENABLE], "auto-save should be off"

        with allure.step('run nv set system config auto-save enable on'):
            system.config.auto_save.set(op_param_name=SystemConsts.AUTO_SAVE_ENABLE,
                                        op_param_value=SystemConsts.AUTO_SAVE_ENABLE_ON).verify_result()

        with allure.step('set eth0 description to be {description} - with apply'.format(description=new_eth0_description)):
            eth0_port.interface.set(NvosConst.DESCRIPTION, new_eth0_description, apply=True).verify_result()

        assert new_eth0_description in TestToolkit.GeneralApi[test_api].show_config(engine=engines.dut, revision='startup'), \
            "Expected to have new description field after set command, but we do not have it."

    finally:

        with allure.step("Unset description and verify"):
            eth0_port.interface.unset(op_param='description').verify_result()

        with allure.step('run nv set system config auto-save enable off'):
            system.config.auto_save.unset(op_param=SystemConsts.AUTO_SAVE_ENABLE, apply=True).verify_result()

        with allure.step('verify nv show system config auto-save enable is off'):
            output = OutputParsingTool.parse_json_str_to_dictionary(system.config.auto_save.show()).verify_result()
            assert SystemConsts.AUTO_SAVE_ENABLE_OFF == output[SystemConsts.AUTO_SAVE_ENABLE], "auto-save should be off"

            TestToolkit.GeneralApi[test_api].save_config(engine=engines.dut)
