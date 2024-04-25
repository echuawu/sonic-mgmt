#!/usr/bin/env python
import os
import allure
import logging
import pytest
import json
import re
from jinja2 import Template

logger = logging.getLogger()

GEN_SENSORS_DATA_PATH = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.disable_loganalyzer
def test_gen_yml_file_including_sensors_data(topology_obj):
    """
    This script will generate one yml file which includes sensors test data for platform_tests/test_sensors.py
    When need add sensors data for new platform, we can generate the data by running the test (same to run ngts test)
    and copy the sensors data into the file of ansible/group_vars/sonic/sku-sensors-data.yml
    :param topology_obj: topology object fixture
    :return: raise assertion error in case of script failure
    """
    try:
        dut_engine = topology_obj.players['dut']['engine']
        cli_object = topology_obj.players['dut']['cli']
        with allure.step("Get platform and sensors data"):
            platform = cli_object.chassis.get_platform()
            raw_sensors_data = json.loads(dut_engine.run_cmd('sensors -A -j'))
        with allure.step("Parse sensors data"):
            sensors_dict = parse_sensors_data(raw_sensors_data)
        with allure.step("Gen yml file for sensors data"):
            yml_file_full_path = os.path.join(GEN_SENSORS_DATA_PATH, f"sensors_{platform}.yml")
            gen_sensors_data_yaml_file(yml_file_full_path, platform, sensors_dict)

    except Exception as err:
        raise AssertionError(err)


def parse_sensors_data(sensors_data):
    sensors_dict = {}

    # parse alarms fan
    reg_alarms_fan = r"^fan[\d+]_(alarm|fault)$"
    sensors_alarms_fan_list = collect_alarms_key(sensors_data, reg_alarms_fan)
    sensors_dict["alarms_fan_list"] = sensors_alarms_fan_list

    # parse alarms power
    reg_alarm_power = r"^(curr[\d+]_alarm|curr[\d+]_crit_alarm|curr[\d+]_max_alarm|curr[\d+]_lcrit_alarm|" \
                      r"in[\d+]_crit_alarm|in[\d+]_max_alarm|in[\d+]_alarm|in[\d+]_min_alarm|in[\d+]_lcrit_alarm|" \
                      r"power[\d+]_alarm|power[\d+]_crit_alarm|power[\d+]_max_alarm|power[\d+]_cap_alarm)$"
    sensors_alarms_power_list = collect_alarms_key(sensors_data, reg_alarm_power)
    sensors_dict["alarms_power_list"] = sensors_alarms_power_list

    # parse alarms temp
    reg_alarms_temp = r"^(temp[\d+]_crit_alarm|temp[\d+]_max_alarm|temp[\d+]_fault|temp[\d+]_min_alarm" \
                      r"|temp[\d+]_lcrit_alarm)$"
    sensors_alarms_temp_list = collect_alarms_key(sensors_data, reg_alarms_temp)
    sensors_dict["alarms_temp_list"] = sensors_alarms_temp_list

    # parse compares temp
    sensors_compares_temp_list = collect_compares_temp_sensor_key(sensors_data)
    sensors_dict["compares_temp_list"] = sensors_compares_temp_list
    return sensors_dict


def collect_alarms_key(sensors_data, reg_match_key):
    sensors_data_list = []
    for key1, value1 in sensors_data.items():
        temp_sensors_list = []
        for key2, value2 in value1.items():
            if "Package" in key2:
                key2 = key2.replace("Package", '\\P[a-z]*\\')
            for key3, value3 in value2.items():
                if not isinstance(value3, dict):
                    if re.search(reg_match_key, key3):
                        temp_sensors_list.append("- {}/{}/{}".format(key1, key2, key3))
        if temp_sensors_list:
            sensors_data_list.extend(temp_sensors_list)
            sensors_data_list.append('')
    return sensors_data_list


def collect_compares_temp_sensor_key(sensors_data):
    sensors_data_list = []
    reg_compares_temp_input = r"^temp[\d+]_input$"
    reg_compares_temp_crit = r"^temp[\d+]_crit$"
    reg_compares_temp_max = r"^temp[\d+]_max$"
    for key1, value1 in sensors_data.items():
        for key2, value2 in value1.items():
            key_temp_input = None
            key_temp_crit = None
            key_temp_max = None
            if "Package" in key2:
                key2 = key2.replace("Package", '\\P[a-z]*\\')
            for key3, value3 in value2.items():
                if not isinstance(value3, dict):
                    if re.search(reg_compares_temp_input, key3):
                        key_temp_input = "- - {}/{}/{}".format(key1, key2, key3)
                    elif re.search(reg_compares_temp_crit, key3):
                        key_temp_crit = "  - {}/{}/{}".format(key1, key2, key3)
                    elif re.search(reg_compares_temp_max, key3):
                        key_temp_max = "  - {}/{}/{}".format(key1, key2, key3)

            if not key_temp_input:
                continue
            elif key_temp_crit:
                sensors_data_list.append(key_temp_input)
                sensors_data_list.append(key_temp_crit)
                sensors_data_list.append('')
            elif key_temp_max:
                sensors_data_list.append(key_temp_input)
                sensors_data_list.append(key_temp_max)
                sensors_data_list.append('')
    return sensors_data_list


def gen_sensors_data_yaml_file(yaml_filename, platform, sensors_dict):
    with open(os.path.join(GEN_SENSORS_DATA_PATH, 'sensors_data_template.j2')) as template_file:
        t = Template(template_file.read())

    content = t.render(platform=platform, sensors_dict=sensors_dict)

    logger.info(f"Sensors data {content}")
    with open(yaml_filename, "w", encoding='utf-8') as f:
        f.write(content)
