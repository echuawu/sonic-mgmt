import logging
import time
import pytest
import random

from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import PlatformConsts, HealthConsts, ActionConsts
from ngts.nvos_constants.constants_nvos import OutputFormat
from ngts.nvos_constants.constants_nvos import FansConsts
from ngts.nvos_constants.constants_nvos import ApiType

logger = logging.getLogger()


@pytest.mark.platform
@pytest.mark.cumulus
@pytest.mark.simx
@pytest.mark.nvos_ci
@pytest.mark.skynet
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_show_platform_environment(engines, devices, test_api, output_format):
    """
    Show platform environment test
    """
    TestToolkit.tested_api = test_api

    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Get output"):
        raw_output = platform.environment.show(output_format=output_format)

    with allure.step("Validate field names (titles)"):
        output_field_names = OutputParsingTool.parse_show_output_to_field_names(raw_output, output_format
                                                                                ).get_returned_value()
        ValidationTool.validate_set_equal(output_field_names, ['type', 'state']).verify_result()

    with allure.step("Validate all environment items are present"):
        output = OutputParsingTool.parse_show_output_to_dict(raw_output, output_format).get_returned_value()
        ValidationTool.validate_set_equal(output.keys(),
                                          devices.dut.psu_fan_list + devices.dut.fan_list + devices.dut.psu_list +
                                          devices.dut.temperature_sensors + devices.dut.led_list +
                                          devices.dut.voltage_sensors).verify_result()


@pytest.mark.platform
@pytest.mark.cumulus
@pytest.mark.simx
@pytest.mark.skynet
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_show_platform_environment_fan(engines, devices, test_api, output_format):
    """
    Show platform environment fan test
    """
    TestToolkit.tested_api = test_api

    with allure.step("Create Platform object"):
        platform = Platform()

    with allure.step("Execute 'show platform environment fan' and validate field names and fan list"):
        raw_output = platform.environment.fan.show(output_format=output_format)
        field_names = OutputParsingTool.parse_show_output_to_field_names(
            raw_output, output_format=output_format, field_name_dict=devices.dut.fan_prop_auto).get_returned_value()
        ValidationTool.validate_set_equal(field_names, devices.dut.platform_environment_fan_values.keys()
                                          ).verify_result()
        output = OutputParsingTool.parse_show_output_to_dict(
            raw_output, output_format=output_format, field_name_dict=devices.dut.fan_prop_auto).get_returned_value()
        actual_fan_list = output.keys()
        ValidationTool.validate_set_equal(actual_fan_list, devices.dut.fan_list + devices.dut.psu_fan_list
                                          ).verify_result()

    with allure.step("Assert all fans have the same direction"):
        directions = {fan["direction"] for fan in output.values() if fan["direction"] != "None"}
        assert len(directions) == 1, f"Not all fans show the same direction: {output}"

    with allure.step("Checking properties of random fan"):
        random_fan = random.choice(devices.dut.fan_list)
        _test_specific_fan(random_fan, output_format, devices.dut.platform_environment_fan_values, output, platform)

    with allure.step("Checking properties of PSU fans"):
        for fan in devices.dut.psu_fan_list:
            if output.get(fan).get("state") == "absent":
                _test_absent_fan(fan, output_format, devices.dut.platform_environment_absent_fan_values, output, platform)
                continue
        _test_specific_fan(fan, output_format, devices.dut.platform_environment_fan_values, output, platform)


def _test_absent_fan(fan, output_format, expected, output, platform):
    logger.info(f"Testing properties of absent fan {fan}")
    with allure.step("Checking output of 'show platform environment fan'"):
        ValidationTool.validate_output_of_show(output[fan], expected).verify_result()
    with allure.step("Checking output of 'show platform environment fan <fan-id>'"):
        fan_output = OutputParsingTool.parse_show_output_to_dict(
            platform.environment.fan.show(fan, output_format=output_format),
            output_format=output_format).get_returned_value()
        ValidationTool.validate_output_of_show(fan_output, expected).verify_result()


def _test_specific_fan(fan, output_format, expected, output, platform):
    logger.info(f"Testing properties of {fan}")
    with allure.step("Checking output of 'show platform environment fan'"):
        ValidationTool.validate_output_of_show(output[fan], expected).verify_result()
    with allure.step("Checking output of 'show platform environment fan <fan-id>'"):
        fan_output = OutputParsingTool.parse_show_output_to_dict(
            platform.environment.fan.show(fan, output_format=output_format),
            output_format=output_format).get_returned_value()
        ValidationTool.validate_output_of_show(fan_output, expected).verify_result()
        assert int(fan_output["min-speed"]) < int(fan_output["current-speed"]) < int(fan_output["max-speed"])


@pytest.mark.platform
@pytest.mark.cumulus
@pytest.mark.simx
@pytest.mark.skynet
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_show_platform_environment_led(engines, devices, test_api):
    """
    Show platform environment led test
    """
    TestToolkit.tested_api = test_api

    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Execute show platform environment led and make sure all the components exist"):
        output = _verify_output(platform, "led", devices.dut.led_list)

    with allure.step("Check that all required properties for each led"):
        logging.info("Check that all required properties for each led")
        for led, led_prop in output.items():
            _verify_led_prop(led, led_prop)

    with allure.step("Check output of a specific Led"):
        led_to_check = list(output.keys())[0]
        output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
            platform.environment.led.show(op_param=led_to_check)).verify_result()
        _verify_led_prop(led_to_check, output)


@pytest.mark.platform
@pytest.mark.simx
@pytest.mark.skynet
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_set_platform_environment_led(engines, devices, test_api):
    """
    Set platform environment led test

    Test flow:
    1. Check all leds are green by default exclude UID
    2. Negative testing, try to turn off leds, which we can't, check value didn't change
    3. Turn-on UID led and check led is green
    4. Unset it and check it returned to default values
    """
    TestToolkit.tested_api = test_api

    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Execute show platform environment led and make sure all the components exist"):
        output = _verify_output(platform, "led", devices.dut.led_list)

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
            platform.environment.led.action(action='turn-{type}'.format(type=PlatformConsts.ENV_LED_TURN_OFF),
                                            suffix=led).verify_result(should_succeed)

    with allure.step("Check that all leds are green and UID off by default"):
        logging.info("Check that all leds are green and UID off by default")
        for led, led_prop in output.items():
            _verify_led_color(led, led_prop)

    with allure.step("Change UID state led to on"):
        logging.info("Check UID state led to on")
        platform.environment.led.action(action='turn-{type}'.format(type=PlatformConsts.ENV_LED_TURN_ON),
                                        suffix=PlatformConsts.ENV_UID)
        output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
            platform.environment.led.show()).verify_result()
        Tools.ValidationTool.compare_values(output['UID']['color'], PlatformConsts.ENV_LED_COLOR_BLUE, True) \
            .verify_result()

    with allure.step("Change UID state led to off"):
        logging.info("Change UID state led to off")
        platform.environment.led.action(action='turn-{type}'.format(type=PlatformConsts.ENV_LED_TURN_OFF),
                                        suffix=PlatformConsts.ENV_UID)
        output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
            platform.environment.led.show()).verify_result()
        Tools.ValidationTool.compare_values(output['UID']['color'], PlatformConsts.ENV_LED_TURN_OFF, True) \
            .verify_result()

    with allure.step("Check that all leds are green and UID off after unset"):
        logging.info("Check that all leds are green and UID off after unset")
        for led, led_prop in output.items():
            _verify_led_color(led, led_prop)


@pytest.mark.platform
@pytest.mark.cumulus
@pytest.mark.simx
@pytest.mark.skynet
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_show_platform_environment_psu(engines, devices, test_api):
    """
    Show platform environment psu test
    """
    TestToolkit.tested_api = test_api

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
            platform.environment.psu.show(op_param=psu_to_check)).verify_result()
        _verify_psu_prop(psu_to_check, output, devices)


@pytest.mark.platform
@pytest.mark.cumulus
@pytest.mark.simx
@pytest.mark.skynet
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_show_platform_environment_temperature(engines, devices, test_api):
    """
    Show platform environment temperature test

    Test flow:
    1. Select a FAN to test
    2. Validate every temperature sensor component in nv show platform environment temperature command
    3. Validate every temperature sensor component properties
    4. Validate every temperature sensor temp in the valid range
    5. Validate CPU sensors temp in specified range from mean by some tolerance
    6. Validate ASIC sensors temp in specified range from mean by some tolerance
    7. Validate PSU sensors temp in specified range from mean by some tolerance

    """
    TestToolkit.tested_api = test_api

    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Execute show platform environment temperature and make sure all the components exist"):
        output = _verify_output(platform, "temperature", devices.dut.temperature_sensors)

    with allure.step("make sure all temperature sensors are present in the output"):
        with allure.step(
                "Verify for every sensor in sensors_dict[TEMPERATURE], it exist in nv show platform temperature"):
            diff_sensors = [x for x in devices.dut.sensors_dict["TEMPERATURE"] if x not in output.keys()]
            err_mes = '' if not len(diff_sensors) else 'the next sensors are not in the output: {}'.format(diff_sensors)
        with allure.step("Verify no extra sensors are found in nv show platform environment temperature"):
            diff_sensors = [x for x in output.keys() if x not in devices.dut.sensors_dict["TEMPERATURE"]]
            err_mes += '' if not len(diff_sensors) else 'there are extra sensors in the output: {}'.format(diff_sensors)

    assert not err_mes, err_mes

    with allure.step("Check that all required properties for each temperature"):
        logging.info("Check that all required properties for each temperature")
        for temp, temp_prop in output.items():
            if temp_prop.get("state") == 'absent':
                continue
            _verify_temp_prop(temp, temp_prop)

    with allure.step("Check that all sensors in required range"):
        logging.info("Check that all sensors in required range")
        for temp, temp_prop in output.items():
            _verify_temp_in_range(temp, temp_prop, PlatformConsts.ENV_TEMP_MIN,
                                  PlatformConsts.ENV_TEMP_MAX)

    verify_sensor_group_by_tolerance(output, PlatformConsts.ENV_CPU)
    verify_sensor_group_by_tolerance(output, PlatformConsts.FW_ASIC)
    verify_sensor_group_by_tolerance(output, PlatformConsts.ENV_PSU.upper())


@pytest.mark.platform
@pytest.mark.simx
def test_platform_environment_events_performance(engines, devices):
    """
     Simulate an event and verify that show event is not flooded with multiple entries

     Test flow:
     1. Validate System Health is OK
     2. Clear System events
     3. Assign default FAN direction for this system
     4. Assign wrong FAN direction for this system
     5. Change FAN direction to wrong direction and verify via CLI
     6. Wait for 2:10 minutes and verify that show event is not flooded with multiple entries for the same fan
     7. Change FAN direction to system default
     """
    TestToolkit.tested_api = ApiType.NVUE
    platform = Platform()
    system = System()
    fan_dir_mismatch_msg = "direction exhaust is not aligned"
    fan_to_check = devices.dut.fan_list[2]

    with allure.step('Validate System health status should be {}'.format(HealthConsts.OK)):
        output = Tools.OutputParsingTool.parse_json_str_to_dictionary(system.health.show()).verify_result()
        assert output['status'] == HealthConsts.OK, 'System health status is {} instead of {}'.format(
            output['status'], HealthConsts.OK)

    with allure.step('Clear system events'):
        system.events.action(ActionConsts.CLEAR)

    with allure.step("Assign default FAN direction as per this System"):
        output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
            platform.environment.fan.show(op_param=fan_to_check)).verify_result()
        def_dir = output['direction']

    with allure.step("Assign wrong direction (opposite to default) as per this System"):
        if def_dir == FansConsts.FORWARD_DIRECTION:
            wrong_dir = FansConsts.BACKWARD_DIRECTION
        else:
            wrong_dir = FansConsts.FORWARD_DIRECTION

    try:
        with allure.step("Change direction of {} to wrong dir({}) and verify".format(fan_to_check, wrong_dir)):
            _set_platform_environment_fan_direction(engines, devices, platform, fan_to_check, def_dir, wrong_dir)

        with allure.step("Wait for the system to be able to generate more events"):
            time.sleep(130)

        with allure.step('Run show system events command & validate there is 1 FAN direction issue per FAN'):
            output = OutputParsingTool.parse_json_str_to_dictionary(system.events.show()).get_returned_value()
            fan_error_set = set()
            for events_no in output['last']:
                if fan_dir_mismatch_msg in str(output["last"][events_no]):
                    fan = output["last"][events_no]["type-id"]
                    assert (fan not in fan_error_set), 'Fan mismatch event occurred more times for FAN:{}'.format(fan)
                    fan_error_set.add(fan)
                    logger.info("Fan direction mismatch Event captured for : {}".format(fan))

        with allure.step("Validate Fan direction error appears in system log but is not flooded"):
            log_cmd = "nv show sys log | grep 'direction exhaust is not aligned' | wc -l"
            no_of_errors_1 = int(engines.dut.run_cmd(log_cmd))
            assert no_of_errors_1 > 0, 'Fan direction error does not appear in log'
            time.sleep(130)
            no_of_errors_2 = int(engines.dut.run_cmd(log_cmd))
            assert no_of_errors_1 == no_of_errors_2, 'Fan direction errors are being repeated in logs'

    finally:
        with allure.step("Change Fan direction of {} to default({}) and verify".format(fan_to_check, def_dir)):
            _set_platform_environment_fan_direction(engines, devices, platform, fan_to_check, def_dir, def_dir)


@pytest.mark.platform
@pytest.mark.simx
def test_platform_environment_fan_direction_mismatch(engines, devices):
    """
    Set FAN direction test

    Test flow:
    1. Select a FAN to test
    2. Validate System health should be OK
    3. Validate there should not be any FAN direction related issues
    4. Assign default FAN direction for this system
    5. Assign wrong FAN direction for this system
    6. Change FAN direction to wrong direction and verify via CLI
    7. Validate System health should be NOT OK
    8. Validate FAN related health issues in System health
    9. Change FAN direction to system default abd verify via CLI
    10. Validate System health should be OK
    11. Validate there should not be any FAN direction related issues
    """
    TestToolkit.tested_api = ApiType.NVUE
    with allure.step('Validate Fan direction mismatch feature enabled'):
        _verify_fan_direction_mismatch_behaviour(engines, devices, True)


def _verify_fan_direction_mismatch_behaviour(engines, devices, feature_enable):
    platform = Platform()
    system = System()
    if feature_enable:
        state = FansConsts.STATE_NOT_OK
        should_str = 'be'
    else:
        state = FansConsts.STATE_OK
        should_str = 'not be'

    try:
        with allure.step('Select FAN to test'):
            # Don't choose FAN1/1 or FAN1/2 because NVOS considers fan1_direction as the "ground truth" that other fans
            # are compared against. This will be changed in the future.
            choose_from = devices.dut.fan_list[2:]
            fan_to_check = random.choice(choose_from)

        with allure.step('Validate System health status should be {}'.format(HealthConsts.OK)):
            output = Tools.OutputParsingTool.parse_json_str_to_dictionary(system.health.show()).verify_result()
            health_status = output['status']
            assert health_status == HealthConsts.OK, 'System health status is {} instead of {}'.format(
                health_status, HealthConsts.OK)

        with allure.step("Validate there should not be any Fan direction Health Issues"):
            output_dict = Tools.OutputParsingTool.parse_json_str_to_dictionary(system.health.show()).verify_result()
            health_issues = output_dict['issues']
            assert not health_issues, f'Unexpected Health Issues:\n{health_issues}'

        with allure.step("Assign default FAN direction as per this System"):
            output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
                platform.environment.fan.show(op_param=fan_to_check)).verify_result()
            def_dir = output['direction']

        with allure.step("Assign wrong direction (opposite to default) as per this System"):
            if def_dir == FansConsts.FORWARD_DIRECTION:
                wrong_dir = FansConsts.BACKWARD_DIRECTION
            else:
                wrong_dir = FansConsts.FORWARD_DIRECTION

        with allure.step("Change direction of {} to wrong dir({}) and verify".format(fan_to_check, wrong_dir)):
            _set_platform_environment_fan_direction(engines, devices, platform, fan_to_check, def_dir, wrong_dir)

        with allure.step('Validate System health status should be {}'.format(state)):
            output = system.health.show(output_format=OutputFormat.json)
            output_dict = Tools.OutputParsingTool.parse_json_str_to_dictionary(output).verify_result()
            health_status = output_dict['status']
            assert health_status == state, 'System health status is {} instead of {}'.format(health_status, state)

        with allure.step("Validate Issues should {} seen in System Health Report".format(should_str)):
            health_issues = output_dict['issues']
            if feature_enable:
                assert fan_to_check in health_issues.keys(), \
                    f'Expected to find issue with {fan_to_check} but issues are:\n{health_issues}'
            else:
                assert not health_issues, f'Unexpected Health Issues:\n{health_issues}'

    finally:
        with allure.step("Change Fan direction of {} to default({}) and verify".format(fan_to_check, def_dir)):
            _set_platform_environment_fan_direction(engines, devices, platform, fan_to_check, def_dir, def_dir)

        with allure.step('Check System health status'):
            output = Tools.OutputParsingTool.parse_json_str_to_dictionary(system.health.show()).verify_result()
            health_status = output['status']
            assert health_status == HealthConsts.OK, 'System health status is {} instead of {}'. \
                format(health_status, HealthConsts.OK)

        with allure.step("Validate there should not be any Fan direction Health Issues"):
            output = Tools.OutputParsingTool.parse_json_str_to_dictionary(system.health.show()).verify_result()
            health_issues = output['issues']
            assert not health_issues, f'Unexpected Health Issues:\n{health_issues}'


def _set_platform_environment_fan_direction(engines, devices, platform, fan_to_check, def_dir, direction):
    if "PSU" in fan_to_check:
        fan_name = fan_to_check.replace("/", "_").lower()
    else:
        fan_name = fan_to_check.split('/')[0].lower()

    with allure.step("Set the direction of the fan {} to {} direction".format(fan_name, direction)):
        simulate_fan_direction(engines, devices, fan_name, direction)

    with allure.step("Check output of a Fan {}".format(fan_name)):
        output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
            platform.environment.fan.show(op_param=fan_to_check)).verify_result()
        ValidationTool.validate_set_equal(output.keys(), devices.dut.platform_environment_fan_values.keys())

    with allure.step("Check fan state and direction via CLI"):
        actual_direction = output['direction']
        state = output['state']
        assert actual_direction == direction, "Unexpected direction of fan: {} instead of {}". \
            format(actual_direction, direction)


def simulate_fan_direction(engines, devices, fan_name, direction):
    """
    @summary: Simulate the direction of the module's fan.
    @param engines : Engine object
    @param devices : devices object
    @param fan_name: the module with the fan to simulate its direction.
    @param direction: the simulated direction, can be FORWARD/BACKWARD_DIRECTION.
    """
    direction_integer = 1 if direction == FansConsts.FORWARD_DIRECTION else 0
    chmod_cmd = "sudo chmod 777 {}/{}_dir".format(devices.dut.fan_direction_dir, fan_name)
    ret_val = engines.dut.run_cmd(chmod_cmd)
    assert len(ret_val) == 0, "Chmod command for fan file failed"

    simulate_cmd = "sudo echo {} > {}/{}_dir".format(direction_integer, devices.dut.fan_direction_dir, fan_name)
    logger.info('simulate {} fan direction to be {}. from linux shell, run: {}'.
                format(fan_name, direction, simulate_cmd))
    ret_val = engines.dut.run_cmd(simulate_cmd)
    assert len(ret_val) == 0, "Write command for fan file failed"
    time.sleep(5)  # for the change to take affect.

    chmod_cmd = "sudo chmod 644  {}/{}_dir".format(devices.dut.fan_direction_dir, fan_name)
    ret_val = engines.dut.run_cmd(chmod_cmd)
    assert len(ret_val) == 0, "Chmod command for fan file failed"


def _verify_temp_prop(temp, temp_prop):
    logging.info("temp {}".format(temp))
    list_of_keys = temp_prop.keys()
    assert "state" in list_of_keys and "current" in list_of_keys, "state/current can't be found"

    if "max" in list_of_keys:
        max_temp = temp_prop["max"]
        assert _get_float(max_temp) or "N/A" in max_temp, "the max temperature value is invalid"

    if "crit" in list_of_keys:
        crit_value = temp_prop["crit"]
        assert _get_float(crit_value) or "N/A" in crit_value, "the critical temperature value is invalid"


def _verify_temp_in_range(temp, temp_prop, min_temp, max_temp):
    curr_temp = temp_prop[PlatformConsts.ENV_TEMP_CURR_PROP]
    assert temp_prop['state'] == PlatformConsts.ENV_TEMP_STATE_OK, 'sensor state is {} instead of {}'.format(
        temp_prop['state'], PlatformConsts.ENV_TEMP_STATE_OK)
    assert min_temp <= _get_float(curr_temp) <= max_temp, f"{temp} temperature {curr_temp} is not within" \
        f" the valid range ({min_temp} - {max_temp})."


def verify_sensor_group_by_tolerance(output, category):
    with allure.step("Check that {} temps are within the specified range from mean by tolerance of {}%"
                     .format(category, PlatformConsts.ENV_TEMP_TOLERANCE)):
        logging.info("Check that {} temps are within the specified range from mean by tolerance of {}%"
                     .format(category, PlatformConsts.ENV_TEMP_TOLERANCE))
    sensors = {temp: float(temp_prop[PlatformConsts.ENV_TEMP_CURR_PROP]) for temp, temp_prop in output.items()
               if category in temp}
    sensor_mean_temp = sum(sensors.values()) / len(sensors)

    for sensor, sensor_temp in sensors.items():
        _verify_temp_by_tolerance(sensor, sensor_temp, sensor_mean_temp, PlatformConsts.ENV_TEMP_TOLERANCE,
                                  category)


def _verify_temp_by_tolerance(temp, curr_temp, mean_temp, p, category):
    min_temp = mean_temp * (1 - p / 100)
    max_temp = mean_temp * (1 + p / 100)
    assert min_temp <= curr_temp <= max_temp, \
        f"{category}: {temp} temperature {curr_temp} is not within the tolerated range from mean ({min_temp} - {max_temp})."


def _verify_output(platform, comp_name, req_fields):
    logging.info("Required comp: " + str(req_fields))
    with allure.step("Verify text output"):
        logging.info("Verify text output")
        output = platform.environment.show(comp_name, output_format=OutputFormat.auto)
        missing_components = [comp for comp in req_fields if comp not in output]
        assert not missing_components, f"The following fields were not found in the output: {missing_components}"

    with allure.step("Verify json output"):
        logging.info("Verify json output")
        output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
            platform.environment.show(comp_name)).verify_result()
        Tools.ValidationTool.verify_field_exist_in_json_output(output, req_fields).verify_result()

    return output


def _verify_led_prop(led, led_prop):
    logging.info("led {}".format(led))
    assert PlatformConsts.ENV_LED_COLOR_LABEL in led_prop.keys(), \
        PlatformConsts.ENV_LED_COLOR_LABEL + " not found for " + led
    assert led_prop[PlatformConsts.ENV_LED_COLOR_LABEL].lower() in PlatformConsts.ENV_LED_COLOR_OPTIONS, \
        led_prop[PlatformConsts.ENV_LED_COLOR_LABEL] + " is not a legal value"


def _verify_led_color(led, led_prop):
    logging.info("led {}".format(led))
    if led == PlatformConsts.ENV_UID:
        assert led_prop['color'] == PlatformConsts.ENV_LED_TURN_OFF, \
            PlatformConsts.ENV_LED_TURN_OFF + " not found for " + led
    else:
        assert led_prop['color'] == PlatformConsts.ENV_LED_COLOR_GREEN, \
            PlatformConsts.ENV_LED_COLOR_GREEN + " not found for " + led


def _verify_psu_prop(psu, psu_prop, devices):
    logging.info("psu {}".format(psu))
    Tools.ValidationTool.verify_field_exist_in_json_output(psu_prop, devices.dut.platform_env_psu_prop).verify_result()


def _get_float(string):
    try:
        return float(string)
    except ValueError:
        return None
