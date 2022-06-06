import logging
import allure

from ngts.nvos_tools.general.system.System import *
from ngts.constants.constants_nvos import SystemConsts
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
logger = logging.getLogger()


def test_system(engines, devices):
    """
    Run show system message command and verify the required message
        Test flow:
            1. run show system message
            2. validate all fields have values
            3. set hostname to "Jaguar-NVOS"
            5. run show system message
            # 6. verify hostname appending value is "Jaguar-NVOS"
            7. run nv config apply
            8. verify hostname changed to "Jaguar-NVOS"
            9. run unset system hostname
            10. run nv config apply
            11. verify hostname changed to ""nvos"
    """
    with allure.step('Run show system command and verify that each field has a value'):
        system = System()
        system.update_output_dictionary(engines.dut)
        ValidationTool.verify_all_fileds_value_exist_in_output_dictionary(
            system.output_dictionary, system.get_expected_fields(devices.dut)).verify_result()

    with allure.step('Run set system hostname command and verify that hostname is updated'):
        new_hostname_value = "NOS-NVOS"
        ValidationTool.verify_field_value_in_output(system.output_dictionary, SystemConsts.HOSTNAME,
                                                    SystemConsts.HOSTNAME_DEFAULT_VALUE).verify_result()
        system.set(new_hostname_value, engines.dut, SystemConsts.HOSTNAME)
        system.update_output_dictionary(engines.dut)
        ValidationTool.verify_field_value_in_output(system.output_dictionary, SystemConsts.HOSTNAME,
                                                    new_hostname_value).verify_result()

    with allure.step('Run unset system hostname command and verify that hostname is updated'):
        system.unset(engines.dut, SystemConsts.HOSTNAME)
        system.update_output_dictionary(engines.dut)
        ValidationTool.verify_field_value_in_output(system.output_dictionary, SystemConsts.HOSTNAME,
                                                    SystemConsts.HOSTNAME_DEFAULT_VALUE).verify_result()


def test_system_message(engines, devices):
    """
    Run show/set/unset system message command and verify the required message
        Test flow:
            1. run show system message
            2. validate all fields have values
            3. set pre-login message[run cmd + apply conf]
            5. run show system message
            6. verify pre-login changed to "NVOS-TESTING"
            7. set post-login message[run cmd + apply conf]
            8. run show system message
            9. verify post-login changed to "NVOS-TESTING"
            10. unset post-login message[run cmd + apply conf]
            11. run show system message
            12. verify post-login changed to default value
            10. unset pre-login message[run cmd + apply conf]
            11. run show system message
            12. verify pre-login changed to default value
    """
    with allure.step('Run show system message command and verify that each field has a value'):
        system = System()
        system.message.update_output_dictionary(engines.dut)
        ValidationTool.verify_all_fileds_value_exist_in_output_dictionary(
            system.message.output_dictionary, system.message.get_expected_fields(devices.dut)).verify_result()

    with allure.step('Run set system message pre-login command and verify that pre-login is updated'):
        ValidationTool.verify_field_value_in_output(system.message.output_dictionary, SystemConsts.PRE_LOGIN_MESSAGE,
                                                    SystemConsts.PRE_LOGIN_MESSAGE_DEFAULT_VALUE).verify_result()
        system.message.set('"Testing PRE LOGIN MESSAGE"', engines.dut, SystemConsts.PRE_LOGIN_MESSAGE)
        system.message.update_output_dictionary(engines.dut)
        ValidationTool.verify_field_value_in_output(system.message.output_dictionary, SystemConsts.PRE_LOGIN_MESSAGE,
                                                    "Testing PRE LOGIN MESSAGE").verify_result()

    with allure.step('Run set system message post-login command and verify that post-login is updated'):
        ValidationTool.verify_field_value_in_output(system.message.output_dictionary, SystemConsts.POST_LOGIN_MESSAGE,
                                                    SystemConsts.POST_LOGIN_MESSAGE_DEFAULT_VALUE).verify_result()
        system.message.set('"Testing POST LOGIN MESSAGE"', engines.dut, SystemConsts.POST_LOGIN_MESSAGE)
        system.message.update_output_dictionary(engines.dut)
        ValidationTool.verify_field_value_in_output(system.message.output_dictionary, SystemConsts.POST_LOGIN_MESSAGE,
                                                    "Testing POST LOGIN MESSAGE").verify_result()

    with allure.step('Run unset system message pre-login command and verify that pre-login is updated'):
        system.message.unset(engines.dut, SystemConsts.PRE_LOGIN_MESSAGE)
        system.message.update_output_dictionary(engines.dut)
        ValidationTool.verify_field_value_in_output(system.message.output_dictionary, SystemConsts.PRE_LOGIN_MESSAGE,
                                                    SystemConsts.PRE_LOGIN_MESSAGE_DEFAULT_VALUE).verify_result()

    with allure.step('Run unset system message post-login command and verify that pre-login is updated'):
        system.message.unset(engines.dut, SystemConsts.POST_LOGIN_MESSAGE)
        system.message.update_output_dictionary(engines.dut)
        ValidationTool.verify_field_value_in_output(system.message.output_dictionary, SystemConsts.POST_LOGIN_MESSAGE,
                                                    SystemConsts.POST_LOGIN_MESSAGE_DEFAULT_VALUE).verify_result()


def test_show_system_version(engines, devices):
    """
    Run show system version command and verify version values
        Test flow
        1. run show system message
        2. validate values in db
    """
    with allure.step('Run show system command and verify that each field has a value'):
        system = System()
        system.version.update_output_dictionary(engines.dut)
        ValidationTool.verify_all_fileds_value_exist_in_output_dictionary(
            system.version.output_dictionary, system.version.get_expected_fields(devices.dut)).verify_result()


def test_show_system_reboot(engines, devices):
    """
    Run show system reboot command and verify the reboot history and reason values
        Test flow:
            1. run show system reboot
            2. validate all fields have values
            3. reboot the switch
            5. run show system message
            6. validate all fields have the new values
    """
    with allure.step('Run show system reboot command and verify that each field has a value'):
        system = System()
        system.reboot.update_output_dictionary(engines.dut)
        ValidationTool.verify_all_fileds_value_exist_in_output_dictionary(
            system.reboot.output_dictionary, system.reboot.get_expected_fields(devices.dut)).verify_result()


def test_show_system_config():
    """
    Run show system config command
    Test flow:

    """
    pass
