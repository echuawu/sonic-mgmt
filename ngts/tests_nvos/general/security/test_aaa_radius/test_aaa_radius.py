import logging
import time
import pytest
from ngts.tests_nvos.general.security.security_test_tools.generic_remote_aaa_testing.generic_remote_aaa_testing import *
from ngts.tools.test_utils import allure_utils as allure
import random
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.security_test_tools.security_test_utils import \
    validate_users_authorization_and_role, validate_authentication_fail_with_credentials
from ngts.tests_nvos.general.security.test_aaa_radius.constants import RadiusConstants
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.tests_nvos.general.security.test_ssh_config.constants import SshConfigConsts
from infra.tools.general_constants.constants import DefaultConnectionValues
from infra.tools.connection_tools.pexpect_serial_engine import PexpectSerialEngine


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_radius_set_unset_show(test_api, engines):
    radius_obj = System().aaa.radius
    generic_aaa_test_set_unset_show(
        test_api=test_api, engines=engines,
        remote_aaa_type=RemoteAaaType.RADIUS,
        main_resource_obj=radius_obj,
        confs={
            radius_obj: {
                AaaConsts.AUTH_TYPE: random.choice(RadiusConstants.VALID_VALUES[AaaConsts.AUTH_TYPE]),
                AaaConsts.PORT: random.choice(RadiusConstants.VALID_VALUES[AaaConsts.PORT]),
                AaaConsts.RETRANSMIT: random.choice(RadiusConstants.VALID_VALUES[AaaConsts.RETRANSMIT]),
                AaaConsts.SECRET: 'alontheking',
                AaaConsts.TIMEOUT: random.choice(RadiusConstants.VALID_VALUES[AaaConsts.TIMEOUT]),
                RadiusConstants.RADIUS_STATISTICS: random.choice(RadiusConstants.VALID_VALUES[RadiusConstants.RADIUS_STATISTICS])
            }
        },
        hostname_conf={
            AaaConsts.AUTH_TYPE: random.choice(RadiusConstants.VALID_VALUES[AaaConsts.AUTH_TYPE]),
            AaaConsts.PORT: random.choice(RadiusConstants.VALID_VALUES[AaaConsts.PORT]),
            AaaConsts.RETRANSMIT: random.choice(RadiusConstants.VALID_VALUES[AaaConsts.RETRANSMIT]),
            AaaConsts.SECRET: 'alontheking',
            AaaConsts.TIMEOUT: random.choice(RadiusConstants.VALID_VALUES[AaaConsts.TIMEOUT]),
            AaaConsts.PRIORITY: 2
        },
        default_confs={
            radius_obj: RadiusConstants.DEFAULT_RADIUS_CONF
        }
    )


# -------------------------- OLD TESTS ---------------------------------


def configure_radius_server(radius_server_info, verify_show: bool = False):
    """
    @summary:
        in this function we will configure the given radius server on the switch.
        and validate the configurations using show command
    :param radius_server_info: dictionary containing the following keys
    e.g.:
        {
            "hostname" : <value>
            "port" : <value>,
            "auth-type" : <value>,
            "secret"  : <value>,
            "timeout" : <value>, (optional argument)
            "priority" : <value> (optional argument)
        }
        Users: are the users configured on the radius server
    """
    system = System(None)

    with allure.step("configuring the following radius server on the switch:\n{}".format(radius_server_info)):
        logging.info("configuring the following radius server on the switch:\n{}".format(radius_server_info))
        system.aaa.radius.set(RadiusConstants.RADIUS_HOSTNAME, radius_server_info[RadiusConstants.RADIUS_HOSTNAME])
        system.aaa.radius.rad_hostname.set_param(radius_server_info[RadiusConstants.RADIUS_HOSTNAME],
                                                 'port', int(radius_server_info[RadiusConstants.RADIUS_AUTH_PORT]))
        system.aaa.radius.rad_hostname.set_param(radius_server_info[RadiusConstants.RADIUS_HOSTNAME],
                                                 'auth-type', radius_server_info[RadiusConstants.RADIUS_AUTH_TYPE])
        if radius_server_info.get(RadiusConstants.RADIUS_TIMEOUT):
            system.aaa.radius.rad_hostname.set_param(radius_server_info[RadiusConstants.RADIUS_HOSTNAME],
                                                     'timeout', int(radius_server_info[RadiusConstants.RADIUS_TIMEOUT]))
        if radius_server_info.get(RadiusConstants.RADIUS_PRIORITY):
            system.aaa.radius.rad_hostname.set_param(radius_server_info[RadiusConstants.RADIUS_HOSTNAME],
                                                     'priority', radius_server_info[RadiusConstants.RADIUS_PRIORITY])
        system.aaa.radius.rad_hostname.set_param(radius_server_info[RadiusConstants.RADIUS_HOSTNAME],
                                                 'secret', radius_server_info[RadiusConstants.RADIUS_PASSWORD], True, True)
    if verify_show:
        with allure.step("Validating configurations"):
            logging.info("Validating configurations")
            output = Tools.OutputParsingTool.parse_json_str_to_dictionary(system.aaa.radius.rad_hostname.show_hostname(
                radius_server_info[RadiusConstants.RADIUS_HOSTNAME], rev=ConfState.APPLIED)).get_returned_value()
            assert output[RadiusConstants.RADIUS_AUTH_TYPE] == radius_server_info[RadiusConstants.RADIUS_AUTH_TYPE], \
                "Not same auth type, actual: {}, expected: {}".format(output[RadiusConstants.RADIUS_AUTH_TYPE],
                                                                      radius_server_info[RadiusConstants.RADIUS_AUTH_TYPE])
            assert str(output[RadiusConstants.RADIUS_AUTH_PORT]) == str(radius_server_info[RadiusConstants.RADIUS_AUTH_PORT]), \
                "Not same auth port, actual: {}, expected: {}".format(str(output[RadiusConstants.RADIUS_AUTH_PORT]),
                                                                      str(radius_server_info[RadiusConstants.RADIUS_AUTH_PORT]))
            priority = RadiusConstants.RADIUS_DEFAULT_PRIORITY if not radius_server_info.get(
                RadiusConstants.RADIUS_PRIORITY) else radius_server_info[RadiusConstants.RADIUS_PRIORITY]
            assert str(int(output[RadiusConstants.RADIUS_PRIORITY])) == str(priority), \
                "Not same priority, actual: {}, expected: {}".format(str(output[RadiusConstants.RADIUS_PRIORITY]), str(priority))
            timeout = RadiusConstants.RADIUS_DEFAULT_TIMEOUT if not radius_server_info.get(
                RadiusConstants.RADIUS_TIMEOUT) else radius_server_info[RadiusConstants.RADIUS_TIMEOUT]
            assert str(int(output[RadiusConstants.RADIUS_TIMEOUT])) == str(int(timeout)), \
                "Not same timeout, actual: {}, expected: {}".format(str(output[RadiusConstants.RADIUS_TIMEOUT]),
                                                                    str(radius_server_info[RadiusConstants.RADIUS_TIMEOUT]))


def enable_radius_feature(dut_engine):
    """
    @summary:
        in this function we want to enable the radius server functionality,
        in the current implementation we use sonic commands, once the nv commands
        are available we will change this function
    """
    with allure.step("Enabling Radius by setting radius auth. method as first auth. method"):
        logging.info("Enabling Radius by setting radius auth. method as first auth. method")
        dut_engine.run_cmd("nv set system aaa authentication order radius,local")
        dut_engine.run_cmd("nv set system aaa authentication fallback enabled")
        dut_engine.run_cmd("nv set system aaa authentication failthrough enabled")
        dut_engine.run_cmd("nv config apply -y")


def test_radius_basic_configurations(engines, clear_all_radius_configurations):
    """
    @summary:
        in this test case we want to connect to configure default configurations for
        radius feature and validate connectivity using radius authentication.
        Default configurations are:
            1. default auth port
            2. default auth type
        additionally, we will test user role for the radius users
    """
    with allure.step("Configuring and enabling radius server"):
        logging.info("Configuring and enabling radius server")
        radius_server_info = RadiusConstants.RADIUS_SERVERS_DICTIONARY['physical_radius_server']
        configure_radius_server(radius_server_info)
        enable_radius_feature(engines.dut)

    with allure.step("Validating access to switch with username configured on the radius server"):
        logging.info("Validating access to switch with username configured on the radius server")
        validate_users_authorization_and_role(engines, radius_server_info[RadiusConstants.RADIUS_SERVER_USERS])


def test_radius_basic_configurations_openapi(engines, clear_all_radius_configurations):
    """
    @summary:
        in this test case we want to connect to configure default configurations for
        radius feature and validate connectivity using radius authentication.
        Default configurations are:
            1. default auth port
            2. default auth type
        additionally, we will test user role for the radius users
    """
    TestToolkit.tested_api = ApiType.OPENAPI
    test_radius_basic_configurations(engines, clear_all_radius_configurations)


def randomize_radius_server():
    """
    @summary:
        in this function we randomize radius server dictionary and return it.
        e.g. of return value:
        {
            "hostname" : <value>
            "port" : <value>,
            "auth-type" : <value>,
            "secret"  : <value>
        }
    """
    randomized_radius_server_info = {
        "hostname": f"1.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}",
        "port": f"{random.randint(0, 255)}",
        "auth-type": "pap",
        "secret": f"{random.randint(0, 255)}",
    }

    return randomized_radius_server_info


def test_radius_priority_and_fail_through_functionality(engines,
                                                        clear_all_radius_configurations):
    """
    @summary: in this test case we want to validate the priority functionality.
    Priority in radius server means the following: if the current radius server is down,
    connect to the second one in line.
    and fail through means to connect to the next radius server in line if the credentials are not matched
    at the current server. (fail through will go to next server)
    In order to test this functionality:
        1. configure unreal radius server (invalid ip), set as highest priority
        3. configure real radius server at second priority
        4. configure real radius server at third priority
    Note:
        1. To be able to test radius fail through we need to connect using credentials that does not exist on the
        first real radius server.
        2. We also test local credentials (DefaultConnectionValues.ADMIN, DefaultConnectionValues.DEFAULT_PASSWORD)

    """
    real_radius_servers_order = []
    enable_radius_feature(engines.dut)

    with allure.step("Configuring unreal radius server"):
        logging.info("Configuring unreal radius server")
        invalid_radius_server_info = randomize_radius_server()
        invalid_radius_server_info[RadiusConstants.RADIUS_PRIORITY] = RadiusConstants.RADIUS_MAX_PRIORITY
        logging.info("Unreal radius server info: {}".format(invalid_radius_server_info))
        configure_radius_server(invalid_radius_server_info)

    with allure.step("Configuring real radius server with lower priorities"):
        logging.info("Configuring real radius server with lower priorities")
        priority = RadiusConstants.RADIUS_MAX_PRIORITY - 1
        for radius_key, radius_server_info in RadiusConstants.RADIUS_SERVERS_DICTIONARY.items():
            radius_server_info[RadiusConstants.RADIUS_PRIORITY] = priority
            configure_radius_server(radius_server_info)
            real_radius_servers_order.append(radius_key)
            priority -= 1

    with allure.step("Sleeping {} secs to apply configurations".format(RadiusConstants.SLEEP_TO_APPLY_CONFIGURATIONS)):
        logging.info("Sleeping {} secs to apply configurations".format(RadiusConstants.SLEEP_TO_APPLY_CONFIGURATIONS))
        time.sleep(RadiusConstants.SLEEP_TO_APPLY_CONFIGURATIONS)

    with allure.step("Testing Priority by connecting to switch using first real radius server credentials"):
        logging.info("Testing Priority by connecting to switch using first real radius server credentials")
        validate_users_authorization_and_role(engines,
                                              RadiusConstants.RADIUS_SERVERS_DICTIONARY[real_radius_servers_order[0]][
                                                  RadiusConstants.RADIUS_SERVER_USERS])

    with allure.step("Testing Priority by connecting to switch using second real radius server credentials"):
        logging.info("Testing Priority by connecting to switch using second real radius server credentials")
        validate_users_authorization_and_role(engines,
                                              RadiusConstants.RADIUS_SERVERS_DICTIONARY[real_radius_servers_order[1]][
                                                  RadiusConstants.RADIUS_SERVER_USERS])


def test_radius_configurations_error_flow(engines, clear_all_radius_configurations):
    """
    @summary: in this test case we want to check the error flow of radius configurations,
        we want to check that with mismatched values *configured* between radius server to the switch we are not able
        to connect to switch.
    e.g. for radius configurations:
        {
            "port" : <value>,
            "secret"  : <value>
        }
        each one of the above values can be configured with invalid values
    Test flow:
        1. configure valid radius server
        2. connect to device using radius server users
        3. set mismatching values for each parameter above and validate no authentication happens
    Note:
        we do not want to check invalid IP address (hostname) because we cover this error flow
        in the test case test_radius_priority_and_fail_through_functionality where we configure
        invalid (unreal) ip address of radius server.
    """
    enable_radius_feature(engines.dut)

    with allure.step("Configuring valid ip address"):
        logging.info("Configuring valid ip address")
        radius_server_info = RadiusConstants.RADIUS_SERVERS_DICTIONARY['physical_radius_server']
        configure_radius_server(radius_server_info)

    with allure.step("Connecting to switch and validate roles"):
        logging.info("Connecting to switch and validate roles")
        validate_users_authorization_and_role(engines, radius_server_info[RadiusConstants.RADIUS_SERVER_USERS])

    system = System()
    with allure.step("Configuring invalid auth-port and validating applied configurations"):
        invalid_port = Tools.RandomizationTool.select_random_value(
            [i for i in range(SshConfigConsts.MIN_LOGIN_PORT, SshConfigConsts.MAX_LOGIN_PORT)],
            [int(radius_server_info[RadiusConstants.RADIUS_AUTH_PORT])]).get_returned_value()
        logging.info("Configuring invalid auth-port: {}".format(invalid_port))
        system.aaa.radius.rad_hostname.set_param(radius_server_info[RadiusConstants.RADIUS_HOSTNAME],
                                                 'port', invalid_port, True, True)
        apply_configuration_sleep = 10
        with allure.step("Sleeping {} secs to apply configurations".format(apply_configuration_sleep)):
            logging.info("Sleeping {} secs to apply configurations".format(apply_configuration_sleep))
            time.sleep(apply_configuration_sleep)

        radius_server_user = radius_server_info[RadiusConstants.RADIUS_SERVER_USERS][0]
        validate_authentication_fail_with_credentials(engines,
                                                      username=radius_server_user[
                                                          RadiusConstants.RADIUS_SERVER_USERNAME],
                                                      password=radius_server_user[
                                                          RadiusConstants.RADIUS_SERVER_USER_PASSWORD])

    with allure.step("Configuring invalid password and validating applied configurations"):
        random_string = Tools.RandomizationTool.get_random_string(10)
        logging.info("Configuring invalid password: {}".format(random_string))
        system.aaa.radius.rad_hostname.set_param(radius_server_info[RadiusConstants.RADIUS_HOSTNAME],
                                                 'secret', random_string, True, True)
        with allure.step("Sleeping {} secs to apply configurations".format(apply_configuration_sleep)):
            logging.info("Sleeping {} secs to apply configurations".format(apply_configuration_sleep))
            time.sleep(apply_configuration_sleep)

        radius_server_user = radius_server_info[RadiusConstants.RADIUS_SERVER_USERS][0]
        validate_authentication_fail_with_credentials(engines,
                                                      username=radius_server_user[
                                                          RadiusConstants.RADIUS_SERVER_USERNAME],
                                                      password=radius_server_user[
                                                          RadiusConstants.RADIUS_SERVER_USER_PASSWORD])


# def test_radius_set_show_unset(engines, clear_all_radius_configurations):
#     """
#     @summary: in this test case we want to validate radius commands:
#         1. set
#         2. show
#         3. unset
#     """
#     configured_radius_servers_hostname = []
#
#     with allure.step("Configuring Radius Server"):
#         logging.info("Configuring Radius Server")
#         for radius_key, radius_server_info in RadiusConstants.RADIUS_SERVERS_DICTIONARY.items():
#             configure_radius_server(radius_server_info)
#             configured_radius_servers_hostname.append(radius_server_info[RadiusConstants.RADIUS_HOSTNAME])
#
#     system = System()
#     with allure.step("Validate Unset command"):
#         logging.info("Validate Unset command")
#         for hostname in configured_radius_servers_hostname:
#             system.aaa.radius.rad_hostname.unset_hostname(hostname, True, True).verify_result(should_succeed=True)
#         system.aaa.radius.unset().verify_result(should_succeed=True)
#
#     with allure.step("Validating the show command output"):
#         logging.info("Validating the show command output")
#         output = system.aaa.radius.rad_hostname.show()
#         for hostname in configured_radius_servers_hostname:
#             assert hostname not in output, "hostname: {}, appears in the show radius hostname after removing it".format(
#                 hostname)


# def test_radius_set_show_unset_openapi(engines, clear_all_radius_configurations):
#     """
#     @summary: in this test case we want to validate radius commands:
#         1. set
#         2. show
#         3. unset
#     """
#     TestToolkit.tested_api = ApiType.OPENAPI
#     test_radius_set_show_unset(engines, clear_all_radius_configurations)


def test_radius_all_supported_auth_types(engines, clear_all_radius_configurations):
    """
    @summary: in this test case we want to validate all supported auth types:
    [pap, chap, mschapv2]
    """
    enable_radius_feature(engines.dut)

    for auth_type in RadiusConstants.AUTH_TYPES:
        with allure.step("Configuring auth-type: {}".format(auth_type)):
            logging.info("Configuring auth-type: {}".format(auth_type))
            radius_server_info = RadiusConstants.RADIUS_SERVERS_DICTIONARY['physical_radius_server']
            radius_server_info[RadiusConstants.RADIUS_AUTH_TYPE] = auth_type
            configure_radius_server(radius_server_info)
        with allure.step("Validating access to switch with username configured on the radius server"):
            logging.info("Validating access to switch with username configured on the radius server")
            validate_users_authorization_and_role(engines,
                                                  radius_server_info[RadiusConstants.RADIUS_SERVER_USERS])


def test_radius_root_user_authentication(engines, clear_all_radius_configurations):
    """
    @summary: in this test case we want to validate that root user is authenticated locally alone.
    """
    enable_radius_feature(engines.dut)

    with allure.step("Configuring valid ip address containing root user configured"):
        logging.info("Configuring valid ip address containing root user configured")
        radius_server_info = RadiusConstants.RADIUS_SERVERS_DICTIONARY['physical_radius_server']
        configure_radius_server(radius_server_info)

    with allure.step("Validating that root user is not to able to be accessed through radius credentials"):
        logging.info("Validating that root user is not to able to be accessed through radius credentials")
        validate_authentication_fail_with_credentials(engines,
                                                      username=radius_server_info['special_user'][0][
                                                          RadiusConstants.RADIUS_SERVER_USERNAME],
                                                      password=radius_server_info['special_user'][0][
                                                          RadiusConstants.RADIUS_SERVER_USER_PASSWORD])


def create_serial_engine_and_login(topology_obj, username, password):
    """
    @summary: in this helper function we want to create a serial engine and connect to switch
    using the credentials passed to the function.
    """
    att = topology_obj.players['dut_serial']['attributes'].noga_query_data['attributes']
    # add connection options to pass connection problems
    extended_rcon_command = att['Specific']['serial_conn_cmd'].split(' ')
    extended_rcon_command.insert(1, DefaultConnectionValues.BASIC_SSH_CONNECTION_OPTIONS)
    extended_rcon_command = ' '.join(extended_rcon_command)
    try:
        serial_engine = PexpectSerialEngine(ip=att['Specific']['ip'],
                                            username=username,
                                            password=password,
                                            rcon_command=extended_rcon_command,
                                            timeout=30)
        serial_engine.create_serial_engine(login_to_switch=True)
    finally:
        serial_engine.__del__()


def test_radius_serial_connection_authentication(engines, clear_all_radius_configurations, topology_obj):
    """
    @summary: in this test case we want to validate successful authentication through radius
    when using serial connection
    """
    enable_radius_feature(engines.dut)

    with allure.step("Configuring valid ip address"):
        logging.info("Configuring valid ip address")
        radius_server_info = RadiusConstants.RADIUS_SERVERS_DICTIONARY['physical_radius_server']
        configure_radius_server(radius_server_info)

    with allure.step("Initializing serial connection and validating radius authentication"):
        logging.info("Initializing serial connection and validating radius authentication")
        user_info = radius_server_info[RadiusConstants.RADIUS_SERVER_USERS][0]
        create_serial_engine_and_login(topology_obj, user_info[RadiusConstants.RADIUS_SERVER_USERNAME],
                                       user_info[RadiusConstants.RADIUS_SERVER_USER_PASSWORD])
