import logging
import pytest
import allure
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.Fae import Fae
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool

logger = logging.getLogger()


@pytest.mark.checklist
@pytest.mark.nvos_ci
@pytest.mark.system
def test_show_system_firmware(devices):
    """
    Show system firmware test

    Test flow:
    1. Run show system firmware
    2. Make sure that all required fields exist
    3. Run show system firmware asic
    4. Compare the output results to the results of show system firmware
    5. Run show system firmware asic <id>
    6. Compare the output results to the results of show system firmware
    """
    validate_show_firmware(devices, is_fae_cmd=False)


@pytest.mark.checklist
@pytest.mark.system
def test_show_fae_firmware(devices):
    """
    Show system firmware test

    Test flow:
    1. Run show fae firmware
    2. Make sure that all required fields exist
    3. Run show fae firmware asic
    4. Compare the output results to the results of show system firmware
    """
    validate_show_firmware(devices, is_fae_cmd=True)


def validate_show_firmware(devices, is_fae_cmd=False):
    system_or_fae_str = "fae" if is_fae_cmd else "system"
    system_or_fae_obj = Fae() if is_fae_cmd else System()
    with allure.step("Run show command to view {} firmware".format(system_or_fae_str)):
        logging.info("Run show command to view {} firmware".format(system_or_fae_str))
        show_output = system_or_fae_obj.firmware.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()

        with allure.step("Validate all expected fields in show output"):
            ValidationTool.verify_field_exist_in_json_output(output_dictionary,
                                                             ["asic", "auto-update", "default"]).verify_result()
            assert output_dictionary["asic"], "'asic' field is empty in show system firmware output"

            with allure.step("Validate asic amount"):
                expected_asic_amount = len(devices.dut.DEVICE_LIST) - 1 if is_fae_cmd else 1
                assert len(output_dictionary["asic"]) == expected_asic_amount, \
                    "Unexpected num of ASIC\n Expected : {}\n but got {}".format(
                    expected_asic_amount, len(output_dictionary["asic"]))

            with allure.step("Validate asic fields"):
                for asic_name, asic_prop in output_dictionary["asic"].items():
                    verify_asic_fields(asic_prop)

            logging.info("All expected fields were found")

        asic_list = output_dictionary["asic"]

    with allure.step("Run show {} firmware asic".format(system_or_fae_str)):
        logging.info("Run show {} firmware asic".format(system_or_fae_str))
        show_output = system_or_fae_obj.firmware.asic.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()

        with allure.step("Validate asic fields"):
            for asic_name, asic_prop in output_dictionary.items():
                verify_asic_fields(asic_prop)

        with allure.step("Compare asic names in outputs"):
            compare_asic_names(asic_list, output_dictionary)

        with allure.step("Compare current output to the output from 'show {} firmware".format(system_or_fae_str)):
            for asic_name, asic_prop in output_dictionary.items():
                compare_asic_fields(asic_list[asic_name], asic_prop)

    if not is_fae_cmd:
        with allure.step("Run show system firmware asic <asic_id>"):
            random_asic = RandomizationTool.select_random_value(list(asic_list.keys())).get_returned_value()
            show_output = system_or_fae_obj.firmware.asic.show(random_asic)
            output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()

            with allure.step("Validate asic fields"):
                verify_asic_fields(output_dictionary)

            with allure.step("Compare asic fields"):
                compare_asic_fields(asic_list[random_asic], output_dictionary)


@pytest.mark.checklist
@pytest.mark.system
def test_set_unset_system_firmware_auto_update(engines):
    """
    set/unset system firmware auto update test

    Test flow:
    1. Disable firmware auto-update and make sure the configuration applied successfully
    2. Enable firmware auto-update and make sure the configuration applied successfully
    3. Disable firmware auto-update and make sure the configuration applied successfully
    4. Unset firmware auto-update and make sure the configuration is updated to default (enable)
    """
    with allure.step("Create System object"):
        system = System()

    with allure.step("Disable firmware auto-update"):
        set_auto_update(system, "disabled")

    with allure.step("Verify the configuration applied successfully - auto-update disabled"):
        verify_firware_value(system, "auto-update", "disabled")

    with allure.step("Enable firmware auto-update"):
        set_auto_update(system, "enabled")

    with allure.step("Verify the configuration applied successfully - auto-update enabled"):
        verify_firware_value(system, "auto-update", "enabled")

    with allure.step("Disable firmware auto-update"):
        set_auto_update(system, "disabled")

    with allure.step("Verify the configuration applied successfully - auto-update disabled"):
        verify_firware_value(system, "auto-update", "disabled")

    with allure.step("Unset auto-update"):
        unset_auto_update(system)

    with allure.step("Verify the configuration applied successfully - auto-update disabled"):
        verify_firware_value(system, "auto-update", "enabled")


@pytest.mark.checklist
@pytest.mark.system
def test_set_unset_system_firmware_default(engines):
    """
    set/unset system firmware default test

    Test flow:
    1. Set firmware default to 'user' and make sure the configuration applied successfully
    2. Set firmware default to 'image' and make sure the configuration applied successfully
    4. Set firmware default to 'user' and make sure the configuration applied successfully
    3. Unset firmware default and make sure the configuration is updated to default (image)
    """
    with allure.step("Create System object"):
        system = System()

    with allure.step("Set firmware default to 'user'"):
        set_firmware_default(system, "user")

    with allure.step("Verify the configuration applied successfully - firmware default is user"):
        verify_firware_value(system, "default", "user")

    with allure.step("Set firmware default to 'image'"):
        set_firmware_default(system, "image")

    with allure.step("Verify the configuration applied successfully - firmware default is user"):
        verify_firware_value(system, "default", "image")

    with allure.step("Set firmware default to 'user'"):
        set_firmware_default(system, "user")

    with allure.step("Verify the configuration applied successfully - firmware default is user"):
        verify_firware_value(system, "default", "user")

    with allure.step("Unset firmware default"):
        unset_firmware_default(system)

    with allure.step("Verify the configuration applied successfully - firmware default is image"):
        verify_firware_value(system, "default", "image")


def set_firmware_default(system, value):
    logging.info("Setting firmware default to '{}'".format(value))
    system.firmware.set("default", value)
    TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(TestToolkit.engines.dut, True)


def unset_firmware_default(system):
    logging.info("Unset firmware default")
    system.firmware.unset("default")
    TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(TestToolkit.engines.dut, True)


def verify_firware_value(system, field_name, expected_value):
    logging.info("Verify the configuration applied successfully")
    show_output = system.firmware.show()
    output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
    ValidationTool.verify_field_value_in_output(output_dictionary, field_name, expected_value).verify_result()


def unset_auto_update(system):
    logging.info('unset firmware auto-update')
    system.firmware.unset("auto-update")
    TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(TestToolkit.engines.dut, True)


def set_auto_update(system, value):
    logging.info('{} firmware auto-update'.format(value))
    system.firmware.set("auto-update", value)
    TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(TestToolkit.engines.dut, True)


def verify_asic_fields(asic_dictionary):
    logging.info("Verify all expected fields are presented in the output")
    ValidationTool.verify_field_exist_in_json_output(asic_dictionary, ["actual-firmware", "installed-firmware",
                                                                       "part-number", "type"]).verify_result()


def compare_asic_names(first_dictionary, second_dictionary):
    logging.info("Compare asic names")
    assert set(first_dictionary.keys()) == set(second_dictionary.keys()), "asic lists are not equal"


def compare_asic_fields(first_dictionary, second_dictionary):
    logging.info("Compare asic fields")
    ValidationTool.compare_dictionaries(first_dictionary, second_dictionary).verify_result()
