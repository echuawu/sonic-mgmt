import logging
import allure
import pytest
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_constants.constants_nvos import SystemConsts
import time
logger = logging.getLogger()


@pytest.mark.system
@pytest.mark.simx
def test_system(engines, devices, topology_obj):
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
        system_output = OutputParsingTool.parse_json_str_to_dictionary(system.show()).get_returned_value()
        system_output.pop(SystemConsts.VERSION)
        ValidationTool.verify_all_fileds_value_exist_in_output_dictionary(
            system_output, system.get_expected_fields(devices.dut)).verify_result()

    with allure.step('Run set system hostname command and verify that hostname is updated'):
        new_hostname_value = "NOS-NVOS"
        hostname_default = SystemConsts.HOSTNAME_DEFAULT_VALUE
        dhcp_hostname = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific']['dhcp_hostname']
        output = OutputParsingTool.parse_json_str_to_dictionary(
            engines.dut.run_cmd("nv show interface eth0 ip dhcp-client -o json")).get_returned_value()
        dhcp_enabled = 'state' in output and output['state'] == "enabled"
        if dhcp_enabled:
            hostname_default = OutputParsingTool.parse_json_str_to_dictionary(system.show()).get_returned_value()[
                "hostname"]
            if dhcp_hostname:
                ValidationTool.verify_field_value_in_output(system_output, SystemConsts.HOSTNAME,
                                                            dhcp_hostname).verify_result()

        system.set(new_hostname_value, engines.dut, SystemConsts.HOSTNAME).verify_result()
        system_output = OutputParsingTool.parse_json_str_to_dictionary(system.show()).get_returned_value()
        ValidationTool.verify_field_value_in_output(system_output, SystemConsts.HOSTNAME,
                                                    new_hostname_value).verify_result()

    with allure.step('Run unset system hostname command and verify that hostname is updated'):
        system.unset(engines.dut, SystemConsts.HOSTNAME).verify_result()
        if dhcp_enabled:
            logging.info("Wait till the management interface will be reloaded to get a hostname from DHCP")
            time.sleep(20)
        system_output = OutputParsingTool.parse_json_str_to_dictionary(system.show()).get_returned_value()
        ValidationTool.verify_field_value_in_output(system_output, SystemConsts.HOSTNAME,
                                                    hostname_default if dhcp_enabled
                                                    else SystemConsts.HOSTNAME_DEFAULT_VALUE).verify_result()


@pytest.mark.system
@pytest.mark.simx
@pytest.mark.nvos_ci
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
    new_pre_login_msg = "Testing PRE LOGIN MESSAGE"
    new_post_login_msg = "Testing POST LOGIN MESSAGE"
    with allure.step('Run show system message command and verify that each field has a value'):
        system = System()
        message_output = OutputParsingTool.parse_json_str_to_dictionary(system.message.show()).get_returned_value()
        ValidationTool.verify_all_fileds_value_exist_in_output_dictionary(
            message_output, system.message.get_expected_fields(devices.dut)).verify_result()

    with allure.step('Run set system message pre-login command and verify that pre-login is updated'):
        ValidationTool.verify_field_value_in_output(message_output, SystemConsts.PRE_LOGIN_MESSAGE,
                                                    SystemConsts.PRE_LOGIN_MESSAGE_DEFAULT_VALUE).verify_result()
        system.message.set(new_pre_login_msg, engines.dut, SystemConsts.PRE_LOGIN_MESSAGE).verify_result()

        message_output = OutputParsingTool.parse_json_str_to_dictionary(system.message.show()).get_returned_value()
        ValidationTool.verify_field_value_in_output(message_output, SystemConsts.PRE_LOGIN_MESSAGE,
                                                    new_pre_login_msg).verify_result()

    with allure.step('Run set system message post-login command and verify that post-login is updated'):
        ValidationTool.verify_field_value_in_output(message_output, SystemConsts.POST_LOGIN_MESSAGE,
                                                    SystemConsts.POST_LOGIN_MESSAGE_DEFAULT_VALUE).verify_result()
        system.message.set(new_post_login_msg, engines.dut, SystemConsts.POST_LOGIN_MESSAGE).verify_result()
        message_output = OutputParsingTool.parse_json_str_to_dictionary(system.message.show()).get_returned_value()
        ValidationTool.verify_field_value_in_output(message_output, SystemConsts.POST_LOGIN_MESSAGE,
                                                    new_post_login_msg).verify_result()

    with allure.step('Run unset system message pre-login command and verify that pre-login is updated'):
        system.message.unset(engines.dut, SystemConsts.PRE_LOGIN_MESSAGE).verify_result()
        message_output = OutputParsingTool.parse_json_str_to_dictionary(system.message.show()).get_returned_value()
        ValidationTool.verify_field_value_in_output(message_output, SystemConsts.PRE_LOGIN_MESSAGE,
                                                    SystemConsts.PRE_LOGIN_MESSAGE_DEFAULT_VALUE).verify_result()
        logging.info("Verify the post-login was not affected")
        ValidationTool.verify_field_value_in_output(message_output, SystemConsts.POST_LOGIN_MESSAGE,
                                                    new_post_login_msg).verify_result()

    with allure.step('Run unset system message post-login command and verify that pre-login is updated'):
        system.message.unset(engines.dut, SystemConsts.POST_LOGIN_MESSAGE).verify_result()
        message_output = OutputParsingTool.parse_json_str_to_dictionary(system.message.show()).get_returned_value()
        ValidationTool.verify_field_value_in_output(message_output, SystemConsts.POST_LOGIN_MESSAGE,
                                                    SystemConsts.POST_LOGIN_MESSAGE_DEFAULT_VALUE).verify_result()


@pytest.mark.system
@pytest.mark.simx
@pytest.mark.nvos_ci
def test_show_system_version(engines, devices):
    """
    Run show system version command and verify version values
        Test flow
        1. run show system message
        2. validate values in db
    """
    with allure.step('Run show system command and verify that each field has a value'):
        system = System()
        version_output = OutputParsingTool.parse_json_str_to_dictionary(system.version.show()).get_returned_value()
        ValidationTool.verify_all_fileds_value_exist_in_output_dictionary(
            version_output, system.version.get_expected_fields(devices.dut)).verify_result()


@pytest.mark.system
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
        reboot_output = OutputParsingTool.parse_json_str_to_dictionary(system.reboot.show()).get_returned_value()
        assert reboot_output['reason'], "reason field is missing"
