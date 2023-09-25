import pytest
from datetime import datetime
from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure


pytestmark = [
    pytest.mark.topology('dpu')
]

BF_2_PLATFORM = 'arm64-nvda_bf-mbf2h536c'
BF_3_PLATFORM = 'arm64-nvda_bf-9009d3b600cvaa'


def test_dpu_show_platform_temperature(duthosts, rand_one_dut_hostname):
    """
    Validate output of command "show platform temperature" on DPU devices
    """
    duthost = duthosts[rand_one_dut_hostname]
    cmd = "show platform temperature"
    platform_temp_parsed = duthost.show_and_parse(cmd)

    platform = duthost.facts['platform']
    expected_sensors = {BF_2_PLATFORM: ['ASIC', 'DDR0_0', 'DDR0_1', 'DDR1_0', 'DDR1_1', 'SFP0', 'SFP1'],
                        BF_3_PLATFORM: ['CPU', 'DDR', 'SFP0', 'SFP1']
                        }

    with allure.step('Validate that all expected sensors available'):
        available_sensors = [sensor_data['sensor'] for sensor_data in platform_temp_parsed]

        for sensor in expected_sensors[platform]:
            assert sensor in available_sensors, \
                'Sensor "{}" not available in output of cmd: "{}"'.format(sensor, cmd)

    bf2_na_sensors = ['DDR0_0', 'DDR0_1', 'DDR1_0', 'DDR1_1', 'SFP0', 'SFP1']
    na_value = 'N/A'
    # Values below from SONiC on DPU PMON HLD document
    expected_crit_low_temp = 5.0
    expected_low_temp = 5.0
    expected_high_temp = 95.0
    expected_crit_high_temp = 100.0

    for sensor_data in platform_temp_parsed:
        sensor = sensor_data['sensor']
        with allure.step('Validate values for sensor "{}"'.format(sensor)):
            if platform == BF_2_PLATFORM and sensor in bf2_na_sensors:
                assert sensor_data['temperature'] == na_value, 'Sensor "{}" has invalid temperature'.format(sensor)
                assert sensor_data['crit low th'] == na_value, 'Sensor "{}" has invalid "crit low th" ' \
                                                               'temperature'.format(sensor)
                assert sensor_data['low th'] == na_value, 'Sensor "{}" has invalid "low th" temperature'.format(sensor)
                assert sensor_data['high th'] == na_value, 'Sensor "{}" has invalid "high th" ' \
                                                           'temperature'.format(sensor)
                assert sensor_data['crit high th'] == na_value, 'Sensor "{}" has invalid "crit high th" ' \
                                                                'temperature'.format(sensor)
            else:
                temperature = float(sensor_data['temperature'])
                crit_low_temp = float(sensor_data['crit low th'])
                low_temp = float(sensor_data['low th'])
                high_temp = float(sensor_data['high th'])
                crit_high_temp = float(sensor_data['crit high th'])

                assert crit_low_temp == expected_crit_low_temp, \
                    'Crit low temp is "{}" not as expected: "{}"'.format(crit_low_temp, expected_crit_low_temp)
                assert low_temp == expected_low_temp, \
                    'Low temp is "{}" not as expected: "{}"'.format(low_temp, expected_low_temp)
                assert high_temp == expected_high_temp, \
                    'High temp is "{}" not as expected: "{}"'.format(high_temp, expected_high_temp)
                assert crit_high_temp == expected_crit_high_temp, \
                    'Crit high temp is "{}" not as expected: "{}"'.format(crit_high_temp, expected_crit_high_temp)
                assert crit_low_temp < temperature < crit_high_temp, \
                    'Temperature: "{}" for sensor: "{}" is not valid, check output: "{}"'.format(temperature, sensor,
                                                                                                 cmd)

            assert sensor_data['warning'] == 'False', \
                'Sensor: "{}" has warning "True", check output of cmd: "{}"'.format(sensor, cmd)

            try:
                datetime.strptime(sensor_data['timestamp'], '%Y%m%d %H:%M:%S')
            except ValueError:
                raise AssertionError('Unable to parse timestamp: "{}" from command "{}" output'.format(
                    sensor_data['timestamp'], cmd))
