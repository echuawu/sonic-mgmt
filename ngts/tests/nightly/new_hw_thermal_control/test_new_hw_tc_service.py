import allure
import logging
import pytest
import time
import operator

from ngts.helpers.new_hw_thermal_control_helper import TC_CONST, MockSensors, compare_pwd_with_expected_value, check_hw_thermal_control_status, verify_rpm_is_expected_value, check_periodic_report


logger = logging.getLogger()


class TestNewTc:

    @pytest.fixture(autouse=True)
    def setup_param(self, topology_obj, engines, cli_objects, interfaces, players):
        self.cli_objects = cli_objects
        self.dut_engine = engines.dut

    @allure.title('test operate tc service')
    def test_operate_tc_service(self, get_dut_supported_sensors_and_tc_config):
        """
        This test is to verify tc service's behaviors when doing start, stop, suspend and resume.
        1. Stop hw-management-tc service
           Check service state
           Check PWM is maximum(100), and check FAN speed is set to correct range
        2. Start hw-management-tc service.
           Immediately after start - check PWM value . It should be at maximum
           wait 120 sec for service init
           Check syslog and service state
           Check PWM value is not maximum(100)
           Check FAN speed is set to correct range
        3. Suspend hw-management-tc service
           Check PWM is maximum(100), and check FAN speed is set to correct range
        4. Resume hw-management-tc service
           Check PWM is not maximum(100), and check FAN speed is set to correct range
        """
        _, tc_config_dict = get_dut_supported_sensors_and_tc_config

        with allure.step("check periodic report"):
            check_periodic_report(self.dut_engine)

        with MockSensors(self.dut_engine, self.cli_objects) as mock_sensor:

            def verify_pwd_and_rpm(operation):
                expected_pwm = 100
                with allure.step(f"Verify current pwd {operation.__name__} {expected_pwm},"
                                 f" and rpm is the corresponding value"):
                    compare_pwd_with_expected_value(mock_sensor, expected_pwm, operation)
                    verify_rpm_is_expected_value(mock_sensor, tc_config_dict)

            with allure.step(f'Stop tc service and check PWM'):
                self.cli_objects.dut.hw_mgmt.stop_thermal_control()
                verify_pwd_and_rpm(operator.eq)
            with allure.step(f'Start tc service and check PWM'):
                self.cli_objects.dut.hw_mgmt.start_thermal_control()
                verify_pwd_and_rpm(operator.eq)
                time.sleep(TC_CONST.THERMAL_WAIT_FOR_CONFIG)
                check_hw_thermal_control_status(self.cli_objects)
                verify_pwd_and_rpm(operator.le)
            with allure.step(f'Suspend tc service'):
                self.cli_objects.dut.hw_mgmt.suspend_thermal_control()
                verify_pwd_and_rpm(operator.eq)
            with allure.step(f'resume tc service'):
                self.cli_objects.dut.hw_mgmt.resume_thermal_control()
                time.sleep(TC_CONST.THERMAL_WAIT_FOR_CONFIG)
                verify_pwd_and_rpm(operator.le)
