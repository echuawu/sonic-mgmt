import logging
import allure
import random
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.test_aaa_radius.constants import RadiusConstans
from ngts.nvos_tools.infra.Tools import Tools
from ngts.tests_nvos.general.security.test_aaa_radius.conftest import clear_all_radius_configurations, restore_original_engine_credentials
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.tests_nvos.general.security.test_ssh_config.constants import SshConfigConsts
from netmiko.ssh_exception import NetmikoAuthenticationException


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
        system.aaa.radius.set(RadiusConstans.RADIUS_HOSTNAME, radius_server_info[RadiusConstans.RADIUS_HOSTNAME])
        system.aaa.radius.set_hostname_password(radius_server_info[RadiusConstans.RADIUS_HOSTNAME], radius_server_info[RadiusConstans.RADIUS_PASSWORD])
        system.aaa.radius.set_hostname_auth_port(radius_server_info[RadiusConstans.RADIUS_HOSTNAME], radius_server_info[RadiusConstans.RADIUS_AUTH_PORT])
        system.aaa.radius.set_hostname_auth_type(radius_server_info[RadiusConstans.RADIUS_HOSTNAME], radius_server_info[RadiusConstans.RADIUS_AUTH_TYPE])
        if radius_server_info.get(RadiusConstans.RADIUS_TIMEOUT):
            system.aaa.radius.set_hostname_timeout(radius_server_info[RadiusConstans.RADIUS_HOSTNAME], radius_server_info[RadiusConstans.RADIUS_TIMEOUT], True, True)
        if radius_server_info.get(RadiusConstans.RADIUS_PRIORITY):
            system.aaa.radius.set_hostname_priority(radius_server_info[RadiusConstans.RADIUS_HOSTNAME], radius_server_info[RadiusConstans.RADIUS_PRIORITY], True, True)

    with allure.step("Validating configurations"):
        logging.info("Validating configurations")
        output = Tools.OutputParsingTool.parse_json_str_to_dictionary(system.aaa.radius.show_hostname(radius_server_info[RadiusConstans.RADIUS_HOSTNAME])).get_returned_value()
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
        dut_engine.run_cmd("sudo config aaa authentication failthrough enable")
        dut_engine.run_cmd("sudo config aaa authentication login radius local")
        dut_engine.run_cmd("sudo ln -s  /bin/bash /usr/bin/sonic-launch-shell")


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
            system.message.set("").verify_result(should_succeed=True)
        else:
            logging.info("User has monitor permissions and cannot set configurations")
            system.message.set("").verify_result(should_succeed=False)


def validate_all_radius_user_authorization_and_role(engines, users):
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
        validate_all_radius_user_authorization_and_role(engines, radius_server_info[RadiusConstans.RADIUS_SERVER_USERS])


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
        validate_all_radius_user_authorization_and_role(engines,
                                                        RadiusConstans.RADIUS_SERVERS_DICTIONARY[real_radius_servers_order[0]][RadiusConstans.RADIUS_SERVER_USERS])

    with allure.step("Testing Priority by connecting to switch using second real radius server credentials"):
        logging.info("Testing Priority by connecting to switch using second real radius server credentials")
        validate_all_radius_user_authorization_and_role(engines,
                                                        RadiusConstans.RADIUS_SERVERS_DICTIONARY[real_radius_servers_order[1]][RadiusConstans.RADIUS_SERVER_USERS])


def validate_failed_authentication_with_new_credentials(engines, username, password):
    '''
    @summary: in this helper function we want to validate authentication failure while using
    username and password credentials
    '''
    with allure.step("Validating failed authentication with new credentials, username: {}".format(username)):
        logging.info("Validating failed authentication with new credentials, username: {}".format(username))
        try:
            connect_to_switch_and_validate_role(engines, username, password)
            raise Exception("Was able to connect to switch with radius server credentials when we expected failure")
        except NetmikoAuthenticationException as err:
            if RadiusConstans.AUTHENTICATION_FAILURE_MESSAGE not in str(err):
                raise Exception("Was able to connect to switch with radius server credentials when we expected failure")
        finally:
            restore_original_engine_credentials(engines)


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
        validate_all_radius_user_authorization_and_role(engines, radius_server_info[RadiusConstans.RADIUS_SERVER_USERS])

    system = System()
    with allure.step("Configuring invalid auth-port and validating applied configurations"):
        invalid_port = Tools.RandomizationTool.select_random_value([i for i in range(SshConfigConsts.MIN_LOGIN_PORT, SshConfigConsts.MAX_LOGIN_PORT)],
                                                                   [int(radius_server_info[RadiusConstans.RADIUS_AUTH_PORT])]).get_returned_value()
        logging.info("Configuring invalid auth-port: {}".format(invalid_port))
        system.aaa.radius.set_hostname_auth_port(radius_server_info[RadiusConstans.RADIUS_HOSTNAME],
                                                 invalid_port, True, True)
        radius_server_user = radius_server_info[RadiusConstans.RADIUS_SERVER_USERS][0]
        validate_failed_authentication_with_new_credentials(engines,
                                                            username=radius_server_user[RadiusConstans.RADIUS_SERVER_USERNAME],
                                                            password=radius_server_user[RadiusConstans.RADIUS_SERVER_USER_PASSWORD])

    with allure.step("Configuring invalid password and validating applied configurations"):
        random_string = Tools.RandomizationTool.get_random_string(10)
        logging.info("Configuring invalid password: {}".format(random_string))
        system.aaa.radius.set_hostname_password(radius_server_info[RadiusConstans.RADIUS_HOSTNAME],
                                                random_string, True, True)
        radius_server_user = radius_server_info[RadiusConstans.RADIUS_SERVER_USERS][0]
        validate_failed_authentication_with_new_credentials(engines,
                                                            username=radius_server_user[RadiusConstans.RADIUS_SERVER_USERNAME],
                                                            password=radius_server_user[RadiusConstans.RADIUS_SERVER_USER_PASSWORD])
