import logging
import pytest
import allure
from ngts.nvos_tools.system.System import System
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool

logger = logging.getLogger()


@pytest.mark.system
def test_show_log(engines):
    """
    Write to log file on switch, run nv show system log command and verify system/images are exist
    command: nv show system log

    Test flow:
        1. Rotate logs
        2. Run show system images
        3. Run nv show system log
        4. Check if we have in the logs 'regular_log' message
    """
    with allure.step("Create System object"):
        system = System(None)

    with allure.step("Rotate logs"):
        logging.info("Rotate logs")
        system.log.rotate_logs()

    with allure.step("Run show command to view system images"):
        logging.info("Run show command to view system images")
        system.images.show()

    with allure.step("Run nv show system log command follow to view system logs"):
        logging.info("Run nv show system log command follow to view system logs")
        show_output = system.log.show_log(exit_cmd='q')

    with allure.step('Verify updated “system/images” in the logs as expected'):
        logging.info('Verify updated “system/images” in the logs as expected')
        ValidationTool.verify_expected_output(show_output, 'system/images').verify_result()


@pytest.mark.system
def test_show_log_continues(engines):
    """
    Write to log file on switch, run nv show system log command and verify system/images are exist
    command: nv show system log --view follow

    Test flow:
        1. Rotate logs
        2. Run show system images
        3. Run nv show system log --view follow
        4. Check if we have in the logs 'regular_log' message
    """
    with allure.step("Create System object"):
        system = System()

    with allure.step("Rotate logs"):
        logging.info("Rotate logs")
        system.log.rotate_logs()

    with allure.step("Run show command to view system images"):
        logging.info("Run show command to view system images")
        system.images.show()

    with allure.step("Run nv show system log command --view follow to view system logs"):
        logging.info("Run nv show system log command --view follow to view system logs")
        show_output = system.log.show_log(param='--view follow', exit_cmd='\x03')

    with allure.step('Verify updated “system/images” in the logs as expected'):
        logging.info('Verify updated “system/images” in the logs as expected')
        ValidationTool.verify_expected_output(show_output, 'system/images').verify_result()


@pytest.mark.system
def test_show_log_files(engines):
    """
    Check all fields in files commands, write to log check it exist in show files command

    Test flow:
        1. Run nv show system log files command and validate fields
        2. Rotate logs
        3. Run show system images
        4. Check if we have in the logs 'system/images' message
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

    with allure.step("Run show command to view system images"):
        logging.info("Run show command to view system images")
        system.images.show()

    with allure.step("Run nv show system log files command follow to view system logs"):
        logging.info("Run nv show system log files command follow to view system logs")
        show_log_files_output = system.log.files.show_log_files(param='files syslog', exit_cmd='q')

    with allure.step('Verify updated “system/images” in the logs as expected'):
        logging.info('Verify updated “system/images” in the logs as expected')
        ValidationTool.verify_expected_output(show_log_files_output, 'system/images').verify_result()


@pytest.mark.system
def test_show_debug_log(engines):
    """
    Check version on switch, run nv show system log command and verify the images method are exist
    command: nv show system debug-log

    Test flow:
        1. Write to debug log message
        2. Check if message exist in debug log
    """
    with allure.step("Create System object"):
        system = System(None)

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
        1. Write to debug log message
        2. Check if message exist in debug log with continues command
    """
    with allure.step("Create System object"):
        system = System()

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


@pytest.mark.system
def test_log_files_rotation_default_fields(engines):
    """
    Check all fields and default values exist in nv show system log files rotation
    command: nv show system log files rotation

    Test flow:
        1. Verify all fields in command
        2. Verify all default values
    """
    with allure.step("Create System object"):
        system = System(None)

    with allure.step("Run nv show system log rotation command and validate fields"):
        logging.info("Run nv show system log rotation command and validate fields")
        show_output = system.log.rotation.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()

        with allure.step("Validate all expected fields in show output"):
            ValidationTool.verify_field_exist_in_json_output(output_dictionary,
                                                             ["frequency", 'max-number', 'size']).verify_result()
            logging.info("All expected fields were found")

    with allure.step("Verify default values"):
        ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                    field_name="frequency", expected_value="daily")

        ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                    field_name='max-number', expected_value="20")

        ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                    field_name='size', expected_value="10.0")


@pytest.mark.system
def test_log_files_set_unset_log_rotation_frequency(engines):
    """
    Check set unset for files rotation parameters
    command: nv set/unset system log rotation command

    Test flow:
        1. Get default values for rotation frequency
        2. Negative testing for frequency
        3. Validate set, unset for frequency
    """
    list_with_possible_frequency = ['daily', 'weekly', 'monthly', 'yearly']
    with allure.step("Create System object"):
        system = System(None)

    with allure.step("Run nv show system log rotation command"):
        logging.info("Run nv show system log rotation command")
        show_output = system.log.rotation.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()

    with allure.step("Get default values for rotation frequency"):
        logging.info("Get default values for rotation frequency")
        show_output = system.log.rotation.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        default_frequency = output_dictionary['frequency']

    with allure.step('Negative validation for frequency with invalid value'):
        system.log.rotation.set('frequency', 'invalid').verify_result(False)

    with allure.step("Validate configure all possible frequency"):
        logging.info("Validate configure all possible frequency")
        for frequency in list_with_possible_frequency:
            system.log.rotation.set('frequency', frequency)
            NvueGeneralCli.apply_config(engines.dut)
            show_output = system.log.rotation.show()
            output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
            ValidationTool.verify_field_value_in_output(output_dictionary, 'frequency', frequency)

    with allure.step("Validate unset frequency"):
        logging.info("Validate unset frequency")
        system.log.rotation.unset('frequency')
        NvueGeneralCli.apply_config(engines.dut)
        show_output = system.log.rotation.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        ValidationTool.verify_field_value_in_output(output_dictionary, 'frequency', default_frequency)


@pytest.mark.system
def test_log_files_set_unset_log_rotation_size_disk_percentage(engines):
    """
    Check set unset for files rotation file size and disk percentage
    command: nv set/unset system log rotation size and sick-percentage

    Test flow:
        1. Negative testing for log file size
        2. Set, unset for log file size
        3. Positive and negative testing for disk percentage parameter
    """
    with allure.step("Create System object"):
        system = System(None)

    with allure.step("Negative validation for rotation size"):
        logging.info("Negative validation for rotation size")
        show_output = system.log.rotation.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        default_size = output_dictionary['size']
        system.log.rotation.set('size', '0.0001').verify_result(False)
        system.log.rotation.set('size', '3500.01').verify_result(False)

    with allure.step("Validate all posible rotation size"):
        logging.info("Validate all posible rotation size")
        system.log.rotation.set('size', '0.001')
        NvueGeneralCli.apply_config(engines.dut)
        show_output = system.log.rotation.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        ValidationTool.verify_field_value_in_output(output_dictionary, 'size', '0.001')

        system.log.rotation.set('size', '3499.999')
        NvueGeneralCli.apply_config(engines.dut)
        show_output = system.log.rotation.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        ValidationTool.verify_field_value_in_output(output_dictionary, 'size', '3499.999')

    with allure.step("Negative validation disk percentage configuration"):
        logging.info("Negative validation disk percentage configuration")
        system.log.rotation.set('disk-percentage', '0.0001').verify_result(False)
        system.log.rotation.set('disk-percentage', '100.001').verify_result(False)

    with allure.step("Validate disk percentage configuration"):
        logging.info("Validate disk percentage configuration")
        system.log.rotation.set('disk-percentage', '50')
        NvueGeneralCli.apply_config(engines.dut)
        show_output = system.log.rotation.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        ValidationTool.verify_field_value_in_output(output_dictionary, 'size', '1750')
        ValidationTool.verify_field_value_in_output(output_dictionary, 'disk-percentage', '50.0')

        logging.info("Validate disk percentage configuration with lowest value")
        system.log.rotation.set('disk-percentage', '0.001')
        NvueGeneralCli.apply_config(engines.dut)
        show_output = system.log.rotation.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        ValidationTool.verify_field_value_in_output(output_dictionary, 'size', '0.035')
        ValidationTool.verify_field_value_in_output(output_dictionary, 'disk-percentage', '0.001')

        logging.info("Validate disk percentage configuration with highest value")
        system.log.rotation.set('disk-percentage', '100')
        NvueGeneralCli.apply_config(engines.dut)
        show_output = system.log.rotation.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        ValidationTool.verify_field_value_in_output(output_dictionary, 'size', '3500')
        ValidationTool.verify_field_value_in_output(output_dictionary, 'disk-percentage', '3500')

    with allure.step("Validate unset log rotation"):
        logging.info("Validate unset log rotation")
        system.log.rotation.unset()
        NvueGeneralCli.apply_config(engines.dut)
        show_output = system.log.rotation.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        ValidationTool.verify_field_value_in_output(output_dictionary, 'size', default_size)


@pytest.mark.system
def test_log_files_set_unset_log_rotation_max_number(engines):
    """
    Check set unset for files rotation max-number
    command: nv set/unset system log rotation max-number

    Test flow:
        1. Negative validation for max-number
        2. Set possible value to max-number
        1. Log rotation max-number testing with files
        2. Unset log rotation and check default parameters
    """
    with allure.step("Create System object"):
        system = System(None)

    with allure.step("Negative validation for log rotation max-number"):
        logging.info("Negative validation for log rotation max-number")
        show_output = system.log.rotation.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        default_max_number = output_dictionary['max-number']
        system.log.rotation.set('max-number', '0.001').verify_result(False)
        system.log.rotation.set('max-number', '9999999').verify_result(False)

    with allure.step("Validate set max-number 5"):
        logging.info("Validate set max-number 5")
        system.log.rotation.set('max-number', 5)
        NvueGeneralCli.apply_config(engines.dut)
        show_output = system.log.rotation.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        ValidationTool.verify_field_value_in_output(output_dictionary, 'max-number', '5')

        logging.info("Rotate log 5 times to check functionality of max-number")
        system.log.rotate_logs()
        system.log.rotate_logs()
        system.log.rotate_logs()
        system.log.rotate_logs()
        system.log.rotate_logs()

        logging.info("Check we have 5 log files")
        show_output = system.log.files.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        assert len(output_dictionary.keys()) >= 6
        assert list(output_dictionary.keys())[-1] == 'syslog.5.gz'

    with allure.step("Validate set max-number 1"):
        logging.info("Validate set max-number 1")
        system.log.rotation.set('max-number', 1)
        NvueGeneralCli.apply_config(engines.dut)
        show_output = system.log.rotation.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        ValidationTool.verify_field_value_in_output(output_dictionary, 'max-number', '1')

        logging.info("Rotate log 1 time to check functionality of max-number")
        system.log.rotate_logs()

        logging.info("Check we have 1 log files")
        show_output = system.log.files.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        assert len(output_dictionary.keys()) == 2
        assert list(output_dictionary.keys())[-1] == 'syslog.1.gz'

    with allure.step("Validate unset log rotation"):
        logging.info("Validate unset log rotation")
        system.log.rotation.unset()
        NvueGeneralCli.apply_config(engines.dut)
        show_output = system.log.rotation.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        ValidationTool.verify_field_value_in_output(output_dictionary, 'max-number', default_max_number)


@pytest.mark.system
def test_log_files_rotation_force(engines):
    """
    Check version on switch, rotate logs, check that it doesn't exist in the logs
    command: nv action system log rotation force

    Test flow:
        1. Run show system images
        2. Rotate logs
        3. Run nv show system log
        4. Check if we have in the logs 'regular_log' message
    """
    with allure.step("Create System object"):
        system = System(None)

    with allure.step("Run show command to view system images"):
        logging.info("Run show command to view system images")
        system.images.show()

    with allure.step("Rotate logs"):
        logging.info("Rotate logs")
        system.log.rotate_logs()

    with allure.step("Run nv show system log command follow to view system logs"):
        logging.info("Run nv show system log command follow to view system logs")
        show_output = system.log.show_log(exit_cmd='q')

    with allure.step('Verify updated “system/images” in the logs as expected'):
        logging.info('Verify updated “system/images” in the logs as expected')
        ValidationTool.verify_expected_output(show_output, 'system/images').verify_result(False)


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


@pytest.mark.system
def test_upload_log_files(engines, topology_obj):
    """
    Check uploading log files to shared location and validate
    command: nv action upload system log file

    Test flow:
        1. Upload log file to shared location
        2. Validate it uploaded
        3. Delete from shared location
        4. Check if in history login and password hided
    """
    player = topology_obj.players['ha']['engine']
    with allure.step("Create System object"):
        system = System(None)

    with allure.step("Get and upload log file"):
        logging.info("Get and upload log file")
        show_output = system.log.files.show()
        log_files_dict = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        log_file = list(log_files_dict.keys())[-1]
        upload_path = 'scp://{}:{}@{}/root/{}'.format(player.username, player.password, player.ip, log_file)
        system.log.files.action_upload(logging_file=log_file, upload_path=upload_path)

    with allure.step("Check if file uploaded and delete it from player"):
        logging.info("Check if file uploaded and delete it from player")
        assert player.run_cmd(cmd='ls -la | grep {}'.format(log_file))
        player.run_cmd(cmd='rm -f {}'.format(log_file))

    with allure.step("Run nv show system log command to check if command with password hiden"):
        logging.info("Run nv show system log command to check if command with password hiden")
        show_output = system.log.show_log(exit_cmd='q')
        ValidationTool.verify_expected_output(show_output, upload_path).verify_result(False)


@pytest.mark.system
def test_delete_log_files(engines):
    """
    Check user can delete debug-log files
    command: nv action delete system log file

    Test flow:
        1. Rotate log to create log files and check created
        2. Get all log files and check we can delete it
        3. Check we didn't delete all log files
        4. Run show system images
        5. Check it exist in log
    """
    with allure.step("Create System object"):
        system = System(None)

    with allure.step("Rotate log 5 times to create log files"):
        logging.info("Rotate log 5 times to create log files")
        system.log.rotate_logs()
        system.log.rotate_logs()
        system.log.rotate_logs()
        system.log.rotate_logs()
        system.log.rotate_logs()

        logging.info("Check we have 5 log files")
        show_output = system.log.files.show()
        log_files_dict = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        assert len(log_files_dict.keys()) >= 6

    with allure.step("Delete all log files and validate"):
        logging.info("Delete all log files and validate")
        for log_file in log_files_dict.keys():
            system.log.files.action_delete(logging_file=log_file)
            show_output = system.log.files.show()
            output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
            assert log_file not in output_dictionary.keys()

    with allure.step("Check we didn't delete all log files"):
        logging.info("Check we didn't delete all log files")
        show_output = system.log.files.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        assert 'syslog' in output_dictionary.keys()
        assert len(output_dictionary.keys()) >= 1

    with allure.step("Run show command to view system images"):
        logging.info("Run show command to view system images")
        system.images.show()

    with allure.step("Run nv show system log command follow to view system logs"):
        logging.info("Run nv show system log command follow to view system logs")
        show_output = system.log.show_log(exit_cmd='q')

    with allure.step('Verify updated “system/images” in the logs as expected'):
        logging.info('Verify updated “system/images” in the logs as expected')
        ValidationTool.verify_expected_output(show_output, 'system/images').verify_result()
