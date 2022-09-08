import logging
import pytest
import allure
from ngts.nvos_tools.system.System import System

from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool

logger = logging.getLogger()


@pytest.mark.system
def test_show_log(engines):
    """
    Write to log file on switch, run nv show system log command and verify regular_log are exist
    command: nv show system log

    Test flow:
        1. Rotate logs
        2. Write to log
        3. Run nv show system log
        4. Check if we have in the logs 'regular_log' message
    """
    with allure.step("Create System object"):
        system = System(None)

    with allure.step("Rotate logs"):
        logging.info("Rotate logs")
        system.log.rotate_logs()

    with allure.step("Write to system log file"):
        logging.info("Write to system log file")
        system.log.write_to_log()

    with allure.step("Run nv show system log command follow to view system logs"):
        logging.info("Run nv show system log command follow to view system logs")
        show_output = system.log.show_log(exit_cmd='q')

    with allure.step('Verify updated “regular_log” in the logs as expected'):
        logging.info('Verify updated “regular_log” in the logs as expected')
        ValidationTool.verify_expected_output(show_output, 'regular_log').verify_result()


@pytest.mark.system
def test_show_log_continues(engines):
    """
    Write to log file on switch, run nv show system log command and verify regular_log are exist
    command: nv show system log --view follow

    Test flow:
        1. Rotate logs
        2. Write to log
        3. Run nv show system log --view follow
        4. Check if we have in the logs 'regular_log' message
    """
    with allure.step("Create System object"):
        system = System()

    with allure.step("Rotate logs"):
        logging.info("Rotate logs")
        system.log.rotate_logs()

    with allure.step("Write to system log file"):
        logging.info("Write to system log file")
        system.log.write_to_log()

    with allure.step("Run nv show system log command --view follow to view system logs"):
        logging.info("Run nv show system log command --view follow to view system logs")
        show_output = system.log.show_log(param='--view follow', exit_cmd='\x03')

    with allure.step('Verify updated “regular_log” in the logs as expected'):
        logging.info('Verify updated “regular_log” in the logs as expected')
        ValidationTool.verify_expected_output(show_output, 'regular_log').verify_result()


@pytest.mark.system
def test_show_log_files(engines):
    """
    Check all fields in files commands, write to log check it exist in show files command

    Test flow:
        1. Run nv show system log files command and validate fields
        2. Rotate logs
        3. Write to log
        4. Check if we have in the logs 'regular_log' message
    """
    with allure.step("Create System object"):
        system = System(None)

    with allure.step("Run nv show system log files command and validate fields"):
        logging.info("Run nv show system log files command and validate fields")
        show_output = system.log.files.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()

        with allure.step("Validate all expected fields in show output"):
            ValidationTool.verify_field_exist_in_json_output(output_dictionary,
                                                             ["syslog"]).verify_result()
            logging.info("All expected fields were found")

    with allure.step("Rotate logs"):
        logging.info("Rotate logs")
        system.log.rotate_logs()

    with allure.step("Write to system log file"):
        logging.info("Write to system log file")
        system.log.write_to_log()

    with allure.step("Run nv show system log files command follow to view system logs"):
        logging.info("Run nv show system log files command follow to view system logs")
        show_log_files_output = system.log.files.show_log_files(param='files syslog', exit_cmd='q')

    with allure.step('Verify updated “regular_log” in the logs as expected'):
        logging.info('Verify updated “regular_log” in the logs as expected')
        ValidationTool.verify_expected_output(show_log_files_output, 'regular_log').verify_result()


@pytest.mark.system
def test_show_debug_log(engines):
    """
    Check version on switch, run nv show system log command and verify the images method are exist
    command: nv show system debug-log

    Test flow:
        1. Rotate debug logs
        2. Write to debug log message
        3. Check if message exist in debug log
    """
    with allure.step("Create System object"):
        system = System(None)

    with allure.step("Rotate debug-logs"):
        logging.info("Rotate debug-logs")
        system.debug_log.rotate_debug_logs()

    with allure.step("Write debug_log message to debug-log"):
        logging.info("Write debug_log message to debug-log")
        system.debug_log.write_to_debug_log()

    with allure.step("Run nv show system debug-log command follow to view system logs"):
        logging.info("Run nv show system debug-log command follow to view system logs")
        show_output = system.debug_log.show_log(log_type='debug-', exit_cmd='q')

    with allure.step('Verify debug_log message in log as expected'):
        logging.info('Verify debug_log message in log as expected')
        ValidationTool.verify_expected_output(show_output, 'debug_log').verify_result()


@pytest.mark.system
def test_show_debug_log_continues(engines):
    """
    Check version on switch, run nv show system log command and verify the images method are exist
    command: nv show system debug-log --view follow

    Test flow:
        1. Rotate debug logs
        2. Write to debug log message
        3. Check if message exist in debug log with continues command
    """
    with allure.step("Create System object"):
        system = System()

    with allure.step("Rotate logs"):
        logging.info("Rotate logs")
        system.debug_log.rotate_debug_logs()

    with allure.step("Write to the logs debug_log message"):
        logging.info("Write to the logs debug_log message")
        system.debug_log.write_to_debug_log()

    with allure.step("Run nv show system log command --view follow to view system logs"):
        logging.info("Run nv show system log command --view follow to view system logs")
        show_output = system.debug_log.show_log(log_type='debug-', param='--view follow', exit_cmd='\x03')

    with allure.step('Verify updated “debug_log” in the logs as expected'):
        logging.info('Verify updated “debug_log” in the logs as expected')
        ValidationTool.verify_expected_output(show_output, 'debug_log').verify_result()


@pytest.mark.system
def test_show_debug_log_files(engines):
    """
    Check all fields in debug-log filles command

    Test flow:
        1. Run nv show system debug-log files command and validate fields
    """
    with allure.step("Create System object"):
        system = System(None)

    with allure.step("Run show command log files command to check fields"):
        logging.info("Run show command log files command to check fields")
        show_output = system.debug_log.files.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()

        with allure.step("Validate all expected fields in show output"):
            ValidationTool.verify_field_exist_in_json_output(output_dictionary,
                                                             ["debug"]).verify_result()
            logging.info("All expected fields were found")


def test_log_files_rotation_default_fields(engines):
    """
    Check all fields exist in nv show system log files rotation
    command: nv show system log files rotation

    Test flow:
        1.
        2.
        3.
    """
    # FIX_ME


def test_log_files_set_unset_log_rotation(engines):
    """
    Check set/uset for filesrotation command
    command: nv set/unset system log rotation command

    Test flow:
        1.
        2.
        3.
    """
    # FIX_ME


def test_log_files_rotation_force(engines):
    """
    Check version on switch, rotate logs, check that it doesn't exist in the logs
    command: nv action system log rotation force

    Test flow:
        1.
        2.
        3.
    """
    # FIX_ME


@pytest.mark.system
def test_log_components(engines):
    """
    Check all fields in components command, check all components can be set/uset with all log levels

    Test flow:
        1. Run show system log component and validate all fields
        2. Run nv show system component and check default log levels for all components
        3. Run nv set/unset for all components with all log levels and validate
    """
    list_with_all_components = ["nvued", "orchagent", "portsyncd", "sai_api_port", "sai_api_switch", "syncd"]
    list_with_all_log_levels = ["critical", "debug", "error", "info", "notice", "warn"]
    with allure.step("Create System object"):
        system = System(None)

    with allure.step("Run show command to view system images"):
        logging.info("Run show command to view system images")
        show_output = system.log.component.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()

        with allure.step("Validate all expected fields in show component output"):
            ValidationTool.verify_field_exist_in_json_output(output_dictionary, list_with_all_components).verify_result()
            logging.info("All expected fields were found")

    with allure.step("Validate default log levels for all components"):
        logging.info("Validate default log levels for all components")
        for component in list_with_all_components:
            default_log_level = "notice"
            if component == "nvued":
                default_log_level = "info"
            with allure.step("Validate component {component} with default log level {level}"
                             .format(component=component, level=default_log_level)):
                ValidationTool.verify_field_value_in_output(output_dictionary[component], "level", default_log_level)
                logging.info("All expected components were with default log levels")

    with allure.step("Rotate logs"):
        logging.info("Rotate logs")
        system.log.rotate_logs()

    with allure.step("Validate all log levels can be applied for all components"):
        logging.info("Validate all log levels can be applied for all components")
        for component in list_with_all_components:
            for log_level in list_with_all_log_levels:
                if component == "nvued" and log_level == "notice":
                    continue
                system.log.component.set_system_log_component(component, log_level)
                show_output = system.log.component.show()
                output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
                ValidationTool.verify_field_value_in_output(output_dictionary[component], "level", log_level)
                if component == "nvued" and log_level is list_with_all_log_levels[-1]:
                    default_log_level_nvued = "info"
                    system.log.component.set_system_log_component(component, default_log_level_nvued)
                else:
                    system.log.component.unset_system_log_component(component)
                    show_output = system.log.component.show()
                    output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
                    ValidationTool.verify_field_value_in_output(output_dictionary[component], "level", default_log_level)


def test_upload_log_files(engines):
    """
    Check uploading log files to shared location and validate
    command: nv action upload system log file

    Test flow:
        1.
        2.
        3.
    """
    # FIX_ME
    with allure.step("Create System object"):
        system = System(None)

    with allure.step("Uploading log files"):
        logging.info("Uploading log files")
        system.log.files.action_upload()


def test_delete_log_files(engines):
    """
    Check user can delete debug-log files
    command: nv action delete system log file

    Test flow:
        1.
        2.
        3.
    """
    # FIX_ME
    with allure.step("Create System object"):
        system = System(None)

    with allure.step("Delete log files"):
        logging.info("Delete log files")
        system.log.files.action_delete()
