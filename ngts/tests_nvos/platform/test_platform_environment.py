import logging
import pytest
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import PlatformConsts
from ngts.nvos_constants.constants_nvos import OutputFormat
from ngts.nvos_constants.constants_nvos import ApiType

logger = logging.getLogger()


@pytest.mark.platform
@pytest.mark.simx
@pytest.mark.nvos_ci
@pytest.mark.cumulus
@pytest.mark.nvos_chipsim_ci
def test_show_platform_environment(engines, devices):
    """
    Show platform environment test
    """
    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Execute show platform environment and make sure all the components exist"):
        _verify_output(platform, "", devices.dut.platform_environment_list)


@pytest.mark.platform
@pytest.mark.cumulus
def test_show_platform_environment_fan(engines, devices):
    """
    Show platform environment fan test
    """
    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Execute show platform environment fan and make sure all the components exist"):
        output = _verify_output(platform, "fan", devices.dut.psu_fan_list + devices.dut.fan_list)

    with allure.step("Check that all required properties for each fan"):
        logging.info("Check that all required properties for each fan")
        for fan, fan_prop in output.items():
            _verify_fan_prop(fan, fan_prop.keys(), devices)

    with allure.step("Check output of a specific Fan"):
        fan_to_check = list(output.keys())[0]
        output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
            platform.environment.show(op_param="fan {}".format(fan_to_check))).verify_result()
        _verify_fan_prop(fan_to_check, output.keys(), devices)


@pytest.mark.platform
@pytest.mark.cumulus
def test_show_platform_environment_led(engines, devices):
    """
    Show platform environment led test
    """
    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Execute show platform environment led and make sure all the components exist"):
        output = _verify_output(platform, "led", devices.dut.fan_led_list)

    with allure.step("Check that all required properties for each led"):
        logging.info("Check that all required properties for each led")
        for led, led_prop in output.items():
            _verify_led_prop(led, led_prop)

    with allure.step("Check output of a specific Led"):
        led_to_check = list(output.keys())[0]
        output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
            platform.environment.show(op_param="led '{}'".format(led_to_check))).verify_result()
        _verify_led_prop(led_to_check, output)


@pytest.mark.platform
def test_set_platform_environment_led(engines, devices):
    """
    Set platform environment led test

    Test flow:
    1. Check all leds are green by default exclude UID
    2. Negative testing, try to turn off leds, which we can't, check value didn't change
    3. Turn-on UID led and check led is green
    4. Unset it and check it returned to default values
    """
    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Execute show platform environment led and make sure all the components exist"):
        output = _verify_output(platform, "led", devices.dut.fan_led_list + PlatformConsts.ENV_LED_COMP)

    with allure.step("Check that all leds are green and UID off by default"):
        logging.info("Check that all leds are green and UID off by default")
        for led, led_prop in output.items():
            _verify_led_color(led, led_prop)

    with allure.step("Negative set off to FAN or PSU"):
        logging.info("Negative set off to FAN or PSU")
        should_succeed = True
        for led, led_prop in output.items():
            if led == PlatformConsts.ENV_UID:
                continue
            if TestToolkit.tested_api != "OpenApi":
                should_succeed = False
            platform.environment.action_turn(turn_type=PlatformConsts.ENV_LED_COLOR_OFF, led=led)\
                .verify_result(should_succeed)

    with allure.step("Check that all leds are green and UID off by default"):
        logging.info("Check that all leds are green and UID off by default")
        for led, led_prop in output.items():
            _verify_led_color(led, led_prop)

    with allure.step("Change UID state led to on"):
        logging.info("Check UID state led to on")
        platform.environment.action_turn(turn_type=PlatformConsts.ENV_LED_TURN_ON, led=PlatformConsts.ENV_UID)
        output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
            platform.environment.show('led')).verify_result()
        Tools.ValidationTool.compare_values(output['UID']['color'], PlatformConsts.ENV_LED_COLOR_BLUE, True)\
            .verify_result()

    with allure.step("Change UID state led to off"):
        logging.info("Change UID state led to off")
        platform.environment.action_turn(turn_type=PlatformConsts.ENV_LED_COLOR_OFF, led=PlatformConsts.ENV_UID)
        output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
            platform.environment.show('led')).verify_result()
        Tools.ValidationTool.compare_values(output['UID']['color'], PlatformConsts.ENV_LED_COLOR_OFF, True) \
            .verify_result()

    with allure.step("Check that all leds are green and UID off after unset"):
        logging.info("Check that all leds are green and UID off after unset")
        for led, led_prop in output.items():
            _verify_led_color(led, led_prop)


@pytest.mark.platform
@pytest.mark.cumulus
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
            _verify_psu_prop(psu, psu_prop, devices)

    with allure.step("Check output of a specific PSU"):
        psu_to_check = list(output.keys())[0]
        output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
            platform.environment.show(op_param="psu {}".format(psu_to_check))).verify_result()
        _verify_psu_prop(psu_to_check, output, devices)


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

    with allure.step("Check output of a specific temperature comp"):
        temperature_to_check = list(output.keys())[0]
        output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
            platform.environment.show(op_param="temperature {}".format(temperature_to_check))).verify_result()
        _verify_temp_prop(temperature_to_check, output)


def _verify_temp_prop(temp, temp_prop):
    logging.info("temp {}".format(temp))
    list_of_keys = temp_prop.keys()
    assert "state" in list_of_keys and "current" in list_of_keys, "state/current can't be found"

    if "max" in list_of_keys:
        value = temp_prop["max"]
        assert _get_float(value) or "N/A" in value, "the max temperature value is invalid"

    if "crit" in list_of_keys:
        value = temp_prop["crit"]
        assert _get_float(value) or "N/A" in value, "the critical temperature value is invalid"
        assert "max" in list_of_keys, "max temperature value is missing"
        assert _get_float(value) >= float(temp_prop["max"]), "the critical temperature < max temperature"


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


def _verify_fan_prop(fan, fan_prop, devices):
    logging.info("fan {}".format(fan))
    assert not any(comp not in fan_prop for comp in devices.dut.fan_prop), \
        "Not all required component were found"


def _verify_led_prop(led, led_prop):
    logging.info("led {}".format(led))
    assert PlatformConsts.ENV_LED_COLOR_LABEL in led_prop.keys(), \
        PlatformConsts.ENV_LED_COLOR_LABEL + " not found for " + led
    assert led_prop[PlatformConsts.ENV_LED_COLOR_LABEL].lower() in PlatformConsts.ENV_LED_COLOR_OPTIONS, \
        led_prop[PlatformConsts.ENV_LED_COLOR_LABEL] + "is not a legal value"


def _verify_led_color(led, led_prop):
    logging.info("led {}".format(led))
    if led == PlatformConsts.ENV_UID:
        assert led_prop['color'] == PlatformConsts.ENV_LED_COLOR_OFF, \
            PlatformConsts.ENV_LED_COLOR_OFF + " not found for " + led
    else:
        assert led_prop['color'] == PlatformConsts.ENV_LED_COLOR_GREEN, \
            PlatformConsts.ENV_LED_COLOR_GREEN + " not found for " + led


def _verify_psu_prop(psu, psu_prop, devices):
    logging.info("psu {}".format(psu))
    Tools.ValidationTool.verify_field_exist_in_json_output(psu_prop, devices.dut.platform_env_psu_prop).verify_result()


# ------------ Open API tests -----------------

@pytest.mark.openapi
@pytest.mark.platform
def test_show_platform_environment_temperature_openapi(engines, devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_show_platform_environment_temperature(engines, devices)


@pytest.mark.openapi
@pytest.mark.platform
def test_show_platform_environment_psu_openapi(engines, devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_show_platform_environment_psu(engines, devices)


@pytest.mark.openapi
@pytest.mark.platform
def test_set_platform_environment_led_openapi(engines, devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_set_platform_environment_led(engines, devices)


@pytest.mark.openapi
@pytest.mark.platform
def test_show_platform_environment_fan_openapi(engines, devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_show_platform_environment_fan(engines, devices)


@pytest.mark.openapi
@pytest.mark.platform
@pytest.mark.simx
@pytest.mark.nvos_ci
def test_show_platform_environment_openapi(engines, devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_show_platform_environment(engines, devices)


def _get_float(string):
    try:
        return float(string)
    except ValueError:
        return None
