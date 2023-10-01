
import logging

from typing import Dict
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.system.RemoteAaaResource import RemoteAaaResource
from ngts.tests_nvos.general.security.security_test_tools.generic_remote_aaa_testing.constants import *
from ngts.tests_nvos.general.security.security_test_tools.security_test_utils import configure_resource
from ngts.tools.test_utils import allure_utils as allure


def generic_aaa_set_unset_show(test_api, engines, remote_aaa_type: str, main_resource_obj: RemoteAaaResource,
                               confs: Dict[BaseComponent, dict],
                               hostname_conf: dict,
                               default_confs: Dict[BaseComponent, dict]):
    """
    @summary: Verify set, unset, show commands for remote AAA feature

        Steps:
        1. set general/global configurations
        2. set hostnames
            1- with default configuration
            2- with new configuration
        3. apply changes
        4. verify new configurations with show commands
            1- general configurations as required
            2- hostname1 configuration as default
            3- hostname2 configuration as required
        5. unset configurations
        6. verify default configuration
    @param test_api: run commands with NVUE / OpenApi
    @param engines: engines object
    @param remote_aaa_type: name of he remote Aaa type (tacacs, ldap, radius)
    @param main_resource_obj: BaseComponent object representing the feature resource
    @param confs: configurations to set
    @param hostname_conf: configuration for hostname2 (the non-default one)
    @param default_confs: default configurations
    """
    assert remote_aaa_type in RemoteAaaType.ALL_TYPES, f'{remote_aaa_type} is not one of {RemoteAaaType.ALL_TYPES}'

    TestToolkit.tested_api = test_api

    with allure.step('Set general configuration'):
        for resource, conf in confs.items():
            configure_resource(engines, resource, conf)

    with allure.step('Set hostnames'):
        hostname1 = '1.2.3.4'
        hostname2 = '2.3.4.5'
        main_resource_obj.hostname.set(hostname1)
        configure_resource(engines, main_resource_obj.hostname.hostname_id[hostname2], hostname_conf, apply=True)

    with allure.step('Verify general configurations'):
        for resource, expected_conf in confs.items():
            with allure.step(f'Verify {resource.get_resource_path()} configuration'):
                cur_conf = OutputParsingTool.parse_json_str_to_dictionary(resource.show()).get_returned_value()
                if RemoteAaaConsts.SECRET_FIELD[remote_aaa_type] in expected_conf.keys():
                    expected_conf[RemoteAaaConsts.SECRET_FIELD[remote_aaa_type]] = '*'
                ValidationTool.validate_fields_values_in_output(expected_fields=expected_conf.keys(),
                                                                expected_values=expected_conf.values(),
                                                                output_dict=cur_conf).verify_result()

    with allure.step('Verify hostnames exist in show output'):
        show_hostname_output = OutputParsingTool.parse_json_str_to_dictionary(
            main_resource_obj.hostname.show()).get_returned_value()
        ValidationTool.verify_field_exist_in_json_output(show_hostname_output, [hostname1, hostname2]).verify_result()

    with allure.step('Verify hostnames configurations'):
        with allure.step(f'Verify default configuration for hostname {hostname1}'):
            global_conf = OutputParsingTool.parse_json_str_to_dictionary(main_resource_obj.show()).get_returned_value()
            expected_conf = {
                key: 1 if key == AaaConsts.PRIORITY else global_conf[key]
                for key in hostname_conf.keys()
            }
            cur_hostname_conf = OutputParsingTool.parse_json_str_to_dictionary(
                main_resource_obj.hostname.hostname_id[hostname1].show()).get_returned_value()
            ValidationTool.validate_fields_values_in_output(expected_fields=expected_conf.keys(),
                                                            expected_values=expected_conf.values(),
                                                            output_dict=cur_hostname_conf).verify_result()

        with allure.step(f'Verify new configuration for hostname {hostname2}'):
            expected_conf = hostname_conf
            if RemoteAaaConsts.SECRET_FIELD[remote_aaa_type] in expected_conf.keys():
                expected_conf[RemoteAaaConsts.SECRET_FIELD[remote_aaa_type]] = '*'
            cur_hostname_conf = OutputParsingTool.parse_json_str_to_dictionary(
                main_resource_obj.hostname.hostname_id[hostname2].show()).get_returned_value()
            ValidationTool.validate_fields_values_in_output(expected_fields=expected_conf.keys(),
                                                            expected_values=expected_conf.values(),
                                                            output_dict=cur_hostname_conf).verify_result()

    if list(hostname_conf.keys()) != [AaaConsts.PRIORITY]:
        with allure.step(f'Clear hostname {hostname2} configuration'):
            for field in hostname_conf.keys():
                if field != AaaConsts.PRIORITY:
                    main_resource_obj.hostname.hostname_id[hostname2].unset(field).verify_result()
            SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config, engines.dut,
                                            True).verify_result()
        with allure.step(f'Verify default configuration for hostname {hostname2}'):
            global_conf = OutputParsingTool.parse_json_str_to_dictionary(main_resource_obj.show()).get_returned_value()
            expected_conf = {
                key: 2 if key == AaaConsts.PRIORITY else global_conf[key]
                for key in hostname_conf.keys()
            }
            cur_hostname_conf = OutputParsingTool.parse_json_str_to_dictionary(
                main_resource_obj.hostname.hostname_id[hostname2].show()).get_returned_value()
            ValidationTool.validate_fields_values_in_output(expected_fields=expected_conf.keys(),
                                                            expected_values=expected_conf.values(),
                                                            output_dict=cur_hostname_conf).verify_result()

    with allure.step('Unset configuration'):
        main_resource_obj.unset(apply=True).verify_result()

    with allure.step('Verify default configuration with show command'):
        for resource, expected_conf in default_confs.items():
            with allure.step(f'Verify default configuration for {resource.get_resource_path()}'):
                cur_conf = OutputParsingTool.parse_json_str_to_dictionary(resource.show()).get_returned_value()
                if RemoteAaaConsts.SECRET_FIELD[remote_aaa_type] in expected_conf.keys():
                    expected_conf[RemoteAaaConsts.SECRET_FIELD[remote_aaa_type]] = '*'
                ValidationTool.validate_fields_values_in_output(expected_fields=expected_conf.keys(),
                                                                expected_values=expected_conf.values(),
                                                                output_dict=cur_conf).verify_result()
