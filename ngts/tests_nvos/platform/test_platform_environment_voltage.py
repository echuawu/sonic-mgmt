import logging
import re
import pytest
import random
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_constants.constants_nvos import DatabaseConst, PlatformConsts

logger = logging.getLogger()


@pytest.mark.platform
@pytest.mark.simx
@pytest.mark.skynet
@pytest.mark.nvos_chipsim_ci
def test_show_platform_environment_voltage(engines):
    """
    Show platform environment test
    """
    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Execute show platform environment and make sure all the components exist"):
        voltage_output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
            platform.environment.voltage.show()).verify_result()
        sensors = Tools.FilesTool.get_subfiles_list(engine=engines.dut, folder_path=PlatformConsts.VOLTAGE_FILES_PATH,
                                                    subfiles_pattern=PlatformConsts.VOLTAGE_FILES_PATTERN)
        assert len(sensors) == len(voltage_output.keys()), "test failed - expected sensors count = {expected}, show command output = {output} \n expected sensors list: {expected_list}".format(
            expected=len(sensors), output=len(voltage_output.keys()), expected_list=sensors)

    with allure.step("pick random sensor to check the out put of the two show commands"):
        random_sensor = random.choice(list(voltage_output.keys()))

        with allure.step("Execute show platform environment voltage for random sensor {}".format(random_sensor)):
            sensor_output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
                platform.environment.voltage.show(random_sensor)).verify_result()
            with allure.step("Verify both dictionaries are equal"):
                voltage_output_for_sensor = voltage_output[random_sensor].copy()
                # the actual voltage might fluctuate between the two `nv show` commands, so we don't compare it
                del sensor_output['actual']
                del voltage_output_for_sensor['actual']
                assert sensor_output == voltage_output_for_sensor, ""

        random_sensor = get_random_sensor_max_min(voltage_output)
        check_voltage_in_range(voltage_output[random_sensor])


@pytest.mark.cumulus
@pytest.mark.platform
@pytest.mark.skynet
@pytest.mark.simx
def test_show_voltage_bad_flow(engines, devices):
    """
    For Each Sensor we have DB (should be part of init flow)
    """
    with allure.step("Create System object"):
        platform = Platform()
        expected_msg = 'The requested item does not exist'
    with allure.step("Try nv show platform environment voltage <not_exist_sensor>"):
        output = platform.environment.voltage.show('not_sensor', should_succeed=False)
        assert expected_msg in output, "check the show command for not exist sensor, the expected message is {}, " \
                                       "the current output is {}".format(expected_msg, output)


@pytest.mark.platform
@pytest.mark.simx
@pytest.mark.skynet
def test_database_platform_environment_voltage(engines, devices):
    """
    For Each Sensor we have DB (should be part of init flow)
    """
    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("get expected sensors"):
        sensors_list = platform.environment.voltage.get_sensors_list(engines.dut)
        logger.info("the expected sensors from switch's file system are: {}".format(sensors_list))

    with allure.step("get expected CLI voltage sensors"):
        cli_sensors_list = platform.environment.voltage.get_cli_sensors_list(engines.dut)

        logger.info("the sensors from switch's CLI are: {}".format(cli_sensors_list))

    with allure.step("get all the tabled with SENSOR in STATE_DB"):
        raw_database_output = Tools.DatabaseTool.sonic_db_cli_get_keys(engine=engines.dut, asic="",
                                                                       db_name=DatabaseConst.STATE_DB_NAME,
                                                                       grep_str="VOLTAGE").splitlines()
        database_output = [re.sub(r"PMIC-\d+ ", "", sensor_str) for sensor_str in raw_database_output]

    with allure.step("Check the Sensors output from CLI"):
        with allure.step("Verify for every sensor in sensors_dict[VOLTAGE], it exist in nv show platform environment voltage"):
            diff_sensors = [x for x in devices.dut.sensors_dict["VOLTAGE"] if x not in cli_sensors_list]
            err_mes = '' if not len(diff_sensors) else 'the next sensors are missed {}'.format(diff_sensors)
        with allure.step("Verify no extra sensors are found in nv show platform environment voltage"):
            diff_sensors = [x for x in cli_sensors_list if x not in devices.dut.sensors_dict["VOLTAGE"]]
            err_mes += '' if not len(diff_sensors) else 'there extra sensors were found: {}'.format(diff_sensors)

    with allure.step("Check the Sensors dynamic tables"):
        with allure.step("Verify for every sensor: VOLTAGE_INFO|<sensor_name> table exist in STATE_DB"):
            diff_sensors = [x for x in sensors_list if x not in database_output]
            err_mes += '' if not len(diff_sensors) else 'the next tables are missed {}'.format(diff_sensors)

        with allure.step("Verify no extra sensor tables in STATE_DB"):
            diff_sensors = [x for x in database_output if x not in sensors_list]
            err_mes += '' if not len(diff_sensors) else 'the next sensors are missed {}'.format(diff_sensors)

        assert not err_mes, err_mes


def get_random_sensor_max_min(sensors_dic):
    """
        get random sensor out of all the sensors with: ok state and have max, min values
    :param sensors_dic:
    :return:
    """
    sensors_list = []
    for item in sensors_dic.keys():
        if 'min' in sensors_dic[item].keys() and 'max' in sensors_dic[item].keys():
            sensors_list.append(item)
    assert sensors_list, "No sensors with Max and Min values"
    return random.choice(sensors_list)


def check_voltage_in_range(sensor_output):
    """

    :param sensor_output:
    :return:
    """
    with allure.step("Verify the actual voltage is between min and max"):
        assert sensor_output['state'] == 'ok', ""
        assert float(sensor_output['actual']) < float(sensor_output['max']), "the actual voltage out of range, max voltage = {}".format(sensor_output['max'])
        assert float(sensor_output['actual']) > float(sensor_output['min']), "the actual voltage out of range, min voltage = {}".format(sensor_output['min'])
