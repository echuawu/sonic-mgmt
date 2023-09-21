import logging
import pytest
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.cli_coverage.operation_time import OperationTime

import time
logger = logging.getLogger()


@pytest.mark.system
@pytest.mark.simx
@pytest.mark.nvos_chipsim_ci
def test_system(engines, devices, topology_obj, test_name):
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
        ValidationTool.verify_all_fields_value_exist_in_output_dictionary(
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

        OperationTime.save_duration('set hostname', '', test_name, system.set, SystemConsts.HOSTNAME, new_hostname_value,
                                    apply=True, ask_for_confirmation=True).verify_result()
        time.sleep(3)
        system_output = OutputParsingTool.parse_json_str_to_dictionary(system.show()).get_returned_value()
        ValidationTool.verify_field_value_in_output(system_output, SystemConsts.HOSTNAME,
                                                    new_hostname_value).verify_result()

    with allure.step('Run unset system hostname command and verify that hostname is updated'):
        system.unset(SystemConsts.HOSTNAME, apply=True, ask_for_confirmation=True).verify_result()
        if dhcp_enabled:
            logging.info("Wait till the management interface will be reloaded to get a hostname from DHCP")
            time.sleep(20)
        system_output = OutputParsingTool.parse_json_str_to_dictionary(system.show()).get_returned_value()
        time.sleep(3)
        ValidationTool.verify_field_value_in_output(system_output, SystemConsts.HOSTNAME,
                                                    hostname_default if dhcp_enabled
                                                    else SystemConsts.HOSTNAME_DEFAULT_VALUE).verify_result()


@pytest.mark.system
@pytest.mark.simx
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
    system = System()

    with allure.step('Run set system message pre-login command and verify that pre-login is updated'):
        message_output = OutputParsingTool.parse_json_str_to_dictionary(system.message.show()).get_returned_value()
        ValidationTool.verify_field_value_in_output(message_output, SystemConsts.PRE_LOGIN_MESSAGE,
                                                    SystemConsts.PRE_LOGIN_MESSAGE_DEFAULT_VALUE).verify_result()
        system.message.set(new_pre_login_msg, engines.dut, SystemConsts.PRE_LOGIN_MESSAGE).verify_result()
        time.sleep(3)
        message_output = OutputParsingTool.parse_json_str_to_dictionary(system.message.show()).get_returned_value()
        ValidationTool.verify_field_value_in_output(message_output, SystemConsts.PRE_LOGIN_MESSAGE,
                                                    new_pre_login_msg).verify_result()

    with allure.step('Run set system message post-login command and verify that post-login is updated'):
        message_output = OutputParsingTool.parse_json_str_to_dictionary(system.message.show()).get_returned_value()
        ValidationTool.verify_field_value_in_output(message_output, SystemConsts.POST_LOGIN_MESSAGE,
                                                    SystemConsts.POST_LOGIN_MESSAGE_DEFAULT_VALUE).verify_result()
        system.message.set(new_post_login_msg, engines.dut, SystemConsts.POST_LOGIN_MESSAGE).verify_result()
        time.sleep(3)
        message_output = OutputParsingTool.parse_json_str_to_dictionary(system.message.show()).get_returned_value()
        ValidationTool.verify_field_value_in_output(message_output, SystemConsts.POST_LOGIN_MESSAGE,
                                                    new_post_login_msg).verify_result()

    with allure.step('Run unset system message pre-login command and verify that pre-login is updated'):
        system.message.unset(engines.dut, SystemConsts.PRE_LOGIN_MESSAGE).verify_result()
        time.sleep(3)
        message_output = OutputParsingTool.parse_json_str_to_dictionary(system.message.show()).get_returned_value()
        ValidationTool.verify_field_value_in_output(message_output, SystemConsts.PRE_LOGIN_MESSAGE,
                                                    SystemConsts.PRE_LOGIN_MESSAGE_DEFAULT_VALUE).verify_result()
        logging.info("Verify the post-login was not affected")
        ValidationTool.verify_field_value_in_output(message_output, SystemConsts.POST_LOGIN_MESSAGE,
                                                    new_post_login_msg).verify_result()

    with allure.step('Run unset system message post-login command and verify that pre-login is updated'):
        system.message.unset(engines.dut, SystemConsts.POST_LOGIN_MESSAGE).verify_result()
        time.sleep(3)
        message_output = OutputParsingTool.parse_json_str_to_dictionary(system.message.show()).get_returned_value()
        ValidationTool.verify_field_value_in_output(message_output, SystemConsts.POST_LOGIN_MESSAGE,
                                                    SystemConsts.POST_LOGIN_MESSAGE_DEFAULT_VALUE).verify_result()


@pytest.mark.system
@pytest.mark.simx
@pytest.mark.nvos_ci
@pytest.mark.nvos_chipsim_ci
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
        ValidationTool.verify_all_fields_value_exist_in_output_dictionary(
            version_output, system.version.get_expected_fields(devices.dut)).verify_result()


@pytest.mark.system
@pytest.mark.cumulus
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


@pytest.mark.system
@pytest.mark.simx
def test_show_system_memory(engines, devices):
    """
    Run show system memory and verify there is a correlation between the different values,
    and the values are in appropriate range.
        Test flow:
            1. run show system memory
            2. verify both keys (Physical and Swap) are exist
            3. validate total value = (free + used) values and greater than 0
            4. validate Utilization percentages are not reaching 60% for both Physical and Swap types (physical > 0)
            5. validate utilization value = (used / total) * 100, for both Physical and Swap types
    """
    with allure.step('Run show system memory command and verify that each field has a value'):
        system = System()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(system.show("memory")).get_returned_value()

        assert len(output_dictionary.keys()) == 2, "Unexpected Number of keys"
        assert list(output_dictionary.keys())[0] == SystemConsts.MEMORY_PHYSICAL_KEY, "Unexpected Key value"
        assert list(output_dictionary.keys())[1] == SystemConsts.MEMORY_SWAP_KEY, "Unexpected Key value"

        total_sum = output_dictionary[SystemConsts.MEMORY_PHYSICAL_KEY]["free"] + \
            output_dictionary[SystemConsts.MEMORY_PHYSICAL_KEY]["used"]

        assert 0 < output_dictionary[SystemConsts.MEMORY_PHYSICAL_KEY]["total"] == total_sum, \
            "Total number of bytes must be equal to calculated total sum and greater than 0"

        utilization = output_dictionary[SystemConsts.MEMORY_PHYSICAL_KEY]["utilization"]
        utilization_calc = (output_dictionary[SystemConsts.MEMORY_PHYSICAL_KEY]["used"] /
                            output_dictionary[SystemConsts.MEMORY_PHYSICAL_KEY]["total"]) * 100
        assert SystemConsts.MEMORY_PERCENT_THRESH_MIN < utilization < SystemConsts.MEMORY_PERCENT_THRESH_MAX, \
            "Physical utilization percentage is out of range"
        assert abs(utilization - utilization_calc) < 0.000001, \
            f"Mismatch between Physical utilization: {utilization}% to calculated utilization: {utilization_calc}%"

        utilization = output_dictionary[SystemConsts.MEMORY_SWAP_KEY]["utilization"]
        assert SystemConsts.MEMORY_PERCENT_THRESH_MIN <= utilization < SystemConsts.MEMORY_PERCENT_THRESH_MAX, \
            "Swap utilization percentage is out of range"
        if output_dictionary[SystemConsts.MEMORY_SWAP_KEY]["total"] > 0:
            utilization_calc = (output_dictionary[SystemConsts.MEMORY_SWAP_KEY]["used"] /
                                output_dictionary[SystemConsts.MEMORY_SWAP_KEY]["total"]) * 100
            assert abs(utilization - utilization_calc) < 0.000001, \
                f"Mismatch between Swap utilization: {utilization}% to calculated utilization: {utilization_calc}%"


@pytest.mark.system
@pytest.mark.simx
def test_show_system_cpu(engines, devices):
    """
    Run show system memory and verify there is a correlation between the different values,
    and the values are in appropriate range.
        Test flow:
            1. run show system memory
            2. verify 3 keys (core-count, model and utilization) are exist
            3. verify switch CPU core-count matches the switch type
            4. validate Utilization percentages are not reaching 30%
    """
    with allure.step('Run show system cpu command and verify that each field has a value'):
        time.sleep(10)
        system = System()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(system.show("cpu")).get_returned_value()

        assert len(output_dictionary.keys()) == 3, "Unexpected Number of keys"
        assert list(output_dictionary.keys())[0] == SystemConsts.CPU_CORE_COUNT_KEY, "Unexpected Key value"
        assert list(output_dictionary.keys())[1] == SystemConsts.CPU_MODEL_KEY, "Unexpected Key value"
        assert list(output_dictionary.keys())[2] == SystemConsts.CPU_UTILIZATION_KEY, "Unexpected Key value"
        assert output_dictionary[SystemConsts.CPU_CORE_COUNT_KEY] == devices.dut.SWITCH_CORE_COUNT, \
            "Unexpected switch core-count"

        utilization = output_dictionary[SystemConsts.CPU_UTILIZATION_KEY]
        assert SystemConsts.CPU_PERCENT_THRESH_MIN < utilization < SystemConsts.CPU_PERCENT_THRESH_MAX, \
            "utilization percentage is out of range"


# ------------ Open API tests -----------------

@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.simx
@pytest.mark.nvos_chipsim_ci
def test_system_openapi(engines, devices, topology_obj, test_name):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_system(engines, devices, topology_obj, test_name)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.simx
def test_show_system_cpu_openapi(engines, devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_show_system_cpu(engines, devices)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.simx
def test_show_system_memory_openapi(engines, devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_show_system_memory(engines, devices)


@pytest.mark.openapi
@pytest.mark.system
def test_show_system_reboot_openapi(engines, devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_show_system_reboot(engines, devices)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.simx
@pytest.mark.nvos_ci
def test_show_system_version_openapi(engines, devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_show_system_version(engines, devices)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.simx
def test_system_message_openapi(engines, devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_system_message(engines, devices)
