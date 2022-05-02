#!/usr/bin/env python
import allure
import logging
import os
import time
import pytest
from ngts.helpers import system_helpers
from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon

logger = logging.getLogger()

ENV_COVERAGE_FILE = 'COVERAGE_FILE'
GCOV_DIR = '/sonic'
SOURCES_PATH = '/src/sonic_src.tar.gz'
GCOV_CONTAINERS_SONIC = ['swss', 'syncd']
GCOV_CONTAINERS_NVOS = ['swss-ibv0', 'syncd-ibv0']


@pytest.mark.disable_loganalyzer
@allure.title('Extract Python Coverage')
def test_extract_python_coverage(topology_obj, dest):
    """
    Extracts code coverage collected by the Coverage.py tool for Python scripts.
    Code coverage is extracted as .xml file, one for the main image and one for
    each Docker container.
    :param topology_obj: topology object fixture.
    :param dest: dest fixture, the directory in which to save the extracted coverage .xml files
    :raise AssertionError: in case of script failure.
    """
    try:
        engine = topology_obj.players['dut']['engine']
        cli_obj = topology_obj.players['dut']['cli']

        with allure.step('Get coverage file path'):
            coverage_file = cli_obj.general.echo(f'${{{ENV_COVERAGE_FILE}}}')
            if not coverage_file:
                raise Exception('The system is not configured to collect code coverage.\n'
                                f'The environment variable {ENV_COVERAGE_FILE} is not defined.')
            logger.info(f'Coverage file path: {coverage_file}')

        with allure.step('Restart all system services to get coverage for running services'):
            cli_obj.general.systemctl_restart('sonic.target')
            system_helpers.wait_for_all_jobs_done(engine)

        coverage_dir = os.path.dirname(coverage_file)
        hostname = cli_obj.general.hostname()
        timestamp = int(time.time())
        coverage_xml_filename_prefix = f'coverage-{hostname}'
        with allure.step('Create coverage xml report for the host'):
            host_coverage_xml_file = os.path.join(coverage_dir, f'{coverage_xml_filename_prefix}-{timestamp}.xml')
            create_coverage_xml(cli_obj.general, coverage_file, host_coverage_xml_file)

        containers = cli_obj.general.get_running_containers_names()
        logger.info(f'Running Docker containers: {containers}')
        for container in containers:
            with allure.step(f'Create coverage xml report for {container} container'):
                docker_exec_engine = system_helpers.PrefixEngine(engine, f'docker exec {container}')
                container_coverage_xml_file = os.path.join(coverage_dir, f'{coverage_xml_filename_prefix}-{timestamp}-{container}.xml')
                create_coverage_xml(GeneralCliCommon(docker_exec_engine), coverage_file, container_coverage_xml_file)
                coverage_xml_files = system_helpers.list_files(docker_exec_engine, coverage_dir, pattern=coverage_xml_filename_prefix)
                logger.info(f'Coverage xml files in {container} container: {coverage_xml_files}')
                for file in coverage_xml_files:
                    cli_obj.general.copy_from_docker(container, file, file)
                    cli_obj.general.rm(file, flags='-f')

        with allure.step(f'Copy coverage xml reports from the system to destination directory'):
            coverage_xml_files = system_helpers.list_files(engine, coverage_dir, pattern=coverage_xml_filename_prefix)
            logger.info(f'Coverage xml files on the system: {coverage_xml_files}')
            logger.info(f'Destination directory: {dest}')
            os.makedirs(dest, exist_ok=True)
            for file in coverage_xml_files:
                filename = os.path.basename(file)
                engine.copy_file(source_file=filename,
                                 dest_file=os.path.join(dest, filename),
                                 file_system=os.path.dirname(file),
                                 direction='get')
                cli_obj.general.rm(file, flags='-f')

    except Exception as err:
        raise AssertionError(err)


@pytest.mark.disable_loganalyzer
@allure.title('Extract GCOV Coverage')
def test_extract_gcov_coverage(topology_obj, dest, nvos):
    """
    Extracts code coverage collected by GCOV for C/C++ binaries that were
    compiled with GCOV flags.
    This is currently relevant for the core components: swss, syncd
    :param topology_obj: topology object fixture.
    :param dest: dest fixture, the directory in which to save the extracted coverage .xml files
    :raise AssertionError: in case of script failure.
    """
    try:
        engine = topology_obj.players['dut']['engine']
        cli_obj = topology_obj.players['dut']['cli']

        with allure.step('Check that sources exist on the switch'):
            cli_obj.general.ls(SOURCES_PATH, validate=True)

        with allure.step('Restart all system services to get coverage for running services'):
            cli_obj.general.systemctl_restart('sonic.target')
            system_helpers.wait_for_all_jobs_done(engine)

        sudo_engine = system_helpers.PrefixEngine(engine, 'sudo')
        sudo_cli_general = GeneralCliCommon(sudo_engine)
        containers = GCOV_CONTAINERS_NVOS if nvos else GCOV_CONTAINERS_SONIC
        logger.info(f'Containers with GCOV coverage: {containers}')
        logger.info(f'GCOV dir: {GCOV_DIR}')
        sudo_cli_general.mkdir(GCOV_DIR, flags='-p')
        hostname = sudo_cli_general.hostname()
        gcov_filename_prefix = f'gcov-{hostname}'
        with allure.step(f'Collect GCOV coverage from docker containers: {containers}'):
            for container in containers:
                collect_gcov_for_container(engine, cli_obj, container, gcov_filename_prefix)

        install_gcov(sudo_cli_general)
        timestamp = int(time.time())
        gcov_report_file = os.path.join(GCOV_DIR, f'{gcov_filename_prefix}-{timestamp}.xml')
        with allure.step(f'Combine GCOV JSON reports into a single report for SonarQube'):
            gcov_json_files = system_helpers.list_files(engine, GCOV_DIR, pattern=gcov_filename_prefix)
            logger.info(f'GCOV JSON files on the system: {gcov_json_files}')
            gcovr_flags = ' '.join(f'-a {gcov_json_file}' for gcov_json_file in gcov_json_files)
            gcovr_flags += f' --sonarqube -r {GCOV_DIR} -o {gcov_report_file}'
            sudo_cli_general.gcovr(flags=gcovr_flags)
            logger.info(f'Destination directory: {dest}')
            os.makedirs(dest, exist_ok=True)
            gcov_report_filename = os.path.basename(gcov_report_file)
            engine.copy_file(source_file=gcov_report_filename,
                             dest_file=os.path.join(dest, gcov_report_filename),
                             file_system=os.path.dirname(gcov_report_file),
                             direction='get')
            sudo_cli_general.rm(gcov_report_file, flags='-f')

    except Exception as err:
        raise AssertionError(err)


def install_gcov(cli_obj):
    with allure.step('Install required packages'):
        cli_obj.apt_update()
        cli_obj.apt_install('lcov', flags='-y')
        cli_obj.pip3_install('gcovr')


def create_coverage_xml(cli_general, coverage_file, coverage_xml_file):
    """
    Checks if coverage files exist, and if so combines them into an xml report.
    :param cli_general: GeneralCliCommon object
    :param coverage_file: the base name of coverage files.
        For example, with coverage_file='/var/lib/python/coverage/raw', coverage
        files created throughout system operation are located under
        /var/lib/python/coverage/, with names in the format 'raw.<hostname>.<pid>.<rand>'.
        Those coverage files are then combined into a single file (that is coverage_file),
        from which the xml report is generated.
    :param coverage_xml_file: the name of the xml report file to generate.
    """
    coverage_dir = os.path.dirname(coverage_file)
    coverage_basename = os.path.basename(coverage_file)
    coverage_files = system_helpers.list_files(cli_general.engine, coverage_dir, pattern=rf'{coverage_basename}\.')
    logger.info(f'Coverage files: {coverage_files}')
    if not coverage_files:
        logger.info('Coverage files not found, skipping...')
    else:
        cli_general.coverage_combine()
        cli_general.coverage_xml(coverage_xml_file)


def collect_gcov_for_container(engine, cli_obj, container, gcov_filename_prefix):
    """
    Collect GCOV coverage from a container running on the system, and creates a
    JSON report from it. This JSON report may later be combined with other JSON
    reports to a get full report.
    :param engine: an engine to the system
    :param cli_obj: dut cli object
    :param container: the container to work on
    :param gcov_filename_prefix: the prefix to give to the result filename
    """
    docker_exec_engine = system_helpers.PrefixEngine(engine, f'docker exec {container}')
    docker_cli_obj = GeneralCliCommon(docker_exec_engine)
    install_gcov(docker_cli_obj)
    with allure.step(f'Create GCOV JSON report for {container} container'):
        container_gcov_json_file = os.path.join(GCOV_DIR, f'{gcov_filename_prefix}-{container}.json')
        docker_cli_obj.tar(flags=f'xzf {SOURCES_PATH} -C {GCOV_DIR}')
        docker_cli_obj.gcovr(paths=GCOV_DIR, flags=f'--json-pretty -r {GCOV_DIR} -o {container_gcov_json_file}')
        cli_obj.general.copy_from_docker(container, container_gcov_json_file, container_gcov_json_file)
        docker_cli_obj.rm(container_gcov_json_file, flags='-f')
