import logging
import pytest
import allure
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_constants.constants_nvos import PlatformConsts
from ngts.nvos_constants.constants_nvos import OutputFormat
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType

logger = logging.getLogger()


@pytest.mark.platform
# TODO need to add pytest.mark.nvos_ci
def test_show_platform_hardware(devices):
    """
    Show platform hardware test
    """
    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Check show hardware output"):
        output = _verify_output(platform, "", PlatformConsts.HW_COMP)

    with allure.step("Check hardware fields values"):
        assert output[PlatformConsts.HW_ASIC_COUNT] == len(devices.dut.DEVICE_LIST) - 1,\
            "Unexpected value in {}\n Expect to have {}, but got {}"\
            .format(PlatformConsts.HW_ASIC_COUNT, len(devices.dut.DEVICE_LIST) - 1, output[PlatformConsts.HW_ASIC_COUNT])
        assert "mqm" in output[PlatformConsts.HW_MODEL], "Invalid model name"
        mac = output[PlatformConsts.HW_MAC].split(":")
        assert len(mac) == 6, "Invalid mac format"


@pytest.mark.platform
def test_show_platform_hardware_component(engines, devices):
    """
    Show platform hardware component test
    """
    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Check show hardware component output"):
        hw_comp_list = devices.dut.fan_list + devices.dut.psu_list
        hw_comp_list.append(PlatformConsts.HW_COMP_SWITCH)
        output = _verify_output(platform, "component", hw_comp_list)

    if TestToolkit.tested_api == ApiType.NVUE:
        with allure.step("Check hardware components values"):
            for comp, comp_values in output.items():
                _verify_comp_fields(platform, comp, comp_values)


def _verify_comp_fields(platform, comp, comp_values):
    logging.info("comp {}".format(comp))
    assert not any(field not in comp_values.keys() for field in PlatformConsts.HW_COMP_LIST), "Not all fields were found"

    with allure.step("Check comp output"):
        _verify_output(platform, "component " + comp, PlatformConsts.HW_COMP_LIST)


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
def test_show_platform_hardware_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_show_platform_hardware(engines)
