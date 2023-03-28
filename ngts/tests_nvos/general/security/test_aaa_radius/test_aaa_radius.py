import logging
import time
import allure
import random
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.test_aaa_radius.constants import RadiusConstans
from ngts.nvos_tools.infra.Tools import Tools
from ngts.tests_nvos.general.security.test_aaa_radius.conftest import clear_all_radius_configurations, restore_original_engine_credentials
from ngts.nvos_constants.constants_nvos import SystemConsts, ApiType
from ngts.tests_nvos.general.security.test_ssh_config.constants import SshConfigConsts
from netmiko.ssh_exception import NetmikoAuthenticationException
from infra.tools.general_constants.constants import DefaultConnectionValues
from infra.tools.connection_tools.pexpect_serial_engine import PexpectSerialEngine


def configure_radius_server(radius_server_info):
    '''
    @summary:
        in this function we will configure the given radius server on the switch.
        and validate the configurations using show command
    :param dut_engine: dut engine
    :param radius_server_dict: dictionary containing the following keys
    e.g.:
        {
            "hostname" : <value>
            "auth-port" : <value>,
            "auth-type" : <value>,
            "password"  : <value>,
            "timeout" : <value>, (optional argument)
            "priority" : <value> (optional argument)
        }
        Users: are the users configured on the radius server
    '''
    system = System(None)

    with allure.step("configuring the following radius server on the switch:\n{}".format(radius_server_info)):
        logging.info("configuring the following radius server on the switch:\n{}".format(radius_server_info))
        system.aaa.radius.set(RadiusConstans.RADIUS_HOSTNAME, radius_server_info[RadiusConstans.RADIUS_HOSTNAME], apply=True, ask_for_confirmation=True)
        system.aaa.radius.hostname.set_password(radius_server_info[RadiusConstans.RADIUS_HOSTNAME], radius_server_info[RadiusConstans.RADIUS_PASSWORD])
        system.aaa.radius.hostname.set_auth_port(radius_server_info[RadiusConstans.RADIUS_HOSTNAME], int(radius_server_info[RadiusConstans.RADIUS_AUTH_PORT]))
        system.aaa.radius.hostname.set_auth_type(radius_server_info[RadiusConstans.RADIUS_HOSTNAME], radius_server_info[RadiusConstans.RADIUS_AUTH_TYPE])
        if radius_server_info.get(RadiusConstans.RADIUS_TIMEOUT):
            system.aaa.radius.hostname.set_timeout(radius_server_info[RadiusConstans.RADIUS_HOSTNAME], int(radius_server_info[RadiusConstans.RADIUS_TIMEOUT]), True, True)
        if radius_server_info.get(RadiusConstans.RADIUS_PRIORITY):
            system.aaa.radius.hostname.set_priority(radius_server_info[RadiusConstans.RADIUS_HOSTNAME], radius_server_info[RadiusConstans.RADIUS_PRIORITY], True, True)

    with allure.step("Validating configurations"):
        logging.info("Validating configurations")
        output = Tools.OutputParsingTool.parse_json_str_to_dictionary(system.aaa.radius.hostname.show_hostname(radius_server_info[RadiusConstans.RADIUS_HOSTNAME])).get_returned_value()
        assert output[RadiusConstans.RADIUS_AUTH_TYPE] == radius_server_info[RadiusConstans.RADIUS_AUTH_TYPE], \
            "Not same auth type, actual: {}, expected: {}".format(output[RadiusConstans.RADIUS_AUTH_TYPE], radius_server_info[RadiusConstans.RADIUS_AUTH_TYPE])
        assert output[RadiusConstans.RADIUS_AUTH_PORT] == radius_server_info[RadiusConstans.RADIUS_AUTH_PORT], \
            "Not same auth port, actual: {}, expected: {}".format(output[RadiusConstans.RADIUS_AUTH_PORT], radius_server_info[RadiusConstans.RADIUS_AUTH_PORT])
        priority = RadiusConstans.RADIUS_DEFAULT_PRIORITY if not radius_server_info.get(RadiusConstans.RADIUS_PRIORITY) else radius_server_info[RadiusConstans.RADIUS_PRIORITY]
        assert int(output[RadiusConstans.RADIUS_PRIORITY]) == priority, \
            "Not same priority, actual: {}, expected: {}".format(output[RadiusConstans.RADIUS_PRIORITY], priority)
        timeout = RadiusConstans.RADIUS_DEFAULT_TIMEOUT if not radius_server_info.get(RadiusConstans.RADIUS_TIMEOUT) else radius_server_info[RadiusConstans.RADIUS_TIMEOUT]
        assert int(output[RadiusConstans.RADIUS_TIMEOUT]) == int(timeout), \
            "Not same timeout, actual: {}, expected: {}".format(output[RadiusConstans.RADIUS_TIMEOUT], radius_server_info[RadiusConstans.RADIUS_TIMEOUT])


def enable_radius_feature(dut_engine):
    '''
    @summary:
        in this function we want to enable the radius server functionality,
        in the current implementation we use sonic commands, once the nv commands
        are available we will change this function
    '''
    with allure.step("Enabling Radius by setting radius auth. method as first auth. method"):
        logging.info("Enabling Radius by setting radius auth. method as first auth. method")
        dut_engine.run_cmd("nv set system aaa authentication order radius,local")
        dut_engine.run_cmd("nv set system aaa authentication fallback enabled")
        dut_engine.run_cmd("nv set system aaa authentication failthrough enabled")
        dut_engine.run_cmd("nv config apply -y")


def connect_to_switch_and_validate_role(engines, username, password, role=SystemConsts.ROLE_VIEWER):
    '''
    @summary:
        in this helper function, we will connect to switch using username, password & port
        and validate user role configurations
    '''
    with allure.step("Using username: {}, role: {}".format(username, role)):
        logging.info("Using username: {}, role: {}".format(username, role))
        engines.dut.update_credentials(username=username, password=password)

    system = System(None)
    SHOW_SYSTEM_VERSION_CMD = 'nv show system version'
    with allure.step("Running command: \'{}\'".format(SHOW_SYSTEM_VERSION_CMD)):
        logging.info("Running command: \'{}\'".format(SHOW_SYSTEM_VERSION_CMD))
        system.version.show()

    with allure.step("Validating role permissions are as expected"):
        logging.info("Validating role permissions are as expected")
        if role == SystemConsts.DEFAULT_USER_ADMIN:
            logging.info("User has admin permissions and can set configurations")
            system.message.set("NVOS TESTS", engines.dut, field_name='pre-login').verify_result(should_succeed=True)
            system.message.unset(engines.dut, field_name='pre-login').verify_result(should_succeed=True)
        else:
            logging.info("User has monitor permissions and cannot set configurations")
            system.message.set("NVOS TESTS", engines.dut, field_name='pre-login').verify_result(should_succeed=False)


def validate_users_authorization_and_role(engines, users):
    """
    @summary:
        in this function we want to iterate on all users given and validate that access to switch
        and role as expected.
        We will restore the engine to default credentials afterwards
    """
    try:
        for user_info in users:
            connect_to_switch_and_validate_role(engines, user_info['username'], user_info['password'], user_info['role'])
    except Exception as err:
        logging.info("Got an exception while connection to switch and validating role")
        raise err
    finally:
        restore_original_engine_credentials(engines)


def test_radius_basic_configurations(engines, clear_all_radius_configurations):
    '''
    @summary:
        in this test case we want to connect to configure default configurations for
        radius feature and validate connectivity using radius authentication.
        Default configurations are:
            1. default auth port
            2. default auth type
        additionally, we will test user role for the radius users
    '''
    with allure.step("Configuring and enabling radius server"):
        logging.info("Configuring and enabling radius server")
        radius_server_info = RadiusConstans.RADIUS_SERVERS_DICTIONARY['physical_radius_server']
        configure_radius_server(radius_server_info)
        enable_radius_feature(engines.dut)

    with allure.step("Validating access to switch with username configured on the radius server"):
        logging.info("Validating access to switch with username configured on the radius server")
        validate_users_authorization_and_role(engines, radius_server_info[RadiusConstans.RADIUS_SERVER_USERS])


def test_radius_basic_configurations_openapi(engines, clear_all_radius_configurations):
    '''
    @summary:
        in this test case we want to connect to configure default configurations for
        radius feature and validate connectivity using radius authentication.
        Default configurations are:
            1. default auth port
            2. default auth type
        additionally, we will test user role for the radius users
    '''
    TestToolkit.tested_api = ApiType.OPENAPI
    test_radius_basic_configurations(engines, clear_all_radius_configurations)


def randomize_radius_server():
    '''
    @summary:
        in this function we randomize radius server dictionary and return it.
        e.g. of return value:
        {
            "hostname" : <value>
            "auth-port" : <value>,
            "auth-type" : <value>,
            "password"  : <value>
        }
    '''
    randomized_radius_server_info = {
        "hostname": f"1.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}",
        "auth-port": f"{random.randint(0, 255)}",
        "auth-type": "pap",
        "password": f"{random.randint(0, 255)}",
    }

    return randomized_radius_server_info


def test_radius_priority_and_fail_through_functionality(engines,
                                                        clear_all_radius_configurations):
    '''
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
        1. To be able to test radius fail through we need to connect using credentials that doesn't exist on the
        first real radius server.
        2. We also test local credentials (DefaultConnectionValues.ADMIN, DefaultConnectionValues.DEFAULT_PASSWORD)

    '''
    real_radius_servers_order = []
    enable_radius_feature(engines.dut)

    with allure.step("Configuring unreal radius server"):
        logging.info("Configuring unreal radius server")
        invalid_radius_server_info = randomize_radius_server()
        invalid_radius_server_info[RadiusConstans.RADIUS_PRIORITY] = RadiusConstans.RADIUS_MAX_PRIORITY
        logging.info("Unreal radius server info: {}".format(invalid_radius_server_info))
        configure_radius_server(invalid_radius_server_info)

    with allure.step("Configuring real radius server with lower priorities"):
        logging.info("Configuring real radius server with lower priorities")
        priority = RadiusConstans.RADIUS_MAX_PRIORITY - 1
        for radius_key, radius_server_info in RadiusConstans.RADIUS_SERVERS_DICTIONARY.items():
            radius_server_info[RadiusConstans.RADIUS_PRIORITY] = priority
            configure_radius_server(radius_server_info)
            real_radius_servers_order.append(radius_key)
            priority -= 1

    with allure.step("Testing Priority by connecting to switch using first real radius server credentials"):
        logging.info("Testing Priority by connecting to switch using first real radius server credentials")
        validate_users_authorization_and_role(engines,
                                              RadiusConstans.RADIUS_SERVERS_DICTIONARY[real_radius_servers_order[0]][RadiusConstans.RADIUS_SERVER_USERS])

    with allure.step("Testing Priority by connecting to switch using second real radius server credentials"):
        logging.info("Testing Priority by connecting to switch using second real radius server credentials")
        validate_users_authorization_and_role(engines,
                                              RadiusConstans.RADIUS_SERVERS_DICTIONARY[real_radius_servers_order[1]][RadiusConstans.RADIUS_SERVER_USERS])


def validate_failed_authentication_with_new_credentials(engines, username, password):
    '''
    @summary: in this helper function we want to validate authentication failure while using
    username and password credentials
    '''
    with allure.step("Validating failed authentication with new credentials, username: {}".format(username)):
        logging.info("Validating failed authentication with new credentials, username: {}".format(username))
        ConnectionTool.create_ssh_conn(engines.dut.ip, username=username, password=password).verify_result(should_succeed=False)


def test_radius_configurations_error_flow(engines, clear_all_radius_configurations):
    '''
    @summary: in this test case we want to check the error flow of radius configurations,
        we want to check that with mismatched values *configured* between radius server to the switch we are not able to connect to
        switch.
    e.g. for radius configurations:
        {
            "auth-port" : <value>,
            "password"  : <value>
        }
        each one of the above values can be configured with invalid values
    Test flow:
        1. configure valid radius server
        2. connect to device using radius server users
        3. set mismatching values for each parameter above and validate no authentication happens
    Note:
        we don't want to check invalid IP address (hostname) becuase we cover this error flow
        in the test case test_radius_priority_and_fail_through_functionality where we configure
        invalid (unreal) ip address of radius server.
    '''
    enable_radius_feature(engines.dut)

    with allure.step("Configuring valid ip address"):
        logging.info("Configuring valid ip address")
        radius_server_info = RadiusConstans.RADIUS_SERVERS_DICTIONARY['physical_radius_server']
        configure_radius_server(radius_server_info)

    with allure.step("Connecting to switch and validate roles"):
        logging.info("Connecting to switch and validate roles")
        validate_users_authorization_and_role(engines, radius_server_info[RadiusConstans.RADIUS_SERVER_USERS])

    system = System()
    with allure.step("Configuring invalid auth-port and validating applied configurations"):
        invalid_port = Tools.RandomizationTool.select_random_value([i for i in range(SshConfigConsts.MIN_LOGIN_PORT, SshConfigConsts.MAX_LOGIN_PORT)],
                                                                   [int(radius_server_info[RadiusConstans.RADIUS_AUTH_PORT])]).get_returned_value()
        logging.info("Configuring invalid auth-port: {}".format(invalid_port))
        system.aaa.radius.set_hostname_auth_port(radius_server_info[RadiusConstans.RADIUS_HOSTNAME],
                                                 invalid_port, True, True)
        apply_configuration_sleep = 10
        with allure.step("Sleeping {} secs to apply configurations".format(apply_configuration_sleep)):
            logging.info("Sleeping {} secs to apply configurations".format(apply_configuration_sleep))
            time.sleep(apply_configuration_sleep)

        radius_server_user = radius_server_info[RadiusConstans.RADIUS_SERVER_USERS][0]
        validate_failed_authentication_with_new_credentials(engines,
                                                            username=radius_server_user[RadiusConstans.RADIUS_SERVER_USERNAME],
                                                            password=radius_server_user[RadiusConstans.RADIUS_SERVER_USER_PASSWORD])

    with allure.step("Configuring invalid password and validating applied configurations"):
        random_string = Tools.RandomizationTool.get_random_string(10)
        logging.info("Configuring invalid password: {}".format(random_string))
        system.aaa.radius.set_hostname_password(radius_server_info[RadiusConstans.RADIUS_HOSTNAME],
                                                random_string, True, True)
        with allure.step("Sleeping {} secs to apply configurations".format(apply_configuration_sleep)):
            logging.info("Sleeping {} secs to apply configurations".format(apply_configuration_sleep))
            time.sleep(apply_configuration_sleep)

        radius_server_user = radius_server_info[RadiusConstans.RADIUS_SERVER_USERS][0]
        validate_failed_authentication_with_new_credentials(engines,
                                                            username=radius_server_user[RadiusConstans.RADIUS_SERVER_USERNAME],
                                                            password=radius_server_user[RadiusConstans.RADIUS_SERVER_USER_PASSWORD])


def test_radius_set_show_unset(engines, clear_all_radius_configurations):
    """
    @summary: in this test case we want to validate radius commands:
        1. set
        2. show
        3. unset
    """
    configured_radius_servers_hostname = []

    with allure.step("Configuring Radius Server"):
        logging.info("Configuring Radius Server")
        for radius_key, radius_server_info in RadiusConstans.RADIUS_SERVERS_DICTIONARY.items():
            configure_radius_server(radius_server_info)
            configured_radius_servers_hostname.append(radius_server_info[RadiusConstans.RADIUS_HOSTNAME])

    system = System()
    with allure.step("Validate Unset command"):
        logging.info("Validate Unset command")
        for hostname in configured_radius_servers_hostname:
            system.aaa.radius.hostname.unset_hostname(hostname, True, True).verify_result(should_succeed=True)
        system.aaa.radius.unset().verify_result(should_succeed=True)

    with allure.step("Validating the show command output"):
        logging.info("Validating the show command output")
        output = system.aaa.radius.hostname.show()
        for hostname in configured_radius_servers_hostname:
            assert hostname not in output, "hostname: {}, appears in the show radius hostname after removing it".format(hostname)


def test_radius_set_show_unset_openapi(engines, clear_all_radius_configurations):
    """
    @summary: in this test case we want to validate radius commands:
        1. set
        2. show
        3. unset
    """
    TestToolkit.tested_api = ApiType.OPENAPI
    test_radius_set_show_unset(engines, clear_all_radius_configurations)


def test_radius_all_supported_auth_types(engines, clear_all_radius_configurations):
    '''
    @summary: in this test case we want to validate all supported auth types:
    [pap, chap, mschapv2]
    '''
    enable_radius_feature(engines.dut)

    for auth_type in RadiusConstans.AUTH_TYPES:
        with allure.step("Configuring auth-type: {}".format(auth_type)):
            logging.info("Configuring auth-type: {}".format(auth_type))
            radius_server_info = RadiusConstans.RADIUS_SERVERS_DICTIONARY['physical_radius_server']
            radius_server_info[RadiusConstans.RADIUS_AUTH_TYPE] = auth_type
            configure_radius_server(radius_server_info)
        with allure.step("Validating access to switch with username configured on the radius server"):
            logging.info("Validating access to switch with username configured on the radius server")
            validate_users_authorization_and_role(engines,
                                                  radius_server_info[RadiusConstans.RADIUS_SERVER_USERS])


def test_radius_root_user_authentication(engines, clear_all_radius_configurations):
    '''
    @summary: in this test case we want to validate that root user is authenticated locally alone.
    '''
    enable_radius_feature(engines.dut)

    with allure.step("Configuring valid ip address containing root user configured"):
        logging.info("Configuring valid ip address containing root user configured")
        radius_server_info = RadiusConstans.RADIUS_SERVERS_DICTIONARY['physical_radius_server']
        configure_radius_server(radius_server_info)

    with allure.step("Validating that root user is not to able to be accessed through radius credentials"):
        logging.info("Validating that root user is not to able to be accessed through radius credentials")
        validate_failed_authentication_with_new_credentials(engines,
                                                            username=radius_server_info['special_user'][0][RadiusConstans.RADIUS_SERVER_USERNAME],
                                                            password=radius_server_info['special_user'][0][RadiusConstans.RADIUS_SERVER_USER_PASSWORD])


def create_serial_engine_and_login(topology_obj, username, password):
    '''
    @suammary: in this helper function we want to create a serial engine and connect to switch
    using the credentials passed to the function.
    '''
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
    '''
    @summary: in this test case we want to validate successful authentication through radius
    when using serial connection
    '''
    enable_radius_feature(engines.dut)

    with allure.step("Configuring valid ip address"):
        logging.info("Configuring valid ip address")
        radius_server_info = RadiusConstans.RADIUS_SERVERS_DICTIONARY['physical_radius_server']
        configure_radius_server(radius_server_info)

    with allure.step("Initializing serial connection and validating radius authentication"):
        logging.info("Initializing serial connection and validating radius authentication")
        user_info = radius_server_info[RadiusConstans.RADIUS_SERVER_USERS][0]
        create_serial_engine_and_login(topology_obj, user_info[RadiusConstans.RADIUS_SERVER_USERNAME],
                                       user_info[RadiusConstans.RADIUS_SERVER_USER_PASSWORD])
