#!/usr/bin/env python
import allure
import logging
import os
import time
import pytest
from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.helpers import system_helpers

logger = logging.getLogger()

ENV_COVERAGE_FILE = 'COVERAGE_FILE'


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

        with allure.step('Get coverage file path'):
            coverage_file = GeneralCliCommon.echo(engine, f'${{{ENV_COVERAGE_FILE}}}')
            if not coverage_file:
                raise Exception('The system is not configured to collect code coverage.\n'
                                f'The environment variable {ENV_COVERAGE_FILE} is not defined.')
            logger.info(f'Coverage file path: {coverage_file}')

        with allure.step('Restart all system services to get coverage for running services'):
            GeneralCliCommon.systemctl_restart(engine, 'sonic.target')
            system_helpers.wait_for_all_jobs_done(engine)

        coverage_dir = os.path.dirname(coverage_file)
        hostname = GeneralCliCommon.hostname(engine)
        timestamp = int(time.time())
        coverage_xml_filename_prefix = f'coverage-{hostname}'
        with allure.step('Create coverage xml report for the host'):
            host_coverage_xml_file = os.path.join(coverage_dir, f'{coverage_xml_filename_prefix}-{timestamp}.xml')
            create_coverage_xml(engine, coverage_file, host_coverage_xml_file)

        containers = GeneralCliCommon.get_running_containers_names(engine)
        logger.info(f'Running Docker containers: {containers}')
        for container in containers:
            with allure.step(f'Create coverage xml report for {container} container'):
                docker_exec_engine = system_helpers.PrefixEngine(engine, f'docker exec {container}')
                container_coverage_xml_file = os.path.join(coverage_dir, f'{coverage_xml_filename_prefix}-{timestamp}-{container}.xml')
                create_coverage_xml(docker_exec_engine, coverage_file, container_coverage_xml_file)
                coverage_xml_files = system_helpers.list_files(docker_exec_engine, coverage_dir, pattern=coverage_xml_filename_prefix)
                logger.info(f'Coverage xml files in {container} container: {coverage_xml_files}')
                for file in coverage_xml_files:
                    SonicGeneralCli().copy_from_docker(engine, container, file, file)
                    GeneralCliCommon.rm(docker_exec_engine, file, flags='-f')

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
                GeneralCliCommon.rm(engine, file, flags='-f')

    except Exception as err:
        raise AssertionError(err)


def create_coverage_xml(engine, coverage_file, coverage_xml_file):
    """
    Checks if coverage files exist, and if so combines them into an xml report.
    :param engine: the engine to use
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
    coverage_files = system_helpers.list_files(engine, coverage_dir, pattern=rf'{coverage_basename}\.')
    logger.info(f'Coverage files: {coverage_files}')
    if not coverage_files:
        logger.info('Coverage files not found, skipping...')
    else:
        GeneralCliCommon.coverage_combine(engine)
        GeneralCliCommon.coverage_xml(engine, coverage_xml_file)
