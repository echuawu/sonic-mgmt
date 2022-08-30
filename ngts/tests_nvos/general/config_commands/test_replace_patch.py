import pytest
import allure
import os
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.constants.constants_nvos import SystemConsts, ConfigConsts, OutputFormat
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort


def test_replace_empty_file(engines):
    """
    Test flow:
        1. run nv set system hostname <new_hostname>
        2. create empty file <file.yaml>
        3. run nv config replace <file.yaml>
        4. run nv config diff save as diff_1
        5. verify diff_1 is empty
    """
    with allure.step('Run show system command and verify that each field has a value'):
        system = System()
        new_hostname_value = 'TestingConfigCmds1'
        with allure.step('set hostname to be {hostname} - without apply'.format(hostname=new_hostname_value)):
            system.set(new_hostname_value, engines.dut, SystemConsts.HOSTNAME, False)

        file_name = 'replace'
        file_type = 'yaml'
        file = create_empty_file(engines.dut, file_name, file_type)
        TestToolkit.GeneralApi[TestToolkit.tested_api].replace_config(engines.dut, file)

        diff_after_hostname_change = OutputParsingTool.parse_json_str_to_dictionary(
            NvueGeneralCli.diff_config(engines.dut)).get_returned_value()

        engines.dut.run_cmd('sudo rm {file}.{type}'.format(file=file_name, type=file_type))
        with allure.step('verify the pending list is empty'):
            assert diff_after_hostname_change == {}, "pending revision should be empty, replace command should replace the last revision with empty file"


def test_replace_positive(engines):
    """

    Test flow:
        - run nv set system hostname <new_hostname> without apply
        - run nv config diff -o=yaml and save as <file_1>
        - run nv system hostname <new_hostname_1> without apply
        - run nv set interface ib0 description <new_description>
        - run nv config diff save as <diff_1>
        - run nv config replace <file_1>
        - run nv config diff save as <diff_2>
        - run nv config apply
        - verify hostname = <new_hostname_1>
        - verify ib0 description is empty (default value)
        - run unset hostname + apply
    """
    with allure.step('Run nv config replace and verify that the pending list is changed'):
        system = System()

        first_hostname = 'TestingConfigCmds2'
        with allure.step('set hostname to be {hostname} - without apply'.format(hostname=first_hostname)):
            system.set(first_hostname, engines.dut, SystemConsts.HOSTNAME, False)

            diff_after_hostname_change = NvueGeneralCli.diff_config(engines.dut, output_type=OutputFormat.yaml)

        new_hostname_value = 'TestingConfigReplace'
        with allure.step('set hostname to be {hostname} - without apply'.format(hostname=new_hostname_value)):
            system.set(new_hostname_value, engines.dut, SystemConsts.HOSTNAME, False)

        ib0_port = MgmtPort('ib0')
        output_dictionary = OutputParsingTool.parse_show_interface_output_to_dictionary(
            ib0_port.show()).get_returned_value()
        current_description = output_dictionary['description']
        new_ib0_description = '"ib0description"'
        with allure.step('set ib0 description to be {description} - with apply'.format(
                description=new_ib0_description)):
            ib0_port.interface.description.set(value=new_ib0_description, apply=False).verify_result()

        file_name = 'replace'
        file_type = 'yaml'
        file = create_file_with_content(engines.dut, file_name, file_type, diff_after_hostname_change)
        TestToolkit.GeneralApi[TestToolkit.tested_api].replace_config(engines.dut, file)

        engines.dut.run_cmd('sudo rm {file}'.format(file=file))
        NvueGeneralCli.apply_config(engines.dut, True)
        with allure.step('verify the hostname is {hostname} and ib0 description is {description}'.format(hostname=new_hostname_value, description=new_ib0_description)):
            system_output = OutputParsingTool.parse_json_str_to_dictionary(system.show()).get_returned_value()
            ValidationTool.verify_field_value_in_output(system_output, SystemConsts.HOSTNAME,
                                                        first_hostname).verify_result()

            output_dictionary = OutputParsingTool.parse_show_interface_output_to_dictionary(
                ib0_port.show()).get_returned_value()

            ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                        field_name=ib0_port.interface.description.label,
                                                        expected_value=current_description).verify_result()
            system.unset(engines.dut)


def test_replace_negative(engines):
    """

    Test flow:
        - run nv set system hostname <new_hostname> without apply
        - run nv config diff -o=yaml and save as <file>
        - create invalid yaml files using <file>
        - run nv config replace <file_1> (Failed to parse YAML)
        - verify expected error message
        - run nv config replace <file_2> (NVUE file must contain a list of operation objects)
        - verify expected error message
        - run nv config replace <file_3> (bad path)
        - verify expected error message
    """
    system = System()

    file_name = 'replace'
    file_type = 'yaml'

    new_hostname_value = 'TestingConfigCmds3'
    with allure.step('set hostname to be {hostname} - without apply'.format(hostname=new_hostname_value)):
        system.set(new_hostname_value, engines.dut, SystemConsts.HOSTNAME, False)

        content = NvueGeneralCli.diff_config(engines.dut, output_type=OutputFormat.yaml)

    parsing_issue, bad_file = create_list_of_bad_files(engines.dut, file_name, file_type, content)
    output1 = engines.dut.run_cmd('nv config replace {file}'.format(file=parsing_issue))
    output2 = engines.dut.run_cmd('nv config replace {file}'.format(file=bad_file))

    engines.dut.run_cmd('sudo rm {file}'.format(file=parsing_issue))
    engines.dut.run_cmd('sudo rm {file}'.format(file=bad_file))

    assert 'Failed to parse YAML' in output1, 'the replace should fail'
    assert 'must contain a list of operation objects' in output2, 'the replace should fail'


def test_patch_empty_file(engines):
    """
    Test flow:
        1. run nv set system hostname <new_hostname>
        2. run nv config diff save as diff_1
        2. create empty file <file.yaml>
        3. run nv config patch <file.yaml>
        4. run nv config diff save as diff_2
        5. verify diff_1 is equal to diff_2
    """
    with allure.step('Run show system command and verify that each field has a value'):
        system = System()
        new_hostname_value = 'TestingConfigPatchCmds4'
        with allure.step('set hostname to be {hostname} - without apply'.format(hostname=new_hostname_value)):
            system.set(new_hostname_value, engines.dut, SystemConsts.HOSTNAME, False)

        diff_after_hostname_change = OutputParsingTool.parse_json_str_to_dictionary(
            NvueGeneralCli.diff_config(engines.dut)).get_returned_value()

        file_name = 'patch'
        file_type = 'yaml'
        file = create_empty_file(engines.dut, file_name, file_type)
        engines.dut.run_cmd('nv config patch {file}'.format(file=file))

        diff_after_patch = OutputParsingTool.parse_json_str_to_dictionary(NvueGeneralCli.diff_config(engines.dut)) \
            .get_returned_value()

        engines.dut.run_cmd('sudo rm {file}.{type}'.format(file=file_name, type=file_type))

        with allure.step('verify the pending file does not change'):
            assert diff_after_hostname_change == diff_after_patch, "pending revision should not change"


def test_patch_positive(engines):
    """

        Test flow:
            - run nv set system hostname <new_hostname> without apply
            - run nv config diff -o=yaml and save as <file_1>
            - run nv system hostname <new_hostname_1> without apply
            - run nv set interface ib0 description <new_description>
            - run nv config diff save as <diff_1>
            - run nv config replace <file_1>
            - run nv config diff save as <diff_2>
            - run nv config apply
            - verify hostname = <new_hostname_1>
            - verify ib0 description is empty (default value)
            - run unset hostname + apply
        - case1 : maybe it's good to create empty yaml file and verify the nv config diff is empty
        """
    with allure.step('Run nv config replace and verify that the pending list is changed'):
        system = System()

        first_hostname = 'TestingConfigCmds5'
        with allure.step('set hostname to be {hostname} - without apply'.format(hostname=first_hostname)):
            system.set(first_hostname, engines.dut, SystemConsts.HOSTNAME, False)

        diff_after_hostname_change = NvueGeneralCli.diff_config(engines.dut, output_type=OutputFormat.yaml)

        new_hostname_value = 'TestingConfigPatch'
        with allure.step('set hostname to be {hostname} - without apply'.format(hostname=new_hostname_value)):
            system.set(new_hostname_value, engines.dut, SystemConsts.HOSTNAME, False)

        ib0_port = MgmtPort('ib0')
        new_ib0_description = 'TEST'
        with allure.step('set ib0 description to be {description} - with apply'.format(
                description=new_ib0_description)):
            ib0_port.interface.description.set(value=new_ib0_description, apply=False).verify_result()

        file_name = 'patch'
        file_type = 'yaml'
        file = create_file_with_content(engines.dut, file_name, file_type, diff_after_hostname_change)
        TestToolkit.GeneralApi[TestToolkit.tested_api].patch_config(engines.dut, file)

        engines.dut.run_cmd('sudo rm {file}'.format(file=file))
        NvueGeneralCli.apply_config(engines.dut, True)
        with allure.step('verify the hostname is {hostname} and ib0 description is {description}'.format(hostname=new_hostname_value, description=new_ib0_description)):
            system_output = OutputParsingTool.parse_json_str_to_dictionary(system.show()).get_returned_value()
            ValidationTool.verify_field_value_in_output(system_output, SystemConsts.HOSTNAME,
                                                        first_hostname).verify_result()

            output_dictionary = OutputParsingTool.parse_show_interface_output_to_dictionary(
                ib0_port.show()).get_returned_value()

            ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                        field_name=ib0_port.interface.description.label,
                                                        expected_value=new_ib0_description).verify_result()
            ib0_port.interface.description.unset().verify_result()


def test_patch_negative(engines):
    """

    Test flow:
        - run nv set system hostname <new_hostname> without apply
        - run nv config diff -o=yaml and save as <file>
        - create invalid yaml files using <file>
        - run nv config replace <file_1> (Failed to parse YAML)
        - verify expected error message
        - run nv config replace <file_2> (NVUE file must contain a list of operation objects)
        - verify expected error message
        - run nv config replace <file_3> (bad path)
        - verify expected error message
    """
    system = System()

    file_name = 'patch'
    file_type = 'yaml'

    new_hostname_value = 'TestingConfigPatchCmds6'
    with allure.step('set hostname to be {hostname} - without apply'.format(hostname=new_hostname_value)):
        system.set(new_hostname_value, engines.dut, SystemConsts.HOSTNAME, False)

        content = NvueGeneralCli.diff_config(engines.dut, output_type=OutputFormat.yaml)

    parsing_issue, bad_file = create_list_of_bad_files(engines.dut, file_name, file_type, content)

    output1 = engines.dut.run_cmd('nv config replace {file}'.format(file=parsing_issue))
    output2 = engines.dut.run_cmd('nv config patch {file}'.format(file=bad_file))

    engines.dut.run_cmd('sudo rm {file}'.format(file=parsing_issue))
    engines.dut.run_cmd('sudo rm {file}'.format(file=bad_file))

    assert 'Failed to parse YAML' in output1, 'the replace should fail'
    assert 'must contain a list of operation objects' in output2, 'the replace should fail'


def create_empty_file(engine, file_name, file_type):
    with allure.step('create empty file {file_name}.{file_type}'.format(file_name=file_name, file_type=file_type)):
        f = '{file_name}.{file_type}'.format(file_name=file_name, file_type=file_type)
        engine.run_cmd('sudo touch ' + f)
        return f


def create_file_with_content(engine, file_name, file_type, content):
    with allure.step('creating yaml file with content'):
        engine.run_cmd('echo "{content}" | tee -a {file_name}.{file_type}'.format(content=content, file_type=file_type,
                                                                                  file_name=file_name))
        return '{file_name}.{file_type}'.format(file_type=file_type, file_name=file_name)


def create_list_of_bad_files(engine, file_name, file_type, content):
    """

    :param engine:
    :param file_name:
    :param file_type:
    :param content:
    :return:
    """
    with allure.step('create bad yaml files for replace and patch'):
        parssing_issue = create_file_with_content(engine, file_name + '_1', file_type, content + ' \n \n AAAAA')
        content = ' {}  '
        non_operation = create_file_with_content(engine, file_name + '_2', file_type, content)
        return parssing_issue, non_operation
