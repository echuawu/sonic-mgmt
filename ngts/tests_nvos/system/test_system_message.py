import logging
import allure
import pytest
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType

import time
logger = logging.getLogger()


def clear_system_messages(system, engines):
    """
    Method to unset the system messages for pre-login, post-login and post-logout
    :param system:  System object
           engines: Engines object
    """
    with allure.step('Run unset system message pre-login command and apply config'):
        system.message.unset(engines.dut, SystemConsts.PRE_LOGIN_MESSAGE).verify_result()

    with allure.step('Run unset system message post-login command and apply config'):
        system.message.unset(engines.dut, SystemConsts.POST_LOGIN_MESSAGE).verify_result()

    with allure.step('Run unset system message post-logout command and apply config'):
        system.message.unset(engines.dut, SystemConsts.POST_LOGOUT_MESSAGE).verify_result()


@pytest.mark.banner
@pytest.mark.system
@pytest.mark.simx
def test_show_system_message(engines, devices):
    """
    Run show/set/unset system message command and verify the required pre-login message
        Test flow:
            1. Check show system message and verify all banner messages are available
            2. Run 'nv unset system message pre-login'
            3. Run 'nv unset system message post-login'
            4. Run 'nv unset system message post-logout'
            5. Run 'nv show system message'
            6. Verify that all messages have default values
    """
    new_pre_login_msg = "Testing PRE  LOGIN MESSAGE"
    new_post_login_msg = "Testing POST LOGIN MESSAGE"
    new_post_logout_msg = "Testing POST LOGOUT MESSAGE"
    system = System()
    clear_system_messages(system, engines)

    try:

        with allure.step('Run show system message command and verify that each field has a value'):
            message_output = OutputParsingTool.parse_json_str_to_dictionary(system.message.show()).get_returned_value()
            ValidationTool.verify_field_value_exist_in_output_dict(message_output,
                                                                   SystemConsts.PRE_LOGIN_MESSAGE).verify_result()
            ValidationTool.verify_field_value_exist_in_output_dict(message_output,
                                                                   SystemConsts.POST_LOGIN_MESSAGE).verify_result()
            ValidationTool.verify_field_value_exist_in_output_dict(message_output,
                                                                   SystemConsts.POST_LOGOUT_MESSAGE).verify_result()

        with allure.step('Run unset system message pre-login command and apply config'):
            system.message.unset(engines.dut, SystemConsts.PRE_LOGIN_MESSAGE).verify_result()

        with allure.step('Verify pre-login changed to default in show system'):
            message_output = OutputParsingTool.parse_json_str_to_dictionary(system.message.show()).get_returned_value()
            ValidationTool.verify_field_value_in_output(message_output, SystemConsts.PRE_LOGIN_MESSAGE,
                                                        SystemConsts.PRE_LOGIN_MESSAGE_DEFAULT_VALUE).verify_result()

        with allure.step('Run unset system message post-login command and apply config'):
            system.message.unset(engines.dut, SystemConsts.POST_LOGIN_MESSAGE).verify_result()

        with allure.step('Verify post-login changed to default in show system'):
            message_output = OutputParsingTool.parse_json_str_to_dictionary(system.message.show()).get_returned_value()
            ValidationTool.verify_field_value_in_output(message_output, SystemConsts.POST_LOGIN_MESSAGE,
                                                        SystemConsts.POST_LOGIN_MESSAGE_DEFAULT_VALUE).verify_result()

        with allure.step('Run unset system message post-logout command and apply config'):
            system.message.unset(engines.dut, SystemConsts.POST_LOGOUT_MESSAGE).verify_result()

        with allure.step('Verify post-logout changed to default in show system'):
            message_output = OutputParsingTool.parse_json_str_to_dictionary(system.message.show()).get_returned_value()
            ValidationTool.verify_field_value_in_output(message_output, SystemConsts.POST_LOGOUT_MESSAGE,
                                                        SystemConsts.POST_LOGOUT_MESSAGE_DEFAULT_VALUE).verify_result()

    finally:
        clear_system_messages(system, engines)


@pytest.mark.banner
@pytest.mark.system
@pytest.mark.simx
def test_set_system_message_pre_login(engines, devices):
    """
    Run show/set/unset system message command and verify the required pre-login message
        Test flow:
            1. Set pre-login message[run cmd + apply conf]
            2. verify pre-login changed to new message in show system
            3. Verify post-login was not affected in show system
            4. Verify post-logout was not affected in show system
            5. Verify pre-login changed to new message upon connecting via SSH
            6. Verify pre-login changed to new message upon connecting via Serial
            7. Unset pre-login message[run cmd + apply conf]
            8. verify pre-login changed to default in show system
            9. Verify pre-login changed to default upon connecting via SSH
            10. Verify pre-login changed to default upon connecting via Serial
    """
    new_pre_login_msg = "Testing PRE LOGIN MESSAGE"
    system = System()

    try:
        with allure.step('Run set system message pre-login command and apply config'):
            system.message.set(new_pre_login_msg, engines.dut, SystemConsts.PRE_LOGIN_MESSAGE).verify_result()

        message_output = OutputParsingTool.parse_json_str_to_dictionary(system.message.show()).get_returned_value()

        with allure.step('Verify pre-login changed to new message in show system'):
            ValidationTool.verify_field_value_in_output(message_output, SystemConsts.PRE_LOGIN_MESSAGE,
                                                        new_pre_login_msg).verify_result()

        with allure.step('Verify post-login did not change in show system'):
            ValidationTool.verify_field_value_in_output(message_output, SystemConsts.POST_LOGIN_MESSAGE,
                                                        SystemConsts.POST_LOGIN_MESSAGE_DEFAULT_VALUE).verify_result()

        with allure.step('Verify post-logout did not change in show system'):
            ValidationTool.verify_field_value_in_output(message_output, SystemConsts.POST_LOGOUT_MESSAGE,
                                                        SystemConsts.POST_LOGOUT_MESSAGE_DEFAULT_VALUE).verify_result()

        with allure.step('Run unset system message pre-login command and apply config'):
            system.message.unset(engines.dut, SystemConsts.PRE_LOGIN_MESSAGE).verify_result()

        with allure.step('Verify pre-login changed to default in show system'):
            message_output = OutputParsingTool.parse_json_str_to_dictionary(system.message.show()).get_returned_value()
            ValidationTool.verify_field_value_in_output(message_output, SystemConsts.PRE_LOGIN_MESSAGE,
                                                        SystemConsts.PRE_LOGIN_MESSAGE_DEFAULT_VALUE).verify_result()
    finally:
        clear_system_messages(system, engines)


# ------------ Open API tests -----------------

@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.simx
def test_system_show_message_openapi(engines, devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_show_system_message(engines, devices)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.simx
def test_set_system_message_pre_login_openapi(engines, devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_set_system_message_pre_login(engines, devices)
