import logging
import os
import re

import pytest
import time
from datetime import datetime
from ngts.constants.constants import LinuxConsts
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.opensm.OpenSmTool import OpenSmTool
from ngts.nvos_constants.constants_nvos import SystemConsts, HealthConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType, NvosConst
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.tests_nvos.system.clock.ClockTools import ClockTools
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort
from ngts.nvos_tools.cli_coverage.operation_time import OperationTime
from ngts.tools.test_utils import allure_utils as allure
from infra.tools.redmine.redmine_api import is_redmine_issue_active

logger = logging.getLogger()

running_dockers = {}
KEEP_ALL_CONFIG = "keep-all-config"
KEEP_ONLY_FILES = "only-files"
KEEP_BASIC = "keep basic"


@pytest.mark.system
@pytest.mark.checklist
@pytest.mark.reset_factory
@pytest.mark.nvos_build
def test_reset_factory_without_params(engines, devices, topology_obj, platform_params):
    """
    Validate reset factory without params cleanup done as expected

        Test flow:
            1. set description to ib ports:
                - set, apply and save configuration
                - set and apply
                - set
            2. Validate ports description
            3. Add data
            4. Run reset factory without params
            5. After system is up again, verify the cleanup done successfully
            6. Verify the setup is functional:
                6.1.	Start openSM
                6.2.	Run several show commands
                6.3.    Run set command & apply
    """
    try:
        with allure.step("Get current time"):
            current_time = get_current_time(engines)

        with allure.step('Create System object'):
            system = System()
            machine_type = platform_params['filtered_platform']

        if machine_type != 'MQM9520':
            with allure.step('Validate health status is OK'):
                system.validate_health_status(HealthConsts.OK)
                last_status_line = system.health.history.retry_get_health_history_file_summary_line()

        with allure.step('Set description to ib ports'):
            logger.info("Set description to ib ports")
            description = "test_reset_factory_without_params"
            ports = Tools.RandomizationTool.select_random_ports(requested_ports_state=None,
                                                                num_of_ports_to_select=3).get_returned_value()
            apply_and_save_port = ports[0]
            just_apply_port = ports[1]
            not_apply_port = ports[2]

        with allure.step('Set and apply description to ib port, save config after it'):
            logger.info("Set and apply description to ib port, save config after it")
            apply_and_save_port.ib_interface.set(NvosConst.DESCRIPTION, description, apply=True).verify_result()
            TestToolkit.GeneralApi[TestToolkit.tested_api].save_config(engines.dut)
            NvueGeneralCli.save_config(engines.dut)
        with allure.step('Set and apply description to ib port'):
            logger.info("Set and apply description to ib port")
            just_apply_port.ib_interface.set(NvosConst.DESCRIPTION, description, apply=True).verify_result()
        with allure.step('Set description to ib port'):
            logger.info("Set description to ib port")
            not_apply_port.ib_interface.set(NvosConst.DESCRIPTION, description, apply=False).verify_result()
        with allure.step('Validate ports description'):
            logger.info("Validate ports description")
            _validate_port_description(engines.dut, apply_and_save_port, description)
            _validate_port_description(engines.dut, just_apply_port, description)
            _validate_port_description(engines.dut, not_apply_port, "")

        with allure.step("Add data before reset factory"):
            username = _add_verification_data(engines.dut, system)

        with allure.step("Get current time"):
            update_timezone(system)
            current_time = get_current_time(engines)

        with allure.step("Run reset factory without params"):
            execute_reset_factory(engines, system, "", current_time)

        update_timezone(system)

        if machine_type != 'MQM9520':
            with allure.step("Validate health status and report"):
                _validate_health_status_report(system, last_status_line)

        with allure.step("Verify description has been deleted"):
            _validate_port_description(engines.dut, apply_and_save_port, "")
            _validate_port_description(engines.dut, just_apply_port, "")
            _validate_port_description(engines.dut, not_apply_port, "")

    finally:
        with allure.step("Verify the cleanup done successfully"):
            _verify_cleanup_done(engines.dut, current_time, system, username)

        with allure.step("Verify the setup is functional"):
            _verify_the_setup_is_functional(system, engines)


@pytest.mark.system
@pytest.mark.checklist
@pytest.mark.reset_factory
def test_reset_factory_keep_basic(engines):
    """
    Validate reset factory with keep basic param cleanup done as expected

        Test flow:
            1. set description to eth0 port:
                - set, apply and save configuration
                - set and apply
                - set
            2. Validate ports description
            3. Add data
            4. Run reset factory with keep basic param
            5. After system is up again, verify the cleanup done successfully
            6. Verify the setup is functional:
                6.1.	Start openSM
                6.2.	Run several show commands
                6.3.    Run set command & apply
    """
    try:
        with allure.step('Create System object'):
            system = System()

        # pre-init current time
        date_time_str = engines.dut.run_cmd("date").split(" ", 1)[1]
        current_time = datetime.strptime(date_time_str, '%d %b %Y %H:%M:%S %p %Z')

        with allure.step('Validate health status is OK'):
            logger.info("Validate health status is OK")
            system.validate_health_status(HealthConsts.OK)
            last_status_line = system.health.history.retry_get_health_history_file_summary_line()

        with allure.step('Set description to eth0 port'):
            logger.info("Set description to eth0 port")
            mgmt_port = MgmtPort('eth0')
            mgmt_port.interface.set(NvosConst.DESCRIPTION, 'nvosdescription', apply=True).verify_result()
            output_dictionary = Tools.OutputParsingTool.parse_show_interface_output_to_dictionary(
                mgmt_port.interface.show()).get_returned_value()

            Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                              field_name=NvosConst.DESCRIPTION,
                                                              expected_value='nvosdescription')

        with allure.step("Add data before reset factory"):
            username = _add_verification_data(engines.dut, system)

        with allure.step("Get current time"):
            update_timezone(system)
            current_time = get_current_time(engines)

        with allure.step("Run reset factory with keep basic param"):
            execute_reset_factory(engines, system, "keep basic", current_time)

        update_timezone(system)

        with allure.step("Validate health status and report"):
            _validate_health_status_report(system, last_status_line)

    finally:
        with allure.step("Verify the cleanup done successfully"):
            _verify_cleanup_done(engines.dut, current_time, system, username, param=KEEP_BASIC)
            Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                              field_name=NvosConst.DESCRIPTION,
                                                              expected_value='nvosdescription')
            mgmt_port.interface.unset(NvosConst.DESCRIPTION, apply=True).verify_result()

        update_timezone(system)

        with allure.step("Verify the setup is functional"):
            _verify_the_setup_is_functional(system, engines)


@pytest.mark.system
@pytest.mark.checklist
@pytest.mark.reset_factory
def test_reset_factory_keep_all_config(engines):
    """
    Validate reset factory with keep all config param cleanup done as expected

        Test flow:
            1. set description to ib ports:
                - set, apply and save configuration
                - set and apply
                - set
            2. Validate ports description
            3. Add data
            4. Run reset factory with keep all config params
            5. After system is up again, verify the cleanup done successfully
            6. Verify the setup is functional:
                6.1.	Start openSM
                6.2.	Run several show commands
                6.3.    Run set command & apply
    """
    try:
        with allure.step('Create System object'):
            system = System()

        with allure.step('Validate health status is OK'):
            logger.info("Validate health status is OK")
            system.validate_health_status(HealthConsts.OK)
            last_status_line = system.health.history.retry_get_health_history_file_summary_line()

        with allure.step('Set description to ib ports'):
            logger.info("Set description to ib ports")
            description = "with_keep_all_config_param"
            ports = Tools.RandomizationTool.select_random_ports(requested_ports_state="up",
                                                                num_of_ports_to_select=3).get_returned_value()
            apply_and_save_port = ports[0]
            just_apply_port = ports[1]
            not_apply_port = ports[2]

        with allure.step('Set and apply description to ib port, save config after it'):
            logger.info("Set and apply description to ib port, save config after it")
            apply_and_save_port.ib_interface.set(NvosConst.DESCRIPTION, description, apply=True).verify_result()
            TestToolkit.GeneralApi[TestToolkit.tested_api].save_config(engines.dut)
            NvueGeneralCli.save_config(engines.dut)
        with allure.step('Set and apply description to ib port'):
            logger.info("Set and apply description to ib port")
            just_apply_port.ib_interface.set(NvosConst.DESCRIPTION, description, apply=True).verify_result()
        with allure.step('Set description to ib port'):
            logger.info("Set description to ib port")
            not_apply_port.ib_interface.set(NvosConst.DESCRIPTION, description, apply=False).verify_result()
        with allure.step('Validate ports description'):
            logger.info("Validate ports description")
            _validate_port_description(engines.dut, apply_and_save_port, description)
            _validate_port_description(engines.dut, just_apply_port, description)
            _validate_port_description(engines.dut, not_apply_port, "")

        with allure.step("Add data before reset factory"):
            username = _add_verification_data(engines.dut, system)

        with allure.step("Get current time"):
            update_timezone(system)
            current_time = get_current_time(engines)

        with allure.step("Run reset factory with keep all-config param"):
            execute_reset_factory(engines, system, "keep all-config", current_time)

        update_timezone(system)

        with allure.step('Validate ports description after reset factory'):
            logger.info("Validate ports description after reset factory")
            _validate_port_description(engines.dut, apply_and_save_port, description)
            _validate_port_description(engines.dut, just_apply_port, "")
            _validate_port_description(engines.dut, not_apply_port, "")

        with allure.step("Validate health status and report"):
            _validate_health_status_report(system, last_status_line)

    finally:
        with allure.step("Verify the cleanup done successfully"):
            _verify_cleanup_done(engines.dut, current_time, system, username, param=KEEP_ALL_CONFIG)

        with allure.step("Verify the setup is functional"):
            _verify_the_setup_is_functional(system, engines)


@pytest.mark.system
@pytest.mark.checklist
@pytest.mark.reset_factory
def test_reset_factory_keep_only_files(engines):
    """
    Validate reset factory with keep only files param cleanup done as expected

        Test flow:
            1. set description to ib ports:
                - set, apply and save configuration
                - set and apply
                - set
            2. Validate ports description
            3. Add data
            4. Run reset factory with keep only files param
            5. After system is up again, verify the cleanup done successfully
            6. Verify the setup is functional:
                6.1.	Start openSM
                6.2.	Run several show commands
                6.3.    Run set command & apply
    """
    try:
        with allure.step('Create System object'):
            system = System()
            date_time_str = engines.dut.run_cmd("date").split(" ", 1)[1]
            current_time = datetime.strptime(date_time_str, '%d %b %Y %H:%M:%S %p %Z')

        with allure.step('Validate health status is OK'):
            logger.info("Validate health status is OK")
            system.validate_health_status(HealthConsts.OK)
            last_status_line = system.health.history.retry_get_health_history_file_summary_line()

        with allure.step('Set description to ib ports'):
            logger.info("Set description to ib ports")
            description = "with_all_files_param"
            ports = Tools.RandomizationTool.select_random_ports(requested_ports_state="up",
                                                                num_of_ports_to_select=2).get_returned_value()
            apply_and_save_port = ports[0]
            just_apply_port = ports[1]
            not_apply_port = Tools.RandomizationTool.select_random_ports(requested_ports_state="down",
                                                                         num_of_ports_to_select=2).get_returned_value()[0]

        with allure.step('Set and apply description to ib port, save config after it'):
            logger.info("Set and apply description to ib port, save config after it")
            apply_and_save_port.ib_interface.set(NvosConst.DESCRIPTION, description, apply=True).verify_result()
            TestToolkit.GeneralApi[TestToolkit.tested_api].save_config(engines.dut)
            NvueGeneralCli.save_config(engines.dut)
        with allure.step('Set and apply description to ib port'):
            logger.info("Set and apply description to ib port")
            just_apply_port.ib_interface.set(NvosConst.DESCRIPTION, description, apply=True).verify_result()
        with allure.step('Set description to ib port'):
            logger.info("Set description to ib port")
            not_apply_port.ib_interface.set(NvosConst.DESCRIPTION, description, apply=False).verify_result()
        with allure.step('Validate ports description'):
            logger.info("Validate ports description")
            _validate_port_description(engines.dut, apply_and_save_port, description)
            _validate_port_description(engines.dut, just_apply_port, description)
            _validate_port_description(engines.dut, not_apply_port, "")

        with allure.step("Add data before reset factory"):
            username = _add_verification_data(engines.dut, system)

        with allure.step("Get current time"):
            update_timezone(system)
            current_time = get_current_time(engines)

        with allure.step("Run reset factory without params"):
            execute_reset_factory(engines, system, "keep only-files", current_time)

        update_timezone(system)

        with allure.step("Validate health status and report"):
            _validate_health_status_report(system, last_status_line, False)

    finally:
        with allure.step("Verify the cleanup done successfully"):
            _verify_cleanup_done(engines.dut, current_time, system, username, param=KEEP_ONLY_FILES)

        with allure.step("Verify the setup is functional"):
            _verify_the_setup_is_functional(system, engines)


def _validate_health_status_report(system, last_status_line, should_change=True):
    start_time = time.time()
    system.health.wait_until_health_status_change_after_reboot(HealthConsts.OK)
    end_time = time.time()
    duration = end_time - start_time

    logger.info("Took {} seconds until health status changed to OK after reset factory".format(duration))

    with allure.step("Validate new health file"):
        logger.info("Validate new health file")
        expected_num = 0 if should_change else 1
        system.health.history.validate_new_summary_line_in_history_file_after_boot(last_status_line)
        assert len(system.health.history.search_line(last_status_line, system.health.history.show())) == expected_num, \
            "Health file has not changed after reset factory"


def _validate_port_description(engine, port, expected_description):
    output_dictionary = Tools.OutputParsingTool.parse_show_interface_output_to_dictionary(
        port.show_interface(engine, port.name)).get_returned_value()
    if expected_description:
        Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                          field_name=NvosConst.DESCRIPTION,
                                                          expected_value=expected_description).verify_result()


def _split_port(engine):
    with allure.step("Start openSM"):
        OpenSmTool.start_open_sm(engine)
        time.sleep(7)

    with allure.step("Select an active random port"):
        logging.info("Select an active random port")
        random_port = Tools.RandomizationTool.get_random_active_port().get_returned_value()[0]

        with allure.step("Split selected port ({})".format(random_port.name)):
            logging.info("Split selected port ({})".format(random_port.name))
            logging.warning("Currently not supported")

    return random_port


def _create_date_time_obj(str_info):
    tmp_str = str_info.split()
    str_date_time = "{date} {time}".format(date=tmp_str[1], time=tmp_str[2].split('.')[0])
    datetime_object = datetime.strptime(str_date_time, '%Y-%m-%d %H:%M:%S')
    return datetime_object


def _add_verification_data(engine, system):
    with allure.step("Add file to /host/mlnx/images"):
        output = engine.run_cmd("ls /host/mlnx")
        if "No such file or directory" in output:
            output = engine.run_cmd("sudo mkdir /host/mlnx")
        output = engine.run_cmd("ls /host/mlnx/images")
        if "No such file or directory" in output:
            output = engine.run_cmd("sudo mkdir /host/mlnx/images")
        output = engine.run_cmd("sudo touch /host/mlnx/images/verification_test")

    with allure.step("Add file to /var/dump/"):
        output = engine.run_cmd("ls /var/dump/")
        if "No such file or directory" in output:
            output = engine.run_cmd("sudo mkdir /var/dump/")
        output = engine.run_cmd("sudo touch /var/dump/verification_test")

    if is_redmine_issue_active([3532683]):
        with allure.step("Add file to /var/stats/"):
            output = engine.run_cmd("ls /var/stats/")
            if "No such file or directory" in output:
                output = engine.run_cmd("sudo mkdir /var/stats/")
            output = engine.run_cmd("sudo touch /var/stats/verification_test")

        with allure.step("Add file to /host/stats/"):
            output = engine.run_cmd("ls /host/stats/")
            if "No such file or directory" in output:
                output = engine.run_cmd("sudo mkdir /host/stats/")
            output = engine.run_cmd("sudo touch /host/stats/verification_test")

    with allure.step("Add history files to /home"):
        output = engine.run_cmd("ls /home")
        if ".bash_history" not in output:
            output = engine.run_cmd("sudo touch /home/.bash_history")
        if ".python_history" not in output:
            output = engine.run_cmd("sudo touch /home/.python_history")
        if ".viminfo" not in output:
            output = engine.run_cmd("sudo touch /home/.viminfo")
        output = engine.run_cmd("sudo touch /home/verification_test")

    with allure.step("Add file to /etc/sonic"):
        output = engine.run_cmd("ls /etc/sonic")
        if "No such file or directory" in output:
            output = engine.run_cmd("sudo mkdir /etc/sonic")
        output = engine.run_cmd("sudo touch /etc/sonic/verification_test")

    with allure.step("Add file to /host/warmboot"):
        output = engine.run_cmd("ls /host/warmboot")
        if "No such file or directory" in output:
            output = engine.run_cmd("sudo mkdir /host/warmboot")
        output = engine.run_cmd("sudo touch /host/warmboot/verification_test")

    with allure.step("Check running dockers"):
        logging.info("Check running dockers")
        output = engine.run_cmd("docker container list").split('\n')[1:]
        for line in output:
            line = line.split()
            docker_name = line[len(line) - 1]
            start_time = engine.run_cmd(r"docker inspect -f \{\{'.Created'\}\} " + docker_name)
            start_time = datetime.strptime(start_time.split(".")[0], f'%Y-%m-%dT%H:%M:%S')
            running_dockers[docker_name] = start_time

    with allure.step("Create new user"):
        username, password = system.create_new_user(engine)
        return username


def _verify_cleanup_done(engine, current_time, system, username, param=''):
    logging.info("Verify cleanup done as expected")
    errors = ""
    with allure.step("Verify NVUE reset done"):
        if param != KEEP_ONLY_FILES:
            output = engine.run_cmd("stat /etc/sonic/nvue.d/platform/immutables.yaml | grep Birth")
            if output and "No such file or directory" not in output:
                file_date_time = _create_date_time_obj(output)
                if current_time >= file_date_time:
                    errors += "\n/etc/sonic/nvue.d/platform/immutables.yaml was not deleted"

            output = engine.run_cmd("stat /etc/sonic/nvue.d/startup.yaml | grep Birth")
            if output and "No such file or directory" not in output:
                file_date_time = _create_date_time_obj(output)
                if current_time >= file_date_time:
                    errors += "\n/etc/sonic/nvue.d/startup.yaml was not deleted"

    with allure.step("Verify sonic.target stopped"):
        if param != KEEP_ONLY_FILES:
            output = engine.run_cmd("systemctl show sonic.target | grep StateChangeTimestamp=")
            if output:
                output = output.split('=')[1].split()
                file_date_time = _create_date_time_obj("date {} {}".format(output[1], output[2]))
                if current_time >= file_date_time:
                    errors += "\nsonic.target probably was not stopped"

    with allure.step("Verify new DB was created"):
        if param not in [KEEP_ALL_CONFIG, KEEP_ONLY_FILES]:
            output = engine.run_cmd("stat /etc/sonic/config_db.json | grep Birth")
            if output and "No such file or directory" not in output:
                file_date_time = _create_date_time_obj(output)
                if current_time >= file_date_time:
                    errors += "\nnew /etc/sonic/config_db.json was not created"

    with allure.step("Verify NVOS HOOKs were deleted"):
        if param != KEEP_ONLY_FILES:
            output = engine.run_cmd("ls /host/mlnx/images")
            if output and "No such file or directory" not in output:
                errors += "\nNVOS Hooks were not deleted"

    with allure.step("Verify tech-support files were deleted"):
        if param != KEEP_ONLY_FILES:
            output = engine.run_cmd("ls /var/dump")
            if output and "No such file or directory" not in output:
                errors += "\ntech-support files were not deleted"

    with allure.step("Verify old stats internal files were deleted"):
        if param != KEEP_ONLY_FILES:
            output = engine.run_cmd("ls /var/stats")
            if output and "No such file or directory" not in output:
                stats_files = list(output.split())
                for stat_file in stats_files:
                    output = engine.run_cmd(f"stat /var/stats/{stat_file} | grep Birth")
                    file_date_time = _create_date_time_obj(output)
                    if current_time >= file_date_time:
                        errors += "\nold stats internal files were not deleted"

    with allure.step("Verify stats external files were deleted"):
        if param != KEEP_ONLY_FILES:
            output = engine.run_cmd("ls /host/stats")
            if output and "No such file or directory" not in output:
                errors += "\nstats external files were not deleted"

    with allure.step("Verify /etc/sonic content was cleared"):
        if param != KEEP_ONLY_FILES:
            output = engine.run_cmd("ls /etc/sonic/verification_test")
            if output and "No such file or directory" not in output:
                errors += "\n/etc/sonic was not cleared"

    with allure.step("Verify /host/warmboot content was deleted"):
        if param != KEEP_ONLY_FILES:
            output = engine.run_cmd("ls /host/warmboot")
            if output and "No such file or directory" not in output:
                errors += "\n/host/warmboot was not cleared"

    with allure.step("Verify history was deleted"):
        if param not in [KEEP_BASIC, KEEP_ONLY_FILES]:
            output = engine.run_cmd("ls /home/.bash_history")
            if "No such file or directory" not in output:
                errors += "\n*.bash_history files were not deleted"
            output = engine.run_cmd("ls /home/.python_history")
            if "No such file or directory" not in output:
                errors += "\n*.python_history files were not deleted"
            output = engine.run_cmd("ls /home/.viminfo")
            if "No such file or directory" not in output:
                errors += "\n*.viminfo files were not deleted"
            output = engine.run_cmd("find /home/ -maxdepth 1 -type f ")

    with allure.step("Verify btmp files were cleared"):
        if param != KEEP_ONLY_FILES:
            output = engine.run_cmd("stat /var/log/btmp | grep Modify")
            if output and "No such file or directory" not in output:
                file_date_time = _create_date_time_obj(output)
                if current_time >= file_date_time:
                    errors += "\n/var/log/btmp was not cleared"

            output = engine.run_cmd("stat /var/log/lastlog | grep Modify")
            if output and "No such file or directory" not in output:
                file_date_time = _create_date_time_obj(output)
                if current_time >= file_date_time:
                    errors += "\n/var/log/lastlog was not created"

            output = engine.run_cmd("stat /var/log/wtmp | grep Modify")
            if output and "No such file or directory" not in output:
                file_date_time = _create_date_time_obj(output)
                if current_time >= file_date_time:
                    errors += "\n/var/log/wtmp was not created"

    with allure.step("Create new user"):
        if param != KEEP_BASIC:
            output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
                engine.run_cmd("nv show system aaa user -o json")).get_returned_value()
            if username in output.keys():
                errors += "\nCreated user was not deleted"

    with allure.step("Check running dockers"):
        if param != KEEP_ONLY_FILES:
            logging.info("Check running dockers")
            for docker_name, orig_create_time in running_dockers.items():
                output = engine.run_cmd(r"docker inspect -f \{\{'.Created'\}\} " + docker_name)
                if "Error" in output:
                    create_time = ""
                else:
                    create_time = datetime.strptime(output.split(".")[0], f'%Y-%m-%dT%H:%M:%S')

                if "database" in docker_name:
                    if create_time != orig_create_time:
                        errors += "reset factory should not restart database docker"
                else:
                    if not create_time:
                        errors += "\n'{}' is not running after reset factory".format(docker_name)
                    elif orig_create_time == create_time:
                        errors += "\n'{}' was not stopped during reset factory".format(docker_name)

    assert not errors, errors


def _verify_profile_and_split(selected_port):
    logging.info("Verify the breakup mode is disabled and selected port is not split any more")
    with allure.step("Check profile"):
        logging.info("Check current profile")
        logging.warning("Currently not supported")

    with allure.step("Verify port {} in not in split mode".format(selected_port.name)):
        logging.info("Verify port {} in not in split mode".format(selected_port.name))
        logging.warning("Currently not supported")


def _verify_the_setup_is_functional(system, engines):
    logging.info("Verify the setup is functional")

    with allure.step("Start OpenSM"):
        OpenSmTool.start_open_sm(engines.dut).verify_result()

    with allure.step("Run show commands"):
        system.message.show()
        system.version.show()
        platform = Platform()
        platform.show()

    with allure.step("Run set and apply"):
        system.message.set(op_param_name=SystemConsts.POST_LOGIN_MESSAGE, op_param_value='"new_post_login_msg"',
                           apply=True, dut_engine=engines.dut).verify_result()

    with allure.step("Run unset and apply"):
        system.message.unset(op_param=SystemConsts.POST_LOGIN_MESSAGE,
                             apply=True, dut_engine=engines.dut).verify_result()


@pytest.mark.system
@pytest.mark.checklist
def test_error_flow_reset_factory_with_params(engines, devices, topology_obj):
    """
    This test is a temporary test - will be changed for GA
    :return:
    """
    with allure.step("Create system object"):
        system = System(None)

    with allure.step("Run reset factory with params - expect failure"):
        logging.info("Run reset factory with params - expect failure")
        output = engines.dut.run_cmd("nv action reset system factory-default only-config")
        assert "Invalid parameter" in output, "Reset factory with param should fail"
        # system.factory_default.action_reset(param="only-config").verify_result(should_succeed=False)


def update_timezone(system):
    with allure.step('Configure timezone'):
        logger.info(
            "Configuring same time zone for dut and local engine to {}".format(LinuxConsts.JERUSALEM_TIMEZONE))
        ClockTools.set_timezone(LinuxConsts.JERUSALEM_TIMEZONE, system, apply=True).verify_result()
        with allure.step('Set timezone using timedatectl command'):
            os.popen('sudo timedatectl set-timezone {}'.format(LinuxConsts.JERUSALEM_TIMEZONE))


def get_current_time(engines):
    date_time_str = engines.dut.run_cmd("date").split(" ", 1)[1]
    current_time = datetime.strptime(date_time_str, '%d %b %Y %H:%M:%S %p %Z')
    return current_time


def execute_reset_factory(engines, system, flag, current_time):
    logging.info("Current time: " + str(current_time))
    res_obj, duration = OperationTime.save_duration('reset factory', flag, pytest.test_name,
                                                    system.factory_default.action_reset, param=flag)
    res_obj.verify_result()
    assert OperationTime.verify_operation_time(duration, 'reset factory'), \
        'Reset factory took more time than threshold value'


# ------------ Open API tests -----------------

@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.checklist
def test_error_flow_reset_factory_with_params_openapi(engines, devices, topology_obj):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_error_flow_reset_factory_with_params(engines, devices, topology_obj)
