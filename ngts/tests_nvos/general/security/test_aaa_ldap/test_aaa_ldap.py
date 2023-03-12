import logging
import allure
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.test_aaa_ldap.constants import LDAPConsts
from ngts.tests_nvos.general.security.test_aaa_radius.test_aaa_radius import \
    validate_all_radius_user_authorization_and_role


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
    system = System()

    with allure.step("Configuring ldap server"):
        logging.info("Configuring ldap server")
        system.aaa.ldap.set_hostname(hostname=ldap_server_info[LDAPConsts.HOSTNAME])
        system.aaa.ldap.set_hostname_priority(hostname=ldap_server_info[LDAPConsts.HOSTNAME],
                                              priority=ldap_server_info[LDAPConsts.PRIORITY])
        system.aaa.ldap.set_scope(scope=ldap_server_info[LDAPConsts.SCOPE])
        system.aaa.ldap.set_base_dn(base=ldap_server_info[LDAPConsts.BASE_DN])
        system.aaa.ldap.set_bind_dn(user=ldap_server_info[LDAPConsts.BIND_DN])
        system.aaa.ldap.set_bind_password(password=ldap_server_info[LDAPConsts.BIND_PASSWORD])
        system.aaa.ldap.set_port(port=ldap_server_info[LDAPConsts.PORT])
        system.aaa.ldap.set_timeout_search(timeout=ldap_server_info[LDAPConsts.TIMEOUT])
        system.aaa.ldap.set_timeout_bind(timeout=ldap_server_info[LDAPConsts.TIMEOUT_BIND])
        system.aaa.ldap.set_version(version=3)
        system.aaa.ldap.set_state(state=LDAPConsts.LDAP_STATE_ENABLED, apply=True, ask_for_confirmation=True)


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
    system = System()

    with allure.step("Validating the configuration of ldap to be the same as {}".format(ldap_server_info)):
        logging.info("Validating the configuration of ldap to be the same as {}".format(ldap_server_info))
        output = system.aaa.ldap.show_hostname(hostname=ldap_server_info[LDAPConsts.HOSTNAME])
        output = OutputParsingTool.parse_json_str_to_dictionary(output).get_returned_value()
        expected_field = []  # TODO: add when the image is ready
        expected_values = []  # TODO: add when the image is ready
        ValidationTool.validate_fields_values_in_output(expected_fields=expected_field,
                                                        expected_values=expected_values,
                                                        output_dict=output).verify_result()


def test_ldap_basic_configurations(engines):
    '''
    @summary: in this test case we want to validate default ldap configurations.
    We will configure the default configurations and connect to device.
    '''
    ldap_server_info = LDAPConsts.PHYSICAL_LDAP_SERVER
    with allure.step("Configuring ldap server {}".format(ldap_server_info)):
        logging.info("Configuring ldap server {}".format(ldap_server_info))
        configure_ldap(ldap_server_info)

    with allure.step("Validating ldap server configurations"):
        logging.info("Validating ldap server configurations")
        validate_ldap_configurations(ldap_server_info)

    with allure.step("Validating ldap credentials"):
        logging.info("Validating ldap credentials")
        validate_all_radius_user_authorization_and_role(engines=engines,
                                                        users=ldap_server_info[LDAPConsts.USERS])
