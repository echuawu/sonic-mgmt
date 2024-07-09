import logging
import random
import pytest

from ngts.nvos_tools.Devices.BaseDevice import BaseSwitch
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.nmx.Cluster import Cluster
from ngts.nvos_constants.constants_nvos import PlatformConsts
from ngts.nvos_constants.constants_nvos import OutputFormat
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType

logger = logging.getLogger()
NMX_CONTROLLER = 'nmx-controller'
NMX_TELEMETRY = 'nmx-telemetry'
INITIAL_EXPECTED_APPS = [NMX_CONTROLLER, NMX_TELEMETRY]


@pytest.mark.nmx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_cluster_app_start_stop(engines, devices, test_api):
    TestToolkit.tested_api = test_api
    output_format = OutputFormat.json

    def verify_apps_attributes(output):
        app_names = list(output.keys())

        with allure.step("Verify initial existing apps"):
            assert set(app_names) == set(INITIAL_EXPECTED_APPS), f"Expected apps:{INITIAL_EXPECTED_APPS} Actual apps:{app_names}"

        with allure.step("Verify 'nv show cluster apps installed' output"):
            ValidationTool.validate_output_of_show(output[NMX_TELEMETRY], devices.dut.cluster_app_nmx_telemetry).verify_result()
            ValidationTool.validate_output_of_show(output[NMX_CONTROLLER], devices.dut.cluster_app_nmx_controller).verify_result()

    with allure.step("Create Cluster object"):
        cluster = Cluster()

    with allure.step("Running 'nv show cluster apps' command and parsing output"):
        output = OutputParsingTool.parse_show_output_to_dict(
            cluster.apps.show(output_format=output_format),
            output_format=output_format).get_returned_value()
        verify_apps_attributes(output)

    with allure.step("Running 'nv show cluster apps <app-name>' command and parsing output"):
        for app in INITIAL_EXPECTED_APPS:
            output = OutputParsingTool.parse_show_output_to_dict(
                cluster.apps.apps_name[app].show(output_format=OutputFormat.json),
                output_format=OutputFormat.json).get_returned_value()
            ValidationTool.validate_output_of_show(output, devices.dut.cluster_app[app]).verify_result()

    with allure.step("Running 'nv show cluster apps installed' command and verifying output"):
        output = OutputParsingTool.parse_show_output_to_dict(
            cluster.apps.installed.show(output_format=output_format),
            output_format=output_format).get_returned_value()
        verify_apps_attributes(output)

    with allure.step("Running 'nv show cluster apps running' command and verifying output"):
        pass

    with allure.step("Start/Stop apps"):
        for app in INITIAL_EXPECTED_APPS:
            with allure.step(f"Start app {app} and validate its up"):
                cluster.apps.apps_name[app].action_start_cluster_apps()
                _verify_app_is_up(engines)
                # TBD -- once "running" is working, use it to verify app is running
            with allure.step(f"Stop app {app} and validate its down"):
                cluster.apps.apps_name[app].action_stop_cluster_apps()
                # TBD -- once "running" is working, use it to verify app is not running
                _verify_app_is_down(engines)


def _verify_app_is_up(engines):
    with allure.step("Checking if service is up using docker ps | grep -i nmx"):
        output = engines.dut.run_cmd('docker ps | grep -i nmx')
        assert output != '', f"nmx docker is still down, {output}"
        output = output.split('\n')
        assert len(output) > 1, f"nmx docker is not up, {output}"


def _verify_app_is_down(engines):
    with allure.step("Checking if service is down using docker ps | grep -i nmx"):
        output = engines.dut.run_cmd('docker ps | grep -i nmx')
        assert output == '', f"nmx docker is still up, {output}"
