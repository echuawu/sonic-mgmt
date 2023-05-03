import logging
import time
from retry import retry
import allure
import pytest
import random
import math
from datetime import datetime

from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.Fae import Fae
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.Simulator import HWSimulator
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import SystemConsts, HealthConsts, NvosConst

logger = logging.getLogger()


OK = HealthConsts.OK
NOT_OK = HealthConsts.NOT_OK
IGNORED = HealthConsts.IGNORED
CHECKER_FILE = "/tmp/my_checker.py"
USER_DEFINED_CHECKERS_LINE = "\"user_defined_checkers\": \\[{}\\]"
DEVICES_TO_IGNORE_LINE = "\"devices_to_ignore\": \\[{}\\]"


@pytest.mark.system
@pytest.mark.health
def test_reboot_test():
    """
    Validate health after reboot :
    - status is OK
    - same health file as before the reboot
    - relevant reboot line appears in the health file
    - new summary line after the reboot in the health file
    """

    system = System()
    system.validate_health_status(OK)
    last_status_line = system.health.history.search_line(HealthConsts.SUMMARY_REGEX_OK)[-1]

    with allure.step('Reboot the system'):
        system.reboot.action_reboot()

    start_time = time.time()
    system.health.wait_until_health_status_change_after_reboot(OK)
    end_time = time.time()
    duration = end_time - start_time

    with allure.step("Took {} seconds until health status changed to OK after reboot".format(duration)):
        logger.info("Took {} seconds until health status changed to OK after reboot".format(duration))

    with allure.step("Validate it is the same health file"):
        logger.info("Validate it is the same health file")
        health_history_output = system.health.history.show()
        assert len(system.health.history.search_line(last_status_line, health_history_output)) == 1, "Health file has changed after reboot"

    with allure.step("Validate health history file indicates reboot occurred and print the status again"):
        logger.info("Validate health history file indicates reboot occurred and print the status again")
        validate_new_summary_line_in_history_file_after_boot(system, last_status_line)


@pytest.mark.system
@pytest.mark.health
def test_show_system_health(devices):
    """
    Validate all the show system health commands
        Test flow:
            1. validate nv show system cmd
            2. validate nv show system health cmd
            3. validate nv show fae health cmd
            4. validate nv show system health history cmd
            5. validate nv show system health history files cmd
            6. validate nv show system health history files <file> cmd
    """

    system = System()

    with allure.step("Validate health status with \"nv show system\" cmd"):
        logger.info("Validate health status with \"nv show system\" cmd")
        system_output = OutputParsingTool.parse_json_str_to_dictionary(system.show()).get_returned_value()
        ValidationTool.verify_field_exist_in_json_output(system_output, [SystemConsts.HEALTH_STATUS]).verify_result()
        verify_expected_health_status(system_output, SystemConsts.HEALTH_STATUS, OK)

    with allure.step("Validate \"nv show system health\" cmd"):
        logger.info("Validate \"nv show system health\" cmd")
        health_output = OutputParsingTool.parse_json_str_to_dictionary(system.health.show()).get_returned_value()
        ValidationTool.validate_all_values_exists_in_list([HealthConsts.STATUS, HealthConsts.STATUS_LED], health_output.keys()).verify_result()
        verify_health_status_and_led(system, HealthConsts.OK)

    with allure.step("Validate \"nv show fae health\" cmd"):
        logger.info("Validate \"nv show fae health\" cmd")
        detail_health_output = OutputParsingTool.parse_json_str_to_dictionary(Fae().health.show()).get_returned_value()
        ValidationTool.validate_all_values_exists_in_list([HealthConsts.STATUS, HealthConsts.STATUS_LED, HealthConsts.MONITOR_LIST],
                                                          detail_health_output).verify_result()
        verify_expected_health_status(detail_health_output, HealthConsts.STATUS, OK)
        monitor_dict = sort_monitor_list(detail_health_output[HealthConsts.MONITOR_LIST])
        assert len(monitor_dict[NOT_OK]) == 0, "Expected not to have \"Not OK\" devices, cause the health status is OK,\n" \
                                               "but those devices are not OK : {}".format(monitor_dict[NOT_OK])
        ValidationTool.validate_all_values_exists_in_list(devices.dut.health_components,
                                                          detail_health_output[HealthConsts.MONITOR_LIST].keys()).verify_result()

    with allure.step("Validate \"nv show system health history\" cmd"):
        logger.info("Validate \"nv show system health history\" cmd")
        health_history_output = system.health.history.show()
        assert system.health.history.get_last_status_from_health_file(health_history_output) == OK, "Last status in the health report file is Not OK but expected to be OK"

    with allure.step("Validate \"nv show system health history files\" cmd"):
        logger.info("Validate \"nv show system health history files\" cmd")
        health_history_files = OutputParsingTool.parse_json_str_to_dictionary(system.health.history.files.show()).get_returned_value()
        files_amount = len(health_history_files)
        assert files_amount in [1, 2], "Unexpected amount of history files.\n Expected: 1 or 2 , but got {}".format(files_amount)
        assert HealthConsts.HEALTH_FIRST_FILE in health_history_files, "Expect to have {} as health file, but have those files {}"\
            .format(HealthConsts.HEALTH_FIRST_FILE, health_history_files)
        if files_amount == 2:
            assert HealthConsts.HEALTH_SECOND_FILE in health_history_files, "Expect to have {} as health file, but have those files {}" \
                .format(HealthConsts.HEALTH_SECOND_FILE, health_history_files)

        health_history_file_output = system.health.history.show_health_report_file(HealthConsts.HEALTH_FIRST_FILE)
        # first line in the health report output is the cmd itself, so we will compared just the file itself.
        assert health_history_file_output.split("\n", 2)[2] == health_history_output.split("\n", 2)[2], "The first health file does not show the same info as the default cmd"


@pytest.mark.system
@pytest.mark.health
def test_system_health_files(engines, devices):
    """
    Will validate the health files requirements:
        -	Tech-support will contain health files
        -	Upload health files
        -	Delete health files
    """

    system_health_files_test(engines, devices, check_rotation=False)


@pytest.mark.system
@pytest.mark.health
@pytest.mark.checklist
def test_system_health_files_with_rotation(engines, devices):
    """
    Will validate the health files requirements:
        -	file will be rotated after 10 MB
        -	maximum 2 health files
        -	Tech-support will contain health files
        -	Upload health files
        -	Delete health files
    """

    system_health_files_test(engines, devices, check_rotation=True)


@pytest.mark.system
@pytest.mark.health
def test_ignore_health_issue(engines, devices):
    """
    Validate we can ignore all health issue and status will change to OK
    steps:
        1. Simulate PSU and FAN health issue
        2. Validate health status and report
        3. Ignore PSU issue and Validate
        4. Ignore FAN issue too and Validate health state change to OK
        5. Remove the ignore from FAN issue and Validate health state change to Not OK
        6. Remove the ignore from PSU issue too and Validate
        7. Fix PSU and FAN health issue
    """
    system = System()
    ignore_health_issue(None, engines.dut, devices.dut)
    verify_health_status_and_led(system, OK)

    try:
        with allure.step("Simulate PSU and FAN health issue"):
            logger.info("Simulate PSU and FAN health issue")
            psu_id, fan_id = simulate_fan_and_psu_health_issue(engines, devices)
            psu_display_name = "PSU{}".format(psu_id)
            psu_config_name = "PSU {}".format(psu_id)
            psu_fan_display_name = "PSU{}/FAN".format(psu_id)
            psu_fan_config_name = "psu{}_fan1".format(psu_id)
            fan_display_name = get_fan_display_name(fan_id)
            fan_config_name = "fan{}".format(fan_id)

        with allure.step("Validate health status and report"):
            logger.info("Validate health status and report")
            system.wait_until_health_status_change_to(NOT_OK)
            verify_health_status_and_led(system, NOT_OK)
            monitor_list = OutputParsingTool.parse_json_str_to_dictionary(Fae().health.show()).get_returned_value()[HealthConsts.MONITOR_LIST]
            verify_devices_health_status_in_monitor_list({psu_display_name: NOT_OK, psu_fan_display_name: NOT_OK, fan_display_name: NOT_OK}, monitor_list)
            verify_devices_health_status_in_issues_list(system, [psu_display_name, psu_fan_display_name, fan_display_name])

        with allure.step("Ignore PSU issue and Validate"):
            logger.info("Ignore PSU issue and Validate")
            ignore_health_issue([psu_config_name, psu_fan_config_name], engines.dut, devices.dut)
            system.wait_until_health_status_change_to(NOT_OK)
            verify_health_status_and_led(system, NOT_OK)
            monitor_list = OutputParsingTool.parse_json_str_to_dictionary(Fae().health.show()).get_returned_value()[
                HealthConsts.MONITOR_LIST]
            verify_devices_health_status_in_monitor_list({psu_display_name: IGNORED, psu_fan_display_name: IGNORED, fan_display_name: NOT_OK}, monitor_list)
            verify_devices_health_status_in_issues_list(system, [fan_display_name])

        with allure.step("Ignore FAN issue too and Validate health state change to OK"):
            logger.info("Ignore FAN issue too and Validate health state change to OK")
            ignore_health_issue([psu_config_name, psu_fan_config_name, fan_config_name], engines.dut, devices.dut)
            system.wait_until_health_status_change_to(OK)
            verify_health_status_and_led(system, OK)
            monitor_list = OutputParsingTool.parse_json_str_to_dictionary(Fae().health.show()).get_returned_value()[
                HealthConsts.MONITOR_LIST]
            verify_devices_health_status_in_monitor_list({psu_display_name: IGNORED, psu_fan_display_name: IGNORED, fan_display_name: IGNORED}, monitor_list)
            verify_devices_health_status_in_issues_list(system, [])

        with allure.step("Remove the ignore from FAN issue and Validate health state change to Not OK"):
            logger.info("Remove the ignore from FAN issue and Validate health state change to Not OK")
            ignore_health_issue([psu_config_name, psu_fan_config_name], engines.dut, devices.dut)
            system.wait_until_health_status_change_to(NOT_OK)
            verify_health_status_and_led(system, NOT_OK)
            monitor_list = OutputParsingTool.parse_json_str_to_dictionary(Fae().health.show()).get_returned_value()[
                HealthConsts.MONITOR_LIST]
            verify_devices_health_status_in_monitor_list({psu_display_name: IGNORED, psu_fan_display_name: IGNORED, fan_display_name: NOT_OK}, monitor_list)
            verify_devices_health_status_in_issues_list(system, [fan_display_name])

        with allure.step("Remove the ignore from PSU issue too and Validate"):
            logger.info("Remove the ignore from PSU issue too and Validate")
            ignore_health_issue(None, engines.dut, devices.dut)
            system.wait_until_health_status_change_to(NOT_OK)
            verify_health_status_and_led(system, NOT_OK)
            verify_devices_health_status_in_monitor_list({psu_display_name: NOT_OK, psu_fan_display_name: NOT_OK, fan_display_name: NOT_OK})
            verify_devices_health_status_in_issues_list(system, [psu_display_name, psu_fan_display_name, fan_display_name])

    finally:

        with allure.step("Fix PSU and FAN health issue"):
            logger.info("Fix PSU and FAN health issue")
            ignore_health_issue(None, engines.dut, devices.dut)
            HWSimulator.simulate_fix_fan_fault(engines.dut, fan_id)
            HWSimulator.simulate_fix_psu_fault(engines.dut, psu_id)
            system.wait_until_health_status_change_to(OK)
            verify_health_status_and_led(system, OK)


@pytest.mark.system
@pytest.mark.health
def test_simulate_health_problem_with_hw_simulator(devices, engines):
    """
    Validate health monitoring.
    Health status should change to "Not OK" when we simulate a problem and return to "OK" if status fixed or ignored.
        Test flow:
            1. Simulate health problem with HW simulator
            2. validate health status changed to "Not OK"
            3. validate devices appear in the detailed health report as not OK
            5. validate status has changed in the log
            6. fix the health issue
            7. validate health status changed to "OK"
            8. validate devices appear in the detailed health report as OK
    """

    system = System()
    system.log.rotate_logs()
    date_time = datetime.now()
    system.health.history.delete_history_file(HealthConsts.HEALTH_FIRST_FILE)
    time.sleep(1)
    verify_health_status_and_led(system, OK)

    try:
        psu_id, fan_id = simulate_fan_and_psu_health_issue(engines, devices)
        psu_display_name = "PSU{}".format(psu_id)
        psu_fan_display_name = "PSU{}/FAN".format(psu_id)
        fan_display_name = get_fan_display_name(fan_id)
        health_issue_dict = {psu_display_name: "missing or not available", psu_fan_display_name: "missing",
                             fan_display_name: "broken"}
        validate_health_fix_or_issue(system, health_issue_dict, date_time, False)

    finally:
        date_time = datetime.now()
        time.sleep(1)
        with allure.step("Fix the health issues"):
            logger.info("Fix the health issues")
            HWSimulator.simulate_fix_fan_fault(engines.dut, fan_id)
            HWSimulator.simulate_fix_psu_fault(engines.dut, psu_id)
            validate_health_fix_or_issue(system, health_issue_dict, date_time, True)


@pytest.mark.system
@pytest.mark.health
def test_simulate_fan_speed_fault(devices, engines):
    """
    Validate health monitoring when having a fan speed fault.
        Test flow:
            1. Simulate fan speed fault
            2. validate health status changed to "Not OK"
            3. validate devices appear in the detailed health report as not OK
            5. validate status has changed in the log
            6. fix the health issue
            7. validate health status changed to "OK"
            8. validate devices appear in the detailed health report as OK
    """
    system = System()
    system.log.rotate_logs()
    date_time = datetime.now()
    system.health.history.delete_history_file(HealthConsts.HEALTH_FIRST_FILE)
    time.sleep(1)
    verify_health_status_and_led(system, OK)
    fan_id = random.randrange(1, len(devices.dut.fan_list) + 1)
    logger.info("Chosen fan : {}  - {}".format(fan_id, get_fan_display_name(fan_id)))

    try:
        real_speed = HWSimulator.simulate_fan_speed_fault(engines.dut, fan_id)
        fan_display_name = get_fan_display_name(fan_id)
        health_issue_dict = {fan_display_name: "speed is out of range"}
        validate_health_fix_or_issue(system, health_issue_dict, date_time, False)

    finally:
        date_time = datetime.now()
        time.sleep(1)
        with allure.step("Fix the health issues"):
            logger.info("Fix the health issues")
            HWSimulator.simulate_fix_fan_speed_fault(engines.dut, fan_id, real_speed)
            logger.info("Sleep 10 second")
            time.sleep(10)
            validate_health_fix_or_issue(system, health_issue_dict, date_time, True)


@pytest.mark.system
@pytest.mark.health
def test_simulate_health_problem_with_user_config_file(devices, engines):
    """
    Validate health monitoring.
    Health status should change to "Not OK" when we simulate a problem and return to "OK" if status fixed or ignored.
        Test flow:
            1. Simulate health problem with user config file
            2. validate health status changed to "Not OK"
            3. validate new devices appear in the detailed cmd
            5. validate status has changed in the log
            6. fix the health issue
            7. validate health status changed to "Not OK"
            8. validate new devices removed from the detailed cmd
    """

    system = System()
    system.log.rotate_logs()
    date_time = datetime.now()
    system.health.history.delete_history_file(HealthConsts.HEALTH_FIRST_FILE)
    time.sleep(1)
    system.validate_health_status(OK)

    try:
        health_issue_dict = simulate_health_issue_with_config_file_and_validate(system, engines.dut, devices.dut)
        validate_health_fix_or_issue(system, health_issue_dict, date_time, False)

    finally:
        date_time = datetime.now()
        time.sleep(1)
        with allure.step("Fix the health issue - remove user config file"):
            logger.info("Fix the health issue - remove user config file")
            remove_user_config_file(engines.dut, devices.dut)
            validate_health_fix_or_issue(system, health_issue_dict, date_time, True)


@pytest.mark.system
@pytest.mark.health
def test_simulate_health_problem_with_docker_stop(devices, engines):
    """
    Validate health monitoring.
    Health status should change to "Not OK" when we simulate a problem and return to "OK" if status fixed or ignored.
        Test flow:
            1. Simulate health problem with user config file
            2. validate health status changed to "Not OK"
            3. validate new devices appear in the detailed cmd
            5. validate status has changed in the log
            6. fix the health issue
            7. validate health status changed to "Not OK"
            8. validate new devices removed from the detailed cmd
    """

    system = System()
    system.log.rotate_logs()
    date_time = datetime.now()
    system.health.history.delete_history_file(HealthConsts.HEALTH_FIRST_FILE)
    time.sleep(1)
    system.validate_health_status(OK)
    docker_to_stop = "ib-utils"

    try:
        output = engines.dut.run_cmd("docker stop {}".format(docker_to_stop))
        assert docker_to_stop in output, "Failed to stop docker"
        health_issue_dict = {docker_to_stop: "Container 'ib-utils' is not running"}
        validate_health_fix_or_issue(system, health_issue_dict, date_time, False, expected_in_monitor_list=False)

    finally:
        date_time = datetime.now()
        time.sleep(1)
        with allure.step("Fix the health issue "):
            logger.info("Fix the health issue ")
            output = engines.dut.run_cmd("docker start {}".format(docker_to_stop))
            assert docker_to_stop in output, "Failed to start docker"
            validate_docker_is_up(engines.dut, docker_to_stop)
            time.sleep(10)
            validate_health_fix_or_issue(system, health_issue_dict, date_time, True)


@retry(Exception, tries=5, delay=2)
def validate_docker_is_up(engine, docker):
    assert docker in engine.run_cmd("docker ps")


def verify_health_status_and_led(system, expected_status, output=None):
    if not output:
        output = OutputParsingTool.parse_json_str_to_dictionary(system.health.show()).get_returned_value()
    verify_expected_health_status(output, HealthConsts.STATUS, expected_status)
    expected_led = HealthConsts.LED_OK_STATUS if expected_status == HealthConsts.OK else HealthConsts.LED_NOT_OK_STATUS
    verify_expected_health_status(output, HealthConsts.STATUS_LED, expected_led)


@retry(Exception, tries=12, delay=30)
def validate_new_summary_line_in_history_file_after_boot(system, last_summary_line):
    health_history_output = system.health.history.show()
    assert system.health.history.search_line(HealthConsts.SUMMARY_REGEX_OK, health_history_output)[
        -1] != last_summary_line, "Didn't print new summary line after boot"
    assert "Monitoring service reboot, clearing issues history." in health_history_output


def verify_devices_health_status_in_monitor_list(device_status_dict, monitor_list=None):
    """
    verify device status in the health detail output
    :param device_status_dict: dictionary with devices and their status, example: {PSU1: OK , PSU2: Not OK, FAN1/1: Ignored}
    """
    monitor_dict = sort_monitor_list(monitor_list)
    for device_name, status in device_status_dict.items():
        if status == HealthConsts.IGNORED and monitor_list:
            assert device_name not in list(monitor_list.keys()), "{} should be ignored , so should not appear in the monitor list"
        else:
            assert device_name in monitor_dict[status]


def verify_devices_health_status_in_issues_list(system, devices_list):
    """
    verify device status in the health show output, under the section "issues"
    :param devices_list: list of devices with issues, example: [PSU1, PSU2, FAN1/1]
    """
    issues_dict = OutputParsingTool.parse_json_str_to_dictionary(system.health.show()).get_returned_value()[HealthConsts.ISSUES]
    assert set(devices_list) == set(list(issues_dict.keys()))


def simulate_fan_and_psu_health_issue(engines, devices):
    logger.info("choose randomly PSU and FAN")
    psu_id = random.randrange(1, len(devices.dut.psu_list) + 1)
    fan_id = random.randrange(1, len(devices.dut.fan_list) + 1)
    logger.info("Chosen PSU : {}\n Chosen fan : {}  - {}".format(psu_id, fan_id, get_fan_display_name(fan_id)))
    HWSimulator.simulate_fan_fault(engines.dut, fan_id)
    HWSimulator.simulate_psu_fault(engines.dut, psu_id)
    return psu_id, fan_id


def get_fan_display_name(fan_id):
    section = 1 if fan_id % 2 == 1 else 2
    num = math.floor(fan_id / 2) + fan_id % 2
    return "FAN{}/{}".format(num, section)


def ignore_health_issue(components_list_to_ignore, engine, device):
    components_as_string = ", ".join(["\"{}\"".format(comp) for comp in components_list_to_ignore]) if components_list_to_ignore else ""
    engine.run_cmd("sudo sed -i 's/{}/{}/' {}".format(DEVICES_TO_IGNORE_LINE.format(".*"),
                                                      DEVICES_TO_IGNORE_LINE.format(components_as_string),
                                                      device.health_monitor_config_file_path))


def validate_health_fix_or_issue(system, health_issue_dict, search_since_datetime, is_fix, expected_in_monitor_list=True):
    """
    validate health issue or fix with show commands
        - validate with system show cmd the health status
        - validate with health detailed report
        - validate with health history file the status and the issues
        - validate system log indicates that health status has changed
    """
    status = OK if is_fix else NOT_OK
    regex = HealthConsts.HEALTH_FIX_REGEX if is_fix else HealthConsts.HEALTH_ISSUE_REGEX
    with allure.step("Validate health issues {}".format("fix" if is_fix else "")):
        logger.info("Validate health issues {}".format("fix" if is_fix else ""))
        system.wait_until_health_status_change_to(status)

        with allure.step("Validate health output issues"):
            logger.info("Validate health output issues")
            health_output = OutputParsingTool.parse_json_str_to_dictionary(system.health.show()).get_returned_value()
            verify_health_status_and_led(system, status, health_output)
            health_issues = health_output[HealthConsts.ISSUES]
            for component, issue in health_issue_dict.items():
                if is_fix:
                    assert component not in health_issues
                else:
                    assert component in health_issues
                    assert issue in health_issues[component]["issue"]

        if expected_in_monitor_list:
            with allure.step("Validate detailed health report"):
                logger.info("Validate detailed health report")
                detail_health_output = OutputParsingTool.parse_json_str_to_dictionary(
                    Fae().health.show()).get_returned_value()
                verify_expected_health_status(detail_health_output, HealthConsts.STATUS, status)
                monitor_dict = sort_monitor_list(detail_health_output[HealthConsts.MONITOR_LIST])
                for component, issue in health_issue_dict.items():
                    if is_fix:
                        assert component not in monitor_dict[NOT_OK]
                    else:
                        assert component in monitor_dict[NOT_OK]
                        assert issue in detail_health_output[HealthConsts.MONITOR_LIST][component]["message"]

        with allure.step("Validate health history file"):
            logger.info("Validate health history file")
            health_history_output = system.health.history.show()
            assert system.health.history.get_last_status_from_health_file(
                health_history_output) == status, "Last status in the health report file is not {}, as we expect".format(status)
            assert len(TestToolkit.search_line_after_a_specific_date_time(
                HealthConsts.ADD_STATUS_TO_SUMMARY_REGEX + status, health_history_output,
                search_since_datetime)) > 0, "Didn't find health status in history file since time : {},\n" \
                                             "history:\n {}".format(search_since_datetime, health_history_output)
            for component, issue in health_issue_dict.items():
                assert len(TestToolkit.search_line_after_a_specific_date_time(
                    regex.format(time_regex=NvosConst.DATE_TIME_REGEX, component=component, issue=issue), health_history_output, search_since_datetime)) > 0

        with allure.step("Validate health status change appears in system log"):
            logger.info("Validate health status change appears in system log")
            log_output = system.log.show_log(exit_cmd='q', expected_str="Health DB change cache")
            assert len(TestToolkit.search_line_after_a_specific_date_time(
                NvosConst.DATE_TIME_REGEX + HealthConsts.SYSTEM_LOG_HEALTH_REGEX.format(status), log_output,
                search_since_datetime)) > 0, "Didn't find health status line in the system log since specific time :{}\n" \
                                             "System Log:\n {}".format(search_since_datetime, log_output)


def system_health_files_test(engines, devices, check_rotation=False):
    """
    Will validate the health files requirements:
    steps:
        1. validate health status is OK
        2. simulate health issue
        3. validate health status is not OK
        4. do file rotation (if flag is true)
        5. Validate health files in tech support file
        6. upload health files
        7. delete health files
    """

    system = System()
    system.validate_health_status(OK)

    try:
        simulate_health_issue_with_config_file_and_validate(system, engines.dut, devices.dut)

        if check_rotation:
            with allure.step("First file rotation"):
                logger.info("First file rotation")
                cause_health_file_rotation_and_validate(engines.dut, system)

            with allure.step("Second file rotation"):
                logger.info("Second file rotation")
                cause_health_file_rotation_and_validate(engines.dut, system)

        health_files = list(OutputParsingTool.parse_json_str_to_dictionary(system.health.history.files.show()).get_returned_value().keys())

        with allure.step("Validate health files in tech support file"):
            logger.info("Validate health files in tech support file")
            validate_health_files_exist_in_techsupport(system, engines.dut, health_files)

        with allure.step("Upload health files"):
            logger.info("Upload health files")
            validate_upload_health_files(engines, system, health_files)

        with allure.step("Delete health files"):
            logger.info("Delete health files")
            validate_delete_health_files(system, health_files)

    finally:
        with allure.step("Remove user monitoring config file"):
            logger.info("Remove user monitoring config file")
            remove_user_config_file(engines.dut, devices.dut)
            system.wait_until_health_status_change_to(OK)


def validate_delete_health_files(system, health_files=[HealthConsts.HEALTH_FIRST_FILE, HealthConsts.HEALTH_SECOND_FILE]):
    """
    delete health files and validate new health file was crated with health summary status
    """
    last_status_line = system.health.history.search_line(HealthConsts.ADD_STATUS_TO_SUMMARY_REGEX + OK)[-1]
    system.health.history.delete_history_files(health_files)
    time.sleep(5)
    with allure.step("Validate new file was created"):
        logger.info("Validate new file was created")
        assert len(system.health.history.search_line(last_status_line)) == 0, "Health file has not changed"

    with allure.step("Validate health status exist in the history file"):
        logger.info("Validate health status exist in the history file")
        health_history_output = system.health.history.show()
        assert system.health.history.get_last_status_from_health_file(health_history_output) == NOT_OK
        assert "health_history file deleted, creating new file" in health_history_output

    validate_health_files_amount(1)


def validate_upload_health_files(engines, system, health_files=[HealthConsts.HEALTH_FIRST_FILE, HealthConsts.HEALTH_SECOND_FILE]):
    """
    validate upload health files with scp and sftp
    """
    upload_protocols = ['scp', 'sftp']
    player = engines['sonic_mgmt']
    file_to_upload = random.choice(health_files)

    with allure.step(
            "Upload health file to player {} with the next protocols : {}".format(player.ip, upload_protocols)):
        logging.info("Upload health file to player {} with the next protocols : {}".format(player.ip, upload_protocols))

        for protocol in upload_protocols:
            with allure.step("Upload health file to player with {} protocol".format(protocol)):
                logging.info("Upload health file to player with {} protocol".format(protocol))
                upload_path = '{}://{}:{}@{}/tmp/{}'.format(protocol, player.username, player.password, player.ip,
                                                            file_to_upload)
                system.health.history.upload_history_files(file_to_upload, upload_path)

            with allure.step("Validate file was uploaded to player and delete it"):
                logging.info("Validate file was uploaded to player and delete it")
                assert player.run_cmd(
                    cmd='ls /tmp/ | grep {}'.format(file_to_upload)), "Did not find the file with ls cmd"
                player.run_cmd(cmd='rm -f /tmp/{}'.format(file_to_upload))
    with allure.step("Validate health files still exist"):
        logger.info("Validate health files still exist")
        validate_health_files_amount(len(health_files))


def validate_health_files_exist_in_techsupport(system, engine, health_files=[HealthConsts.HEALTH_FIRST_FILE, HealthConsts.HEALTH_SECOND_FILE]):
    """
    generate techsupport and validate we have the health files in the log dir
    """
    tech_support_folder = system.techsupport.action_generate()
    techsupport_files_list = system.techsupport.get_techsupport_log_files_names(engine, tech_support_folder)
    for health_file in health_files:
        assert "{}.gz".format(health_file) in techsupport_files_list, \
            "Expect to have {} file, in the tech support log files {}".format(HealthConsts.HEALTH_FIRST_FILE, techsupport_files_list)


def create_health_issue_with_user_config_file(engine, device):
    """
    create health issue with user monitor config file :
    create a checker file like,
    update the monitor config file filed with the file that we created. field: user_defined_checkers
    example :
        echo -e 'print("MyCategory") /n print("bad_device:device is out of power")' > /tmp/my_checker.py
        sudo sed -i 's/"user_defined_checkers": \\[\\]/"user_defined_checkers": \\["python \\/tmp\\/my_checker.py"\\]/' \\/tmp\\/system_health_monitoring_config.json

    """
    with allure.step("create my_checker file"):
        logger.info("create my_checker file")
        create_my_checker_file_cmd = "echo -e 'print(\"MyCategory\") \nprint(\"bad_device:device is out of power\")' > {}".format(CHECKER_FILE)
        engine.run_cmd(create_my_checker_file_cmd)

    with allure.step("Update monitoring config file with my_checker file"):
        logger.info("Update monitoring config file with my_checker file")
        checker_file = CHECKER_FILE.replace("/", "\\/")
        engine.run_cmd("sudo sed -i 's/{}/{}/' {}".format(USER_DEFINED_CHECKERS_LINE.format(""), USER_DEFINED_CHECKERS_LINE.format("\"python {}\"".format(checker_file)), device.health_monitor_config_file_path))
        return {"bad_device": "device is out of power"}


def simulate_health_issue_with_config_file_and_validate(system, engine, device):
    with allure.step("Simulate health problem with user config file"):
        logger.info("Simulate health problem with user config file")
        new_devices_dict = create_health_issue_with_user_config_file(engine, device)

    with allure.step("Validate health status has change and add the info of the new devices"):
        logger.info("Validate health status has change and add the info of the new devices")
        system.wait_until_health_status_change_to(NOT_OK)
        health_output = OutputParsingTool.parse_json_str_to_dictionary(system.health.show()).get_returned_value()
        verify_expected_health_status(health_output, HealthConsts.STATUS, NOT_OK)
        detail_health_output = OutputParsingTool.parse_json_str_to_dictionary(
            Fae().health.show()).get_returned_value()
        verify_expected_health_status(detail_health_output, HealthConsts.STATUS, NOT_OK)
        for device, issue in new_devices_dict.items():
            assert device in health_output[HealthConsts.ISSUES].keys()
            assert issue in health_output[HealthConsts.ISSUES][device].values()
            assert device in detail_health_output[HealthConsts.MONITOR_LIST].keys()
            assert issue in detail_health_output[HealthConsts.MONITOR_LIST][device].values()
    return new_devices_dict


def remove_user_config_file(engine, device):
    engine.run_cmd("sudo sed -i 's/{}/{}/' {}".format(USER_DEFINED_CHECKERS_LINE.format(".*"), USER_DEFINED_CHECKERS_LINE.format(""), device.health_monitor_config_file_path))


def cause_health_file_rotation_and_validate(engine, system):
    last_status_line = system.health.history.search_line(HealthConsts.ADD_STATUS_TO_SUMMARY_REGEX + OK)[-1]
    with allure.step("create text file in size of 10 MB and replace it with the health file"):
        logger.info("create text file in size of 10 MB and replace it with the health file")
        engine.run_cmd("dd if=/dev/urandom bs=1M count=10 | base64 > file.txt")
        engine.run_cmd("sudo cp file.txt /var/log/health_history")

    with allure.step("Wait until file rotation"):
        logger.info("Wait until file rotation")
        system.health.history.wait_until_health_history_file_rotation()

    with allure.step("Validate we have 2 health files"):
        logger.info("Validate we have 2 health files")
        wait_until_expected_health_files_amount(2)

    with allure.step("Validate new file was created"):
        logger.info("Validate new file was created")
        lines = system.health.history.search_line(last_status_line)
        assert len(lines) == 0, "Health file has not changed"

    with allure.step("Validate health status exist in the history file"):
        logger.info("Validate health status exist in the history file")
        health_history_output = system.health.history.show()
        assert system.health.history.get_last_status_from_health_file(health_history_output) == NOT_OK


def sort_monitor_list(monitor_list=None):
    """
    get the monitor list from the "nv show fae health command,
    return a dictionary with all the optional status as keys: [OK, Not OK , Ignored]
    if the status of a device is not one of [OK, Not OK , Ignored], we will consider it as NOT OK.
    :param monitor_list:
    :return:
    """
    if not monitor_list:
        monitor_list = OutputParsingTool.parse_json_str_to_dictionary(Fae().health.show()).get_returned_value()[HealthConsts.MONITOR_LIST]
    status_options = [OK, NOT_OK, IGNORED]
    monitor_dict = {status_key: [] for status_key in status_options}
    for key, value in monitor_list.items():
        status = value[HealthConsts.STATUS]
        assert status in status_options, "{} is not expected status. Expect to be one of them {}".format(status, status_options)
        monitor_dict[status].append(key)
    return monitor_dict


def verify_expected_health_status(health_output_dict, health_status_field, expected_status):
    """
    verify the expected health status
    :param health_output_dict: dictionary of health status. for example from "nv show system health" cmd.
    :param health_status_field: the health status field name. example : "Status"
    :param expected_status: the expected health status. example "Not OK"
    """
    assert expected_status == health_output_dict[health_status_field], \
        "Unexpected health status. \n Expected: {}, but got :{}".format(expected_status, health_output_dict[health_status_field])


@retry(Exception, tries=12, delay=30)
def wait_until_expected_health_files_amount(num_of_expected_files, actual_health_files=None):
    validate_health_files_amount(num_of_expected_files, actual_health_files)


def validate_health_files_amount(num_of_expected_files, actual_health_files=None):
    if not actual_health_files:
        actual_health_files = OutputParsingTool.parse_json_str_to_dictionary(System().health.history.files.show()).get_returned_value()
    assert num_of_expected_files == len(actual_health_files),\
        "Unexpected num of health files.\n Expected: {}, actual files: {}".format(num_of_expected_files, actual_health_files)
