import pytest
from ngts.tools.test_utils import allure_utils as allure
import logging
import re
from ngts.nvos_tools.ib.Ib import Ib
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_constants.constants_nvos import IbConsts

logger = logging.getLogger()


@pytest.mark.ib
@pytest.mark.device
def test_show_ib_device(engines, devices):
    """
    Run show ib device and verify there is a correlation between the different values,
    and the values are in appropriate range.
    Test flow:
        1. Create an IB object.
        2. Run "nv show ib device" command.
        3. Verify all expected devices exist and have a valid value (not none).
        4. Go over all devices using "nv show ib device <device-id>" command, and verify their values
           (Supports multi-ASIC system as well):
           - GUID numbers are in the specific XX:XX:XX:XX:XX:XX:XX:XX format
           - lid value >= 0
           - subnet is not empty
           - type is as expected
        5. Verify SYSTEM and ASIC1 devices (should exist in every switch) have the same GUID number.
    """
    with allure.step("Create an IB object"):
        ib = Ib(None)

    with allure.step('Run nv show ib device command and verify that each field has a value'):
        output = OutputParsingTool.parse_json_str_to_dictionary(ib.device.show()).get_returned_value()

        ValidationTool.verify_all_fields_value_exist_in_output_dictionary(
            output, devices.dut.device_list).verify_result()
        assert len(devices.dut.device_list) == len(output), "Unexpected amount of ib devices.\n" \
                                                            "Expect {} devices:{} \n" \
                                                            "but got {} devices: {}".format(
            len(devices.dut.device_list),
            devices.dut.device_list,
            len(output), output.keys())

        for device in output:
            with allure.step('Run nv show ib device <device-id> command and verify that each field has a value'):
                dev_output = OutputParsingTool.parse_json_str_to_dictionary(
                    ib.device.show(device)).get_returned_value()

            if IbConsts.DEVICE_ASIC_PREFIX in device:
                verify_device_fields_and_validate_guid_value(IbConsts.DEVICE_ASIC_LIST, dev_output)
                assert dev_output['lid'] >= 0, "Invalid number of lid"
                assert dev_output['subnet'] != '', "Subnet should not be none"
                assert dev_output['type'] == devices.dut.ASIC_TYPE, "Unexpected ASIC type"
                if device == IbConsts.DEVICE_ASIC_PREFIX + '1':
                    asic1_guid = dev_output['guid']

            elif IbConsts.DEVICE_SYSTEM in device:
                verify_device_fields_and_validate_guid_value(IbConsts.DEVICE_SYSTEM_LIST, dev_output)
                system_guid = dev_output['guid']

            else:
                raise Exception("Found an unexpected device")

        assert asic1_guid == system_guid, "System and ASIC1 should have the same GUID value"


def verify_device_fields_and_validate_guid_value(device_list, device_output):
    with allure.step('Verify all device fields exist'):
        ValidationTool.validate_all_values_exists_in_list(device_list, device_output).verify_result()
    with allure.step('Validate device GUID value'):
        if not (re.match(IbConsts.GUID_FORMAT, device_output['guid'].lower())):
            raise Exception("Invalid GUID number, must be in XX:XX:XX:XX:XX:XX:XX:XX format")
