import logging
import allure
import pytest
import re
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_constants.constants_nvos import SystemConsts, HealthConsts

logger = logging.getLogger()


OK = "OK"
NOT_OK = "Not OK"
IGNORED = "Ignored"


@pytest.mark.system
@pytest.mark.health
def test_system_health(devices):
    """
    Validate all the show system health commands
        Test flow:
            1. validate nv show system cmd
            2. validate nv show system health cmd
            3. validate nv show system health -w brief cmd
            5. validate nv show system health -w detail cmd
            6. validate nv show system health history cmd
            7. validate nv show system health history files cmd
            8. validate nv show system health history files <file> cmd
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
        verify_expected_health_status(health_output, HealthConsts.STATUS, OK)

    with allure.step("Validate \"nv show system health -w brief\" cmd"):
        logger.info("Validate \"nv show system health -w brief\" cmd")
        brief_health_output = OutputParsingTool.parse_json_str_to_dictionary(system.health.show(" -w brief")).get_returned_value()
        ValidationTool.compare_dictionaries(health_output, brief_health_output).verify_result()

    with allure.step("Validate \"nv show system health -w detail\" cmd"):
        logger.info("Validate \"nv show system health -w detail\" cmd")
        detail_health_output = OutputParsingTool.parse_json_str_to_dictionary(system.health.show(" -w detail")).get_returned_value()
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
        assert get_last_status_from_health_file(health_history_output) == OK, "Last status in the health report file is Not OK but expected to be OK"

    with allure.step("Validate \"nv show system health history files\" cmd"):
        logger.info("Validate \"nv show system health history files\" cmd")
        health_history_files = OutputParsingTool.parse_json_str_to_dictionary(system.health.history.files.show()).get_returned_value()
        files_amount = len(health_history_files)
        assert files_amount in [1, 2], "Unexpected amout of history files.\n Expected: 1 or 2 , but got {}".format(files_amount)
        assert HealthConsts.HEALTH_FIRST_FILE in health_history_files, "Expect to have {} as health file, but have those files {}"\
            .format(HealthConsts.HEALTH_FIRST_FILE, health_history_files)
        if files_amount == 2:
            assert HealthConsts.HEALTH_SECOND_FILE in health_history_files, "Expect to have {} as health file, but have those files {}" \
                .format(HealthConsts.HEALTH_SECOND_FILE, health_history_files)

        health_history_file_output = system.health.history.show_health_report_file(HealthConsts.HEALTH_FIRST_FILE)
        # first line in the health report output is the cmd itself, so we will compared just the file itself.
        assert health_history_file_output.split("\n", 2)[2] == health_history_output.split("\n", 2)[2], "The first health file doesnt show the same info as the default cmd"


def sort_monitor_list(monitor_list=None):
    """
    get the monitor list from the "nv show system health -w detailed command,
    return a dictionary with all the optional status as keys: [OK, Not OK , Ignored]
    if the status of a device is not one of [OK, Not OK , Ignored], we will consider it as NOT OK.
    :param monitor_list:
    :return:
    """
    if not monitor_list:
        monitor_list = OutputParsingTool.parse_json_str_to_dictionary(System().health.show("-w detailed")).get_returned_value()[HealthConsts.MONITOR_LIST]
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


def search_line_in_health_report_file(line_to_search, file_output=None):
    if not file_output:
        file_output = OutputParsingTool.parse_json_str_to_dictionary(System().health.history.show()).get_returned_value()
    return re.findall(line_to_search, file_output)


def get_last_status_from_health_file(file_output=None):
    last_status = search_line_in_health_report_file(".*summary:.*OK", file_output)[-1]
    logger.info("last status line is: \n {}".format(last_status))
    return NOT_OK if "Not OK" in last_status else OK


'''
def validate_health_files_amount(num_of_expected_files, actual_health_files=None):
    if not actual_health_files:
        actual_health_files = OutputParsingTool.parse_json_str_to_dictionary(System().health.history.files.show()).get_returned_value()
    assert num_of_expected_files == len(actual_health_files), "Unexpected num of health files.\n Expected: {}, actual files: {}".format(num_of_expected_files, actual_health_files)


def create_health_issue_with_user_config_file(engine, device):
    # create a file
    checker_file = "/tmp/my_checker.py"
    create_my_checker_file_cmd = "echo -e 'print(\"MyCategory\") \nprint(\"device1:OK\") \nprint(\"device2:device2 is out of power\")' > {}".format(checker_file)
    engine.run_cmd(create_my_checker_file_cmd)

    # update config file
    line_to_replce = "\"user_defined_checkers\": [{}]"

    engine.run_cmd("sed 's/{}/{}/' {}".format(line_to_replce.format(""), line_to_replce.format("\"python {}\"".format(checker_file)), device.health_monitor_config_file_path))
    return {"device1": "OK", "device2":"device2 is out of power"}
'''
