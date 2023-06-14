import random
import time
import logging
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.constants import AuthConsts
from ngts.tests_nvos.general.security.security_test_utils import validate_users_authorization_and_role, \
    configure_authentication, validate_services_and_dockers_availability
from ngts.tests_nvos.general.security.test_aaa_ldap.constants import LdapConsts
from ngts.tests_nvos.infra.init_flow.init_flow import test_system_dockers, test_system_services
from ngts.tools.test_utils import allure_utils as allure


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

    with allure.step("Configuring ldap server"):
        if ldap_server_info.get(LdapConsts.SCOPE):
            system.aaa.ldap.set(LdapConsts.SCOPE, ldap_server_info[LdapConsts.SCOPE])
        if ldap_server_info.get(LdapConsts.BASE_DN):
            system.aaa.ldap.set(LdapConsts.BASE_DN, ldap_server_info[LdapConsts.BASE_DN])
        if ldap_server_info.get(LdapConsts.BIND_DN):
            system.aaa.ldap.set(LdapConsts.BIND_DN, ldap_server_info[LdapConsts.BIND_DN])
        if ldap_server_info.get(LdapConsts.BIND_PASSWORD):
            system.aaa.ldap.set(LdapConsts.BIND_PASSWORD, ldap_server_info[LdapConsts.BIND_PASSWORD])
        if ldap_server_info.get(LdapConsts.PORT):
            system.aaa.ldap.set(LdapConsts.PORT, ldap_server_info[LdapConsts.PORT])
        if ldap_server_info.get(LdapConsts.TIMEOUT):
            system.aaa.ldap.set(LdapConsts.TIMEOUT, ldap_server_info[LdapConsts.TIMEOUT])
        if ldap_server_info.get(LdapConsts.TIMEOUT_BIND):
            system.aaa.ldap.set(LdapConsts.TIMEOUT_BIND, ldap_server_info[LdapConsts.TIMEOUT_BIND])
        if ldap_server_info.get(LdapConsts.VERSION):
            system.aaa.ldap.set(LdapConsts.VERSION, ldap_server_info[LdapConsts.VERSION])
        if ldap_server_info.get(LdapConsts.PRIORITY):
            priority = int(ldap_server_info[LdapConsts.PRIORITY])
        else:
            priority = LdapConsts.DEFAULT_PRIORTIY
        system.aaa.ldap.hostname.set_priority(hostname=ldap_server_info[LdapConsts.HOSTNAME],
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

    with allure.step("Validating the configuration of ldap to be the same as {}".format(ldap_server_info)):
        output = system.aaa.ldap.show()
        output = OutputParsingTool.parse_json_str_to_dictionary(output).get_returned_value()
        expected_field = [LdapConsts.PORT, LdapConsts.BASE_DN, LdapConsts.BIND_DN,
                          LdapConsts.LOGIN_ATTR,
                          LdapConsts.TIMEOUT_BIND, LdapConsts.TIMEOUT]
        expected_values = [ldap_server_info[LdapConsts.PORT], ldap_server_info[LdapConsts.BASE_DN],
                           ldap_server_info[LdapConsts.BIND_DN], ldap_server_info[LdapConsts.LOGIN_ATTR],
                           ldap_server_info[LdapConsts.TIMEOUT_BIND], ldap_server_info[LdapConsts.TIMEOUT],
                           ldap_server_info[LdapConsts.VERSION]]
        ValidationTool.validate_fields_values_in_output(expected_fields=expected_field,
                                                        expected_values=expected_values,
                                                        output_dict=output).verify_result()
        output = system.aaa.ldap.hostname.show_hostname(hostname=ldap_server_info[LdapConsts.HOSTNAME])
        output = OutputParsingTool.parse_json_str_to_dictionary(output).get_returned_value()
        expected_field = [LdapConsts.PRIORITY]
        expected_values = [ldap_server_info[LdapConsts.PRIORITY]]
        ValidationTool.validate_fields_values_in_output(expected_fields=expected_field,
                                                        expected_values=expected_values,
                                                        output_dict=output).verify_result()


def enable_ldap_feature(engines, devices):
    """
    @summary:
        in this function we want to enable the LDAP server functionality,
        in the current implementation we use sonic commands, once the nv commands
        are available we will change this function
    """
    with allure.step("Enabling LDAP by setting LDAP auth. method as first auth. method"):
        configure_authentication(engines, devices, order=[AuthConsts.LDAP, AuthConsts.LOCAL], failthrough=LdapConsts.ENABLED, fallback=LdapConsts.ENABLED)


def configure_ldap_and_validate(engines, ldap_server_list, devices, should_validate_conf=True):
    """
    @summary: in this function we will configure ldap servers in he ldap server list
    and validate the ldap configurations per server
    """
    for ldap_server_info in ldap_server_list:
        with allure.step("Configuring ldap server {}".format(ldap_server_info)):
            configure_ldap(ldap_server_info)

        if should_validate_conf:
            with allure.step("Validating ldap server configurations"):
                validate_ldap_configurations(ldap_server_info)

    configure_authentication(engines, devices, order=[AuthConsts.LDAP, AuthConsts.LOCAL], failthrough=LdapConsts.ENABLED)
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


def configure_ldap_server(engines, ldap_obj, ldap_server_info):
    """
    @summary: Configure ldap server according to the given server information
    @param engines: engines object
    @param ldap_obj: Ldap object (under System.Aaa object)
    @param ldap_server_info: dictionary that holds information about the given server
    """
    with allure.step(f'Configure ldap server: {ldap_server_info[LdapConsts.HOSTNAME]}'):
        logging.info(f'Server details:\n{ldap_server_info}')

        with allure.step('Configure general settings to match the given server'):
            conf_to_set = {
                LdapConsts.PORT: ldap_server_info[LdapConsts.PORT],
                LdapConsts.BASE_DN: ldap_server_info[LdapConsts.BASE_DN],
                LdapConsts.BIND_DN: ldap_server_info[LdapConsts.BIND_DN],
                LdapConsts.GROUP_ATTR: ldap_server_info[LdapConsts.GROUP_ATTR],
                LdapConsts.LOGIN_ATTR: ldap_server_info[LdapConsts.LOGIN_ATTR],
                LdapConsts.BIND_PASSWORD: ldap_server_info[LdapConsts.BIND_PASSWORD],
                LdapConsts.TIMEOUT_BIND: ldap_server_info[LdapConsts.TIMEOUT_BIND],
                LdapConsts.TIMEOUT: ldap_server_info[LdapConsts.TIMEOUT],
                LdapConsts.VERSION: ldap_server_info[LdapConsts.VERSION]
            }
            configure_ldap_settings(engines, ldap_obj, conf_to_set)

        with allure.step('Configure the given server with its priority'):
            priority = int(ldap_server_info[LdapConsts.PRIORITY])
            ldap_obj.hostname.set_priority(hostname=ldap_server_info[LdapConsts.HOSTNAME], priority=priority,
                                           apply=True).verify_result()


def configure_ldap_encryption(engines, ldap_obj, encryption_mode):
    """
    @summary: Configure ldap settings according to the given encryption mode
    @param engines: engines object
    @param ldap_obj: Ldap object (under System.Aaa object)
    @param encryption_mode: in [NONE, START_TLS, SSL]
    """
    with allure.step(f'Configure ldap encryption: {encryption_mode}'):
        # todo: understand what conf needed for each encryption mode
        if encryption_mode == LdapConsts.TLS:
            configure_ldap_settings(engines, ldap_obj, ldap_conf={
                # LdapConsts.SSL: {
                # LdapConsts.SSL_MODE: LdapConsts.START_TLS,
                # LdapConsts.SSL_CERT_VERIFY: LdapConsts.ENABLED
                # }
            })
        elif encryption_mode == LdapConsts.SSL:
            configure_ldap_settings(engines, ldap_obj, ldap_conf={
                # LdapConsts.SSL: {
                # LdapConsts.SSL_MODE: LdapConsts.SSL,
                # LdapConsts.SSL_CERT_VERIFY: LdapConsts.ENABLED,
                # LdapConsts.SSL_PORT: 636
                # }
            })
        elif encryption_mode == LdapConsts.NONE:
            configure_ldap_settings(engines, ldap_obj, ldap_conf={
                # LdapConsts.SSL: {
                # LdapConsts.SSL_MODE: LdapConsts.NONE,  # todo: verify phase 2 defaults
                # LdapConsts.SSL_CERT_VERIFY: LdapConsts.DEFAULTS[LdapConsts.SSL_CERT_VERIFY],
                # LdapConsts.SSL_CA_LIST: LdapConsts.DEFAULTS[LdapConsts.SSL_CA_LIST],
                # LdapConsts.SSL_CIPHERS: LdapConsts.DEFAULTS[LdapConsts.SSL_CIPHERS],
                # LdapConsts.TLS_CRL_CHECK_FILE: LdapConsts.DEFAULTS[LdapConsts.TLS_CRL_CHECK_FILE],
                # LdapConsts.TLS_CRL_CHECK_STATE: LdapConsts.DEFAULTS[LdapConsts.TLS_CRL_CHECK_STATE],
                # LdapConsts.SSL_PORT: LdapConsts.DEFAULTS[LdapConsts.SSL_PORT]
                # }
            })


def configure_ldap_settings(engines, ldap_obj, ldap_conf):
    """
    @summary: Configure ldap settings according to the given desired configuration
        * Configuration example:
            if we want:
                - bind-dn = abc
                - auth-port = 123
                - ssl ssl-port = 456
                - tls mode = start-tls
            then configuration dictionary should be:
            {
                bind-dn: abc,
                auth-port: 123,
                ssl:    {
                            ssl-port: 456
                        },
                tls:    {
                            mode: start-tls
                        }
            }
    @param engines: engines object
    @param ldap_obj: ldap object
    @param ldap_conf: the desired ldap configuration (dictionary)
    """
    if not ldap_conf:
        return

    with allure.step('Set ldap configuration'):
        logging.info(f'Given configuration to set:\n{ldap_conf}')

        for key, value in ldap_conf.items():
            if key == LdapConsts.SSL:
                ssl_conf = ldap_conf[LdapConsts.SSL]
                for ssl_key, ssl_value in ssl_conf.items():
                    ssl_value = int(ssl_value) if ssl_value.isnumeric() else ssl_value
                    ldap_obj.ssl.set(ssl_key, ssl_value, apply=False).verify_result()
            elif key == LdapConsts.TLS:
                tls_conf = ldap_conf[LdapConsts.TLS]
                for tls_key, tls_value in tls_conf.items():
                    tls_value = int(tls_value) if tls_value.isnumeric() else tls_value
                    ldap_obj.tls.set(tls_key, tls_value, apply=False).verify_result()
            else:
                value = int(value) if value.isnumeric() else value
                ldap_obj.set(key, value, apply=False).verify_result()

        logging.info('Apply all changes')
        SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config, engines.dut, True)\
            .verify_result()
