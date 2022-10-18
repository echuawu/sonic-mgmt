import logging
import pytest
import allure
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_constants.constants_nvos import PlatformConsts
from ngts.nvos_constants.constants_nvos import OutputFormat

logger = logging.getLogger()


@pytest.mark.platform
def test_show_platform_environment(engines):
    """
    Show platform environment test
    """
    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Execute show platform environment and make sure all the components exist"):
        _verify_output(platform, "", PlatformConsts.ENV_COMP)


@pytest.mark.platform
def test_show_platform_environment_fan(engines, devices):
    """
    Show platform environment fan test
    """
    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Execute show platform environment fan and make sure all the components exist"):
        output = _verify_output(platform, "fan", devices.dut.psu_list + devices.dut.fan_list)

    with allure.step("Check that all required properties for each fan"):
        logging.info("Check that all required properties for each fan")
        for fan, fan_prop in output.items():
            _verify_fan_prop(fan, fan_prop.keys())


@pytest.mark.platform
def test_show_platform_environment_led(engines, devices):
    """
    Show platform environment led test
    """
    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Execute show platform environment led and make sure all the components exist"):
        output = _verify_output(platform, "led", devices.dut.fan_list + PlatformConsts.ENV_LED_COMP)

    with allure.step("Check that all required properties for each led"):
        logging.info("Check that all required properties for each led")
        for led, led_prop in output.items():
            _verify_led_prop(led, led_prop)


@pytest.mark.platform
def test_show_platform_environment_psu(engines, devices):
    """
    Show platform environment psu test
    """
    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Execute show platform environment psu and make sure all the components exist"):
        output = _verify_output(platform, "psu", devices.dut.psu_list)

    with allure.step("Check that all required properties for each psu"):
        logging.info("Check that all required properties for each psu")
        for psu, psu_prop in output.items():
            _verify_psu_prop(psu, psu_prop)


@pytest.mark.platform
def test_show_platform_environment_temperature(engines, devices):
    """
    Show platform environment temperature test
    """
    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Execute show platform environment temperature and make sure all the components exist"):
        output = _verify_output(platform, "temperature", devices.dut.temperature_list)

    with allure.step("Check that all required properties for each temperature"):
        logging.info("Check that all required properties for each temperature")
        for temp, temp_prop in output.items():
            _verify_temp_prop(temp, temp_prop)

    if "SODIMM 1 Temp" in output.keys():
        with allure.step('Verify "SODIMM 1 Temp" values'):
            _verify_temp_prop("SODIMM 1 Temp", output["SODIMM 1 Temp"])


def _verify_temp_prop(temp, temp_prop):
    logging.info("temp {}".format(temp))
    list_of_keys = temp_prop.keys()
    assert "state" in list_of_keys and "current" in list_of_keys, "state/current can't be found"

    if "max" in list_of_keys:
        value = temp_prop["max"]
        assert isinstance(value, int), "the max temperature value is not integer"

    if "crit" in list_of_keys:
        value = temp_prop["crit"]
        assert isinstance(value, int), "the critical temperature value is not integer"
        assert "max" in list_of_keys, "max temperature value is missing"
        assert int(value) >= int(temp_prop["max"]), "the critical temperature < max temperature"


def _verify_output(platform, comp_name, req_fields):
    logging.info("Required comp: " + str(req_fields))
    with allure.step("Verify text output"):
        logging.info("Verify text output")
        output = platform.environment.show(comp_name, output_format=OutputFormat.auto)
        assert not any(comp not in output for comp in req_fields), "Not all required component were found"

    with allure.step("Verify json output"):
        logging.info("Verify json output")
        output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
            platform.environment.show(comp_name)).verify_result()
        Tools.ValidationTool.verify_field_exist_in_json_output(output, req_fields).verify_result()

    return output


def _verify_fan_prop(fan, fan_prop):
    logging.info("fan {}".format(fan))
    assert not any(comp not in fan_prop for comp in PlatformConsts.ENV_FAN_COMP), \
        "Not all required component were found"


def _verify_led_prop(led, led_prop):
    logging.info("led {}".format(led))
    assert PlatformConsts.ENV_LED_COLOR_LABEL in led_prop.keys(), \
        PlatformConsts.ENV_LED_COLOR_LABEL + " not found for " + led
    assert led_prop[PlatformConsts.ENV_LED_COLOR_LABEL].lower() in PlatformConsts.ENV_LED_COLOR_OPTIONS,\
        led_prop[PlatformConsts.ENV_LED_COLOR_LABEL] + "is not a legal value"


def _verify_psu_prop(psu, psu_prop):
    logging.info("psu {}".format(psu))
    Tools.ValidationTool.verify_field_exist_in_json_output(psu_prop, PlatformConsts.ENV_PSU_PROP).verify_result()
