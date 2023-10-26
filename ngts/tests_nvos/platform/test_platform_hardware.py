import logging
import pytest
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_constants.constants_nvos import PlatformConsts
from ngts.nvos_constants.constants_nvos import OutputFormat
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.Devices.BaseDevice import MarlinSwitch

logger = logging.getLogger()


@pytest.mark.platform
@pytest.mark.cumulus
@pytest.mark.nvos_ci
def test_show_platform_hardware(devices):
    """
    Show platform hardware test
    """
    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Check show hardware output"):
        expected_fields = devices.dut.platform_hw_list
        if isinstance(devices.dut, MarlinSwitch):
            expected_fields.remove("manufacturer")
            expected_fields.remove("hw-revision")
        output = _verify_output(platform, "", expected_fields)

    with allure.step("Check hardware fields values"):
        if PlatformConsts.HW_ASIC_COUNT in output.keys():
            assert output[PlatformConsts.HW_ASIC_COUNT] == len(devices.dut.DEVICE_LIST) - 1,\
                "Unexpected value in {}\n Expect to have {}, but got {}"\
                .format(PlatformConsts.HW_ASIC_COUNT, len(devices.dut.DEVICE_LIST) - 1,
                        output[PlatformConsts.HW_ASIC_COUNT])
            assert "mqm" in output[PlatformConsts.HW_MODEL], "Invalid model name"
        mac = output[PlatformConsts.HW_MAC].split(":")
        assert len(mac) == 6, "Invalid mac format"


@pytest.mark.platform
@pytest.mark.cumulus
def test_show_platform_hardware_component(engines, devices):
    """
    Show platform hardware component test
    """
    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Check show hardware component output"):
        hw_comp_list = devices.dut.hw_comp_list
        output = _verify_output(platform, "component", hw_comp_list)

    if TestToolkit.tested_api == ApiType.NVUE:
        with allure.step("Check hardware components values"):
            for comp, comp_values in output.items():
                _verify_comp_fields(platform, comp, comp_values, devices)


def _verify_comp_fields(platform, comp, comp_values, devices):
    logging.info("comp {}".format(comp))
    assert not any(field not in comp_values.keys() for field in devices.dut.hw_comp_prop), "Not all fields were found"

    with allure.step("Check comp output"):
        _verify_output(platform, "component " + comp, devices.dut.hw_comp_prop)


def _verify_output(platform, comp_name, req_fields):
    logging.info("Required comp: " + str(req_fields))
    with allure.step("Verify text output"):
        logging.info("Verify text output")
        output = platform.hardware.show(comp_name, output_format=OutputFormat.auto)
        missing_fields = []
        for field in req_fields:
            if field not in output:
                missing_fields.append(field)
        assert missing_fields == [], "Missing fields: {}".format(missing_fields)

    with allure.step("Verify json output"):
        logging.info("Verify json output")
        output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
            platform.hardware.show(comp_name)).verify_result()
        Tools.ValidationTool.verify_field_exist_in_json_output(output, req_fields).verify_result()

    return output


# ------------ Open API tests -----------------

@pytest.mark.openapi
@pytest.mark.platform
def test_show_platform_hardware_component_openapi(engines, devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_show_platform_hardware_component(engines, devices)


@pytest.mark.openapi
@pytest.mark.platform
@pytest.mark.nvos_ci
def test_show_platform_hardware_openapi(devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_show_platform_hardware(devices)
