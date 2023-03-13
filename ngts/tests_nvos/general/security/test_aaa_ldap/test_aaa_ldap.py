import logging
import allure
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.test_aaa_ldap.constants import LDAPConsts
from ngts.tests_nvos.general.security.test_aaa_radius.test_aaa_radius import \
    validate_users_authorization_and_role
from ngts.tests_nvos.general.security.test_aaa_ldap.conftest import remove_ldap_configurations


def configure_ldap(ldap_server_info):
    '''
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
    '''
    system = System(None)

    with allure.step("Configuring ldap server"):
        logging.info("Configuring ldap server")
        system.aaa.ldap.set_hostname(hostname=ldap_server_info[LDAPConsts.HOSTNAME], apply=True)
        if ldap_server_info.get(LDAPConsts.PRIORITY):
            system.aaa.ldap.set_hostname_priority(hostname=ldap_server_info[LDAPConsts.HOSTNAME],
                                                  priority=ldap_server_info[LDAPConsts.PRIORITY], apply=True)
        if ldap_server_info.get(LDAPConsts.SCOPE):
            system.aaa.ldap.set_scope(scope=ldap_server_info[LDAPConsts.SCOPE], apply=True)
        if ldap_server_info.get(LDAPConsts.BASE_DN):
            system.aaa.ldap.set_base_dn(base=ldap_server_info[LDAPConsts.BASE_DN], apply=True)
        if ldap_server_info.get(LDAPConsts.BIND_DN):
            system.aaa.ldap.set_bind_dn(user=ldap_server_info[LDAPConsts.BIND_DN], apply=True)
        if ldap_server_info.get(LDAPConsts.BIND_PASSWORD):
            system.aaa.ldap.set_bind_password(password=ldap_server_info[LDAPConsts.BIND_PASSWORD], apply=True)
        if ldap_server_info.get(LDAPConsts.PORT):
            system.aaa.ldap.set_port(port=ldap_server_info[LDAPConsts.PORT], apply=True)
        if ldap_server_info.get(LDAPConsts.TIMEOUT):
            system.aaa.ldap.set_timeout_search(timeout=ldap_server_info[LDAPConsts.TIMEOUT], apply=True)
        if ldap_server_info.get(LDAPConsts.TIMEOUT_BIND):
            system.aaa.ldap.set_timeout_bind(timeout=ldap_server_info[LDAPConsts.TIMEOUT_BIND], apply=True)
        if ldap_server_info.get(LDAPConsts.VERSION):
            system.aaa.ldap.set_version(version=ldap_server_info[LDAPConsts.VERSION], apply=True)


def validate_ldap_configurations(ldap_server_info):
    '''
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
    '''
    system = System(None)

    with allure.step("Validating the configuration of ldap to be the same as {}".format(ldap_server_info)):
        logging.info("Validating the configuration of ldap to be the same as {}".format(ldap_server_info))
        output = system.aaa.ldap.show_hostname(hostname=ldap_server_info[LDAPConsts.HOSTNAME])
        output = OutputParsingTool.parse_json_str_to_dictionary(output).get_returned_value()
        expected_field = []  # TODO: add when the image is ready
        expected_values = []  # TODO: add when the image is ready
        ValidationTool.validate_fields_values_in_output(expected_fields=expected_field,
                                                        expected_values=expected_values,
                                                        output_dict=output).verify_result()


def enable_ldap_feature(dut_engine):
    '''
    @summary:
        in this function we want to enable the LDAP server functionality,
        in the current implementation we use sonic commands, once the nv commands
        are available we will change this function
    '''
    with allure.step("Enabling LDAP by setting LDAP auth. method as first auth. method"):
        logging.info("Enabling LDAP by setting LDAP auth. method as first auth. method")
        dut_engine.run_cmd("nv set system aaa authentication order ldap,local")
        dut_engine.run_cmd("nv set system aaa authentication fallback enabled")
        dut_engine.run_cmd("nv set system aaa authentication failthrough enabled")
        dut_engine.run_cmd("nv config apply -y")


def configure_ldap_and_validate(engines, ldap_server_list):
    '''
    @summary: in this function we will configure ldap servers in he ldap server list
    and validate the ldap configurations per server
    '''
    enable_ldap_feature(engines.dut)

    for ldap_server_info in ldap_server_list:
        with allure.step("Configuring ldap server {}".format(ldap_server_info)):
            logging.info("Configuring ldap server {}".format(ldap_server_info))
            configure_ldap(ldap_server_info)

        with allure.step("Validating ldap server configurations"):
            logging.info("Validating ldap server configurations")
            validate_ldap_configurations(ldap_server_info)


def test_ldap_basic_configurations(engines, remove_ldap_configurations):
    '''
    @summary: in this test case we want to validate default ldap configurations.
    We will configure the default configurations and connect to device.
    '''
    ldap_server_info = LDAPConsts.PHYSICAL_LDAP_SERVER
    configure_ldap_and_validate(engines, ldap_server_list=[ldap_server_info])

    with allure.step("Validating ldap credentials"):
        logging.info("Validating ldap credentials")
        validate_users_authorization_and_role(engines=engines, users=ldap_server_info[LDAPConsts.USERS])


def test_ldap_priority_and_fallback_functionality(engines, remove_ldap_configurations):
    ''''
    @summary: in this test case we want to validate the functionality of the priority
    and fallback, we will configure 2 ldap servers and then connect through the credentials
    found only in the first server and connect through credentials in the second server only
    and we are testing the local credentials
    '''
    configure_ldap_and_validate(engines, ldap_server_list=LDAPConsts.LDAP_SERVERS_LIST)

    with allure.step("Validating first ldap server credentials"):
        logging.info("Validating first ldap server credentials")
        first_ldap_server_users = LDAPConsts.LDAP_SERVERS_LIST[0][LDAPConsts.USERS]
        validate_users_authorization_and_role(engines=engines, users=first_ldap_server_users)

    with allure.step("Validating second ldap server credentials"):
        logging.info("Validating second ldap server credentials")
        second_ldap_server_users = LDAPConsts.LDAP_SERVERS_LIST[0][LDAPConsts.USERS]
        validate_users_authorization_and_role(engines=engines, users=second_ldap_server_users)
