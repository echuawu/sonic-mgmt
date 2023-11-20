import logging
import pytest
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
import time

logger = logging.getLogger()

TIMEOUT = 300
CPU_TEM_LABEL = "CPU Core"


@pytest.mark.checklist
def test_stress_check_nvue(engines):
    with allure.step("Check CPU temperature before the test"):
        platform = Platform()
        pre_temp_values = check_cpu_temp(platform)

    with allure.step("Start techsupport process"):
        logging.info("Start techsupport process")
        system = System()
        start_time = time.time()
        while time.time() - start_time <= TIMEOUT:
            system.techsupport.action_generate()

    with allure.step("Check CPU temperature after the test"):
        post_temp_values = check_cpu_temp(platform)

    with allure.step("Compare temperature values"):
        logging.info("Compare temperature values")
        errors = ""
        for temp, value in pre_temp_values.items():
            if float(value) >= float(post_temp_values[temp]):
                errors += f"{temp} value was not increased during the test\n"

    with allure.step("Wait 5 min till the system cool down"):
        logging.info("Wait 5 min till the system cool down")
        time.sleep(300)

    with allure.step("Check temperature values after 5 min"):
        logging.info("Check temperature values after 5 min")
        cool_down_temp_values = check_cpu_temp(platform)
        for temp, value in cool_down_temp_values.items():
            if float(value) >= float(post_temp_values[temp]):
                errors += f"{temp} is still high\n"

    assert errors, errors


def check_cpu_temp(platform):
    temp_list = {}
    with allure.step("Check CPU temperature"):
        logging.info("CPU temperature")
        temperatures = OutputParsingTool.parse_json_str_to_dictionary(platform.environment.temperature.show()).get_returned_value()
        for temp, values in temperatures.items():
            if temp.startswith(CPU_TEM_LABEL):
                temp_list[temp] = values["current"]
    return temp_list
