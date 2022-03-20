#!/usr/bin/env python
import allure
import logging
import os
import pytest
import json
from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.helpers import system_helpers

logger = logging.getLogger()

SRC_DIR = os.path.dirname(os.path.realpath(__file__))
VALGRIND_CONFIG_PATH = os.path.join(SRC_DIR, 'valgrind_config')
VALGRIND_DIR = '/valgrind/'
VALGRIND_RUNNER = 'valgrind_runner'
VALGRIND_RUNNER_STAMP = '# VALGRIND_RUNNER'  # Used to differentiate between the wrapper and the original bin
VALGRIND_RUNNER_STAMP_LINE_NUM = 2  # The line number where the stamp is expected
VALGRIND_RUNNER_SRC_PATH = os.path.join(SRC_DIR, VALGRIND_RUNNER)
VALGRIND_RUNNER_PATH = os.path.join(VALGRIND_DIR, VALGRIND_RUNNER)

HOST_PROCESSES_KEY = 'host_processes'
DOCKER_PROCESSES_KEY = 'docker_processes'
NO_SERVICE_KEY = 'null'  # For processes that are not associated with any service


@pytest.fixture
def valgrind_config():
    """
    Reads the valgrind config file and returns the parsed dict.
    The valgrind config file is in json format. It describes the processes on
    which valgrind will run.
    Processes are either "host processes", which run directly on the host, or
    "docker processes", which run inside a Docker container.
    The processes are grouped by the service that uses them. When valgrind is
    installed/uninstalled, the corresponding service is restarted to apply.
    Host processes may be specified under the 'NO_SERVICE_KEY' ('null'), in
    which case no service will be restarted for them.
    """
    with open(VALGRIND_CONFIG_PATH) as valgrind_config_file:
        return json.load(valgrind_config_file)


@pytest.mark.disable_loganalyzer
@allure.title('Install valgrind')
def test_install_valgrind(topology_obj, valgrind_config):
    """
    Wraps the requested processes by a valgrind runner.
    It installs the valgrind package if needed, then replaces each specified
    binary with a wrapper script which runs the original binary with valgrind.
    :param topology_obj: topology object fixture.
    :param valgrind_config: valgrind_config fixture.
    :raise AssertionError: in case of script failure.
    """
    install_uninstall_valgrind(topology_obj, valgrind_config, install=True)


@pytest.mark.disable_loganalyzer
@allure.title('Uninstall valgrind')
def test_uninstall_valgrind(topology_obj, valgrind_config):
    """
    Returns the requested processes to run their original binaries.
    :param topology_obj: topology object fixture.
    :param valgrind_config: valgrind_config fixture.
    :raise AssertionError: in case of script failure.
    """
    install_uninstall_valgrind(topology_obj, valgrind_config, install=False)


def install_uninstall_valgrind(topology_obj, valgrind_config, install):
    """
    Installs/uninstalls valgrind for the requested processes.
    Install procedure wraps the requested processes by a valgrind runner.
    It installs the valgrind package if needed, then replaces each specified
    binary with a wrapper script which runs the original binary with valgrind.
    Uninstall procedure returns the requested processes to run their original binaries.
    :param topology_obj: topology object fixture.
    :param valgrind_config: valgrind_config fixture.
    :param install: boolean flag, whether to install (install=True) or uninstall (install=False)
    :raise AssertionError: in case of script failure.
    """
    try:
        engine = topology_obj.players['dut']['engine']
        sudo_engine = system_helpers.PrefixEngine(engine, 'sudo')

        if install:
            clear_valgrind_dir(sudo_engine)

            with allure.step(f'Copy valgrind runner onto host at {VALGRIND_RUNNER_PATH}'):
                engine.copy_file(source_file=VALGRIND_RUNNER_SRC_PATH,
                                 dest_file=os.path.basename(VALGRIND_RUNNER_PATH),
                                 file_system=os.path.dirname(VALGRIND_RUNNER_PATH),
                                 direction='put')

        services_to_restart = []

        host_processes = valgrind_config[HOST_PROCESSES_KEY]
        if host_processes:
            processes = flatten(host_processes.values())
            if install:
                with allure.step(f'Install valgrind on host processes: {processes}'):
                    install_valgrind(sudo_engine, processes)
            else:
                with allure.step(f'Uninstall valgrind on host processes: {processes}'):
                    uninstall_valgrind(sudo_engine, processes)

            services_to_restart.extend(service for service in host_processes.keys() if service != NO_SERVICE_KEY)

        docker_processes = valgrind_config[DOCKER_PROCESSES_KEY]
        if docker_processes:
            with allure.step('Verify containers are up: {}'.format(docker_processes.keys())):
                SonicGeneralCli().verify_dockers_are_up(engine, docker_processes.keys())

            for (container, processes) in docker_processes.items():
                docker_exec_engine = system_helpers.PrefixEngine(engine, f'docker exec {container}')
                if install:
                    clear_valgrind_dir(docker_exec_engine)

                    with allure.step(f'Copy valgrind runner into {container} container at {VALGRIND_RUNNER_PATH}'):
                        SonicGeneralCli().copy_to_docker(engine, container, VALGRIND_RUNNER_PATH, VALGRIND_RUNNER_PATH)

                    with allure.step(f'Install valgrind on {container} container processes: {processes}'):
                        install_valgrind(docker_exec_engine, processes)
                else:
                    with allure.step(f'Uninstall valgrind on {container} container processes: {processes}'):
                        uninstall_valgrind(docker_exec_engine, processes)

            services_to_restart.extend(docker_processes.keys())

        restart_services(engine, services_to_restart)

        if docker_processes:
            with allure.step('Verify containers are up: {}'.format(docker_processes.keys())):
                SonicGeneralCli().verify_dockers_are_up(engine, docker_processes.keys())

    except Exception as err:
        raise AssertionError(err)


def flatten(l):
    """
    Flattens a list of lists
    :param l: a list of lists, e.g. [[1, 2], [3, 4], [5]]
    :return: the flattened list, e.g. [1, 2, 3, 4, 5]
    """
    return [item for sublist in l for item in sublist]


def clear_valgrind_dir(engine):
    """
    Clears the valgrind dir.
    :param engine: the engine to use, may use a PrefixEngine with prefix 'sudo'
        to act on the host, or with prefix 'docker exec <container>'
        to act on a Docker container.
    """
    with allure.step(f'Clear valgrind dir at {VALGRIND_DIR}'):
        GeneralCliCommon.rm(engine, VALGRIND_DIR, flags='-rf')
        GeneralCliCommon.mkdir(engine, VALGRIND_DIR, flags='-p')
        GeneralCliCommon.chmod_by_mode(engine, VALGRIND_DIR, '777', flags='-R')


def install_valgrind_package(engine):
    """
    Installs valgrind package if it is not already installed.
    :param engine: the engine to use.
    """
    with allure.step("Install valgrind package"):
        if GeneralCliCommon.which(engine, 'valgrind'):
            logger.info('Valgrind package is already installed, skipping...')
        else:
            GeneralCliCommon.apt_update(engine)
            GeneralCliCommon.apt_install(engine, 'valgrind', '-y')
            get_process_path(engine, 'valgrind')  # sanity check


def get_process_path(engine, process):
    """
    Returns the absolute path of a process, found by the 'which' command.
    :param engine: the engine to use.
    :param process: the process of which to get the absolute path.
    :return: the absolute path of the process.
    :raise Exception: if the process was not found.
    """
    path = GeneralCliCommon.which(engine, process)
    if not path:
        raise Exception(f'Process {process} not found')
    return path


def install_valgrind(engine, processes):
    """
    Installs the valgrind package, and wraps processes with the valgrind runner.
    :param engine: the engine to use, may use a PrefixEngine with prefix 'sudo'
        to act on host processes, or with prefix 'docker exec <container>'
        to act on processes that run in a Docker container.
    :param processes: the list of processes to wrap with the valgrind runner.
    """
    install_valgrind_package(engine)

    with allure.step(f'Install valgrind for processes: {processes}'):
        for process in processes:
            process_path = get_process_path(engine, process)

            if is_valgrind_installed_for_process(engine, process_path):
                logger.info(f'Valgrind is already installed for process {process}, skipping...')
            else:
                new_process_path = f'{process_path}.bin'
                GeneralCliCommon.mv(engine, process_path, new_process_path)
                GeneralCliCommon.cp(engine, VALGRIND_RUNNER_PATH, process_path)
                GeneralCliCommon.chown_by_ref_file(engine, process_path, new_process_path)
                GeneralCliCommon.chmod_by_ref_file(engine, process_path, new_process_path)
                if not is_valgrind_installed_for_process(engine, process_path):
                    raise Exception(f'Failed to install valgrind for process {process}')


def uninstall_valgrind(engine, processes):
    """
    Returns the processes to run their original binaries.
    :param engine: the engine to use, may use a PrefixEngine with prefix 'sudo'
        to act on host processes, or with prefix 'docker exec <container>'
        to act on processes that run in a Docker container.
    :param processes: the list of processes to return to their original binaries.
    """
    with allure.step(f'Uninstall valgrind for processes: {processes}'):
        for process in processes:
            process_path = get_process_path(engine, process)

            if not is_valgrind_installed_for_process(engine, process_path):
                logger.info(f'Process {process} already uses its original binary, skipping...')
            else:
                orig_process_path = get_process_path(engine, f'{process_path}.bin')
                GeneralCliCommon.mv(engine, orig_process_path, process_path)
                if is_valgrind_installed_for_process(engine, process_path):
                    raise Exception(f'Failed to uninstall valgrind for process {process}')


def is_valgrind_installed_for_process(engine, process_path):
    """
    Checks if valgrind is installed for a process. This is done by looking for
    a unique and well-known stamp which exists only in the valgrind runner.
    :param engine: the engine to use.
    :param process_path: the path to the process.
    :return: True if valgrind is installed for the process, False otherwise.
    """
    return VALGRIND_RUNNER_STAMP == GeneralCliCommon.sed(engine, process_path, f'{VALGRIND_RUNNER_STAMP_LINE_NUM}q;d')


def restart_services(engine, services_to_restart):
    """
    Restart system services using service stop and start commands.
    We use explicit stop and start commands instead of a restart command, and
    we do it on each service one by one, to avoid bugs that may cause a
    "Job for <x>.service canceled" message to be printed.
    :param engine: the engine to use.
    :param services_to_restart: a list of services to restart
    """
    if services_to_restart:
        with allure.step(f'Restart system services: {services_to_restart}'):
            for service in services_to_restart:
                GeneralCliCommon.stop_service(engine, service)
                system_helpers.wait_for_all_jobs_done(engine)

            for service in services_to_restart:
                GeneralCliCommon.start_service(engine, service)
                system_helpers.wait_for_all_jobs_done(engine)
