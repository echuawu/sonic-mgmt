from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.constants.constants_nvos import SystemConsts
import allure
import logging
import pytest

logger = logging.getLogger()


@pytest.mark.general
def test_techsupport_folder_name(engines):
    """
    Test flow:
        1. get time
        2. run nv action generate system tech-support
        3. validate the tar.gz name is /var/dump/nvos_dump_<hostname>_<date>_<time>.tar.gz
    """
    with allure.step('Run nv action generate system tech-support and validate the tech-support name'):
        system = System(None)
        output_dictionary_before = OutputParsingTool.parse_show_system_techsupport_output_to_dictionary(
            system.techsupport.show()).get_returned_value()
        tech_support_folder = system.techsupport.action_generate()
        validate_techsupport_folder_name(system, tech_support_folder)
        output_dictionary_after = OutputParsingTool.parse_show_system_techsupport_output_to_dictionary(
            system.techsupport.show()).get_returned_value()

        cleanup_techsupport(engines.dut, output_dictionary_before, output_dictionary_after)


@pytest.mark.general
def test_techsupport_with_dockers_down(engines, dockers_list=['ib-utils']):
    """
    Test flow:
        1. run sudo systemctl stop ib-utils
        2. run nv action generate system tech-support
        3. validate it's working as expected
    """
    with allure.step('Run nv action generate system tech-support while at least one docker is down'):
        system = System(None)
        for docker in dockers_list:
            engines.dut.run_cmd('sudo systemctl stop {docker}'.format(docker=docker))
        tech_support_folder = system.techsupport.action_generate()
    with allure.step('validate commands works as expected'):
        assert '/var/dump/nvos_dump' in tech_support_folder, "{err}".format(err=tech_support_folder)

    cleanup_techsupport(engines.dut, [], [tech_support_folder])


@pytest.mark.general
def test_techsupport_expected_files(engines, devices):
    """
    Run nv show system tech-support files command and verify the required fields are exist
    command: nv show system tech-support files

    Test flow:
        1. get_expected dummy files per device
        2. get new files after configurations
        3. run nv action generate system tech-support
        4. extract result validate all files as expected
        5. select random port and config state
        6. apply
        7. run nv action generate system tech-support
        8. extract result validate the last config file exist
    """
    with allure.step('Run nv action generate system tech-support and validate dump files'):
        system = System(None)
        tech_support_folder = system.techsupport.action_generate()
        techsupport_files_list = get_techsupport_dump_files_names(engines.dut, tech_support_folder)
    with allure.step('validate dump files'):
        verify_techsupport_dump_files(devices.dut, techsupport_files_list)

    cleanup_techsupport(engines.dut, [], [tech_support_folder])


def validate_techsupport_folder_name(system, tech_support_folder):
    """
    Test flow:
        1. run nv show system
        2. get the hosname value
        3. validate the tar.gz name is /var/dump/nvos_dump_<hostname>_<time_now>.tar.gz
    """
    with allure.step('Check that tech-support name is as expected :/var/dump/nvos_dump_<hostname>_<time_now>.tar.gz'):
        system_output = OutputParsingTool.parse_json_str_to_dictionary(system.show()).get_returned_value()
        hostname = system_output[SystemConsts.HOSTNAME]
        assert '/var/dump/nvos_dump_' + hostname in tech_support_folder, 'the tech-support should be under var dump ' \
                                                                         'and includes hostname'


def get_techsupport_dump_files_names(engine, techsupport):
    """
    :param engine:
    :param techsupport: the techsupport .tar.gz name
    :return: list of the fump files in the tech-support
    """
    with allure.step('Get all tech-support dump files'):
        engine.run_cmd('sudo tar -xf ' + techsupport + ' -C /var/dump')
        folder_name = techsupport.replace('.tar.gz', "")
        output = engine.run_cmd('ls ' + folder_name + '/dump')
        engine.run_cmd('sudo rm -rf ' + folder_name)
        return output.split()


def verify_techsupport_dump_files(device, files_list):
    """
    :param files_list: list of dump files
    :param device:
    :return:
    """
    files = [file for file in device.constants.dump_files if file not in files_list]
    assert len(files) == 0, "the next files are missed {files}".format(files=files)
    files = [file for file in files_list if file not in device.constants.dump_files]
    if len(files) != 0:
        logger.warning("the next files are in the dump folder but not in our check list {files}".format(files=files))


def cleanup_techsupport(engine, before, after):
    new_folders = [file for file in after if file not in before]
    for dump in new_folders:
        engine.run_cmd('sudo rm -rf ' + dump)
