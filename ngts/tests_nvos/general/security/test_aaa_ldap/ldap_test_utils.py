import random
import time

from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.test_aaa_ldap.constants import LDAPConsts
from ngts.tests_nvos.infra.init_flow.init_flow import test_system_dockers, test_system_services
from ngts.tools.test_utils.allure_utils import allure_step


def configure_ldap(ldap_server_info):
    """
    @summary: configure ldap server from the given ldap_server_info
    :param ldap_server_info: a dict containing the ldap server info. e.g.:
    {
        "hostname" : <value>,
        "base-dn" : <value>,
        "bind-dn" " <value>,
        "bind-password" : <value>,
        "login-attribute" : <value>,
        "group-attribute" : <value>,
        "scope" : <value>,
        "port" : <value>,
        "timeout-bind" : <value>,
        "timeout" : <value>,
        "version" : <value>,
        "priority" : <value>
    }
    """
    system = System(None)

    with allure_step("Configuring ldap server"):
        if ldap_server_info.get(LDAPConsts.SCOPE):
            system.aaa.ldap.set_scope(scope=ldap_server_info[LDAPConsts.SCOPE])
        if ldap_server_info.get(LDAPConsts.BASE_DN):
            system.aaa.ldap.set_base_dn(base=ldap_server_info[LDAPConsts.BASE_DN])
        if ldap_server_info.get(LDAPConsts.BIND_DN):
            system.aaa.ldap.set_bind_dn(user=ldap_server_info[LDAPConsts.BIND_DN])
        if ldap_server_info.get(LDAPConsts.BIND_PASSWORD):
            system.aaa.ldap.set_bind_password(password=ldap_server_info[LDAPConsts.BIND_PASSWORD])
        if ldap_server_info.get(LDAPConsts.PORT):
            system.aaa.ldap.set_port(port=ldap_server_info[LDAPConsts.PORT])
        if ldap_server_info.get(LDAPConsts.TIMEOUT):
            system.aaa.ldap.set_timeout_search(timeout=ldap_server_info[LDAPConsts.TIMEOUT])
        if ldap_server_info.get(LDAPConsts.TIMEOUT_BIND):
            system.aaa.ldap.set_timeout_bind(timeout=ldap_server_info[LDAPConsts.TIMEOUT_BIND])
        if ldap_server_info.get(LDAPConsts.VERSION):
            system.aaa.ldap.set_version(version=ldap_server_info[LDAPConsts.VERSION])
        if ldap_server_info.get(LDAPConsts.PRIORITY):
            priority = int(ldap_server_info[LDAPConsts.PRIORITY])
        else:
            priority = LDAPConsts.DEFAULT_PRIORTIY
        system.aaa.ldap.hostname.set_priority(hostname=ldap_server_info[LDAPConsts.HOSTNAME],
                                              priority=priority,
                                              apply=True).verify_result()


def validate_ldap_configurations(ldap_server_info):
    """
    @summary: validate ldap server configurations same as the given ldap_server_info
    :param ldap_server_info: a dict containing the ldap server info. e.g.:
    {
        "hostname" : <value>,
        "base-dn" : <value>,
        "bind-dn" " <value>,
        "bind-password" : <value>,
        "login-attribute" : <value>,
        "group-attribute" : <value>,
        "scope" : <value>,
        "port" : <value>,
        "timeout-bind" : <value>,
        "timeout" : <value>,
        "version" : <value>,
        "priority" : <value>
    }
    """
    system = System(None)

    with allure_step("Validating the configuration of ldap to be the same as {}".format(ldap_server_info)):
        output = system.aaa.ldap.show()
        output = OutputParsingTool.parse_json_str_to_dictionary(output).get_returned_value()
        expected_field = [LDAPConsts.PORT, LDAPConsts.BASE_DN, LDAPConsts.BIND_DN,
                          LDAPConsts.LOGIN_ATTR,
                          LDAPConsts.TIMEOUT_BIND, LDAPConsts.TIMEOUT]
        expected_values = [ldap_server_info[LDAPConsts.PORT], ldap_server_info[LDAPConsts.BASE_DN],
                           ldap_server_info[LDAPConsts.BIND_DN], ldap_server_info[LDAPConsts.LOGIN_ATTR],
                           ldap_server_info[LDAPConsts.TIMEOUT_BIND], ldap_server_info[LDAPConsts.TIMEOUT],
                           ldap_server_info[LDAPConsts.VERSION]]
        ValidationTool.validate_fields_values_in_output(expected_fields=expected_field,
                                                        expected_values=expected_values,
                                                        output_dict=output).verify_result()
        output = system.aaa.ldap.hostname.show_hostname(hostname=ldap_server_info[LDAPConsts.HOSTNAME])
        output = OutputParsingTool.parse_json_str_to_dictionary(output).get_returned_value()
        expected_field = [LDAPConsts.PRIORITY]
        expected_values = [ldap_server_info[LDAPConsts.PRIORITY]]
        ValidationTool.validate_fields_values_in_output(expected_fields=expected_field,
                                                        expected_values=expected_values,
                                                        output_dict=output).verify_result()


def enable_ldap_feature(dut_engine):
    """
    @summary:
        in this function we want to enable the LDAP server functionality,
        in the current implementation we use sonic commands, once the nv commands
        are available we will change this function
    """
    with allure_step("Enabling LDAP by setting LDAP auth. method as first auth. method"):
        dut_engine.run_cmd("nv set system aaa authentication order ldap,local")
        dut_engine.run_cmd("nv set system aaa authentication fallback enabled")
        dut_engine.run_cmd("nv set system aaa authentication failthrough enabled")
        dut_engine.run_cmd("nv config apply -y")
        NVUED_SLEEP_FOR_RESTART = 4
        with allure_step("Sleeping {} secs for nvued to start the restart".format(NVUED_SLEEP_FOR_RESTART)):
            time.sleep(NVUED_SLEEP_FOR_RESTART)
        NvueGeneralCli.wait_for_nvos_to_become_functional(dut_engine)


def validate_services_and_dockers_availability(engines, devices):
    """
    @summary: validate all services and dockers are up configuring ldap
    """
    with allure_step("validating all services and dockers are up"):
        test_system_dockers(engines, devices)
        test_system_services(engines, devices)


def configure_ldap_and_validate(engines, ldap_server_list, devices):
    """
    @summary: in this function we will configure ldap servers in he ldap server list
    and validate the ldap configurations per server
    """
    enable_ldap_feature(engines.dut)

    for ldap_server_info in ldap_server_list:
        with allure_step("Configuring ldap server {}".format(ldap_server_info)):
            configure_ldap(ldap_server_info)

        with allure_step("Validating ldap server configurations"):
            validate_ldap_configurations(ldap_server_info)

    validate_services_and_dockers_availability(engines, devices)


def randomize_ldap_server():
    """
    @summary:
        in this function we randomize ldap server dictionary and return it.
        e.g. of return value:
        {
            "hostname" : <value>
        }
    """
    randomized_ldap_server_info = {
        "hostname": f"1.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}",
    }
    return randomized_ldap_server_info
