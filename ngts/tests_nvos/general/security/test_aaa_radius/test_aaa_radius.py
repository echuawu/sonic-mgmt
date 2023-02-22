import logging
import allure
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.test_aaa_radius.constants import RadiusConstans
from ngts.nvos_tools.infra.Tools import Tools
from ngts.tests_nvos.general.security.test_aaa_radius.conftest import clear_all_radius_configurations, restore_original_engine_credentials
from ngts.nvos_constants.constants_nvos import SystemConsts


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


def connect_to_switch_and_valiate_role(engines, username, password, role):
    '''
    @summary:
        in this helper function, we will connect to switch using username, password & port
        and validate user role configurationl
    '''
    with allure.step("Using username: {}, role: {}".format(username, role)):
        logging.info("Using username: {}, role: {}".format(username, role))
        engines.dut.update_credentials(username=username, password=password)

    system = System(None)
    SHOW_SYSTEM_VERSION_CMD = 'nv show system version'
    with allure.step("Running command: \'{}\'".format(SHOW_SYSTEM_VERSION_CMD)):
        logging.info("Running command: \'{}\'".format(SHOW_SYSTEM_VERSION_CMD))
        system.version.show()

    with allure.step("Validating role permission are as expected"):
        logging.info("Validating role permission are as expected")
        if role == SystemConsts.DEFAULT_USER_ADMIN:
            logging.info("User has admin permission and can set configurations")
            system.message.set("").verify_result(should_succeed=True)
        else:
            logging.info("User has monitor permission and cannot set configurations")
            system.message.set("").verify_result(should_succeed=False)


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
        try:
            for user_info in radius_server_info['users']:
                connect_to_switch_and_valiate_role(engines, user_info['username'], user_info['password'], user_info['role'])
        except Exception as err:
            logging.info("Got an exception while connection to switch and executing show command")
            raise err
        finally:
            restore_original_engine_credentials(engines)