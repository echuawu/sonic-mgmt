import pytest
import allure
import random
import logging
from ngts.nvos_tools.ib.Ib import Ib
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_constants.constants_nvos import IbConsts

logger = logging.getLogger()


@pytest.mark.ib
@pytest.mark.sm
def test_set_ib_sm_prio_positive(engines):
    """
        testing nv unset ib command
        test flow:
            1. select random between 1 and 15
            2. run nv set ib sm sm-priority <random1>
            3. select random between 1 and 15
            4. run nv set ib sm sm-sl <random2>
            5. run nv set ib sm state enabled
            6. run nv config apply
            7. run nv unset ib
            8. run nv show ib sm
            9. verify all default values
    """
    with allure.step("Create IB object"):
        ib = Ib(None)

    with allure.step('select random value for {param}'.format(param=IbConsts.SM_PRIORITY)):
        with allure.step('select random value between 1 and 15'):
            priority_random_val = random.randint(1, 15)
            logger.info('selected value = {val}'.format(val=priority_random_val))

        with allure.step('Run nv set ib sm {param} {value}'.format(param=IbConsts.SM_PRIORITY, value=priority_random_val)):
            ib.sm.set(IbConsts.SM_PRIORITY, str(priority_random_val)).verify_result()

    with allure.step('select random value for {param}'.format(param=IbConsts.SM_SL)):
        with allure.step('select random value between 1 and 15'):
            sl_random_val = random.randint(1, 15)
            logger.info('selected value = {val}'.format(val=sl_random_val))

        with allure.step('Run nv set ib sm {param} {value}'.format(param=IbConsts.SM_SL, value=sl_random_val)):
            ib.sm.set(IbConsts.SM_SL, str(sl_random_val))

    with allure.step('Run nv set ib sm {param} {value} and apply the configurations'
                     .format(param=IbConsts.SM_STATE, value=IbConsts.SM_STATE_ENABLE)):
        ib.sm.set(IbConsts.SM_STATE, IbConsts.SM_STATE_ENABLE)
        TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(engines.dut)
        output = OutputParsingTool.parse_json_str_to_dictionary(ib.sm.show()).get_returned_value()
        ValidationTool.validate_fields_values_in_output(output_dict=output,
                                                        expected_fields=[IbConsts.SM_STATE, IbConsts.SM_PRIORITY,
                                                                         IbConsts.SM_SL],
                                                        expected_values=[IbConsts.SM_STATE_ENABLE, priority_random_val,
                                                                         sl_random_val])

        with allure.step("Unset and verify output"):
            ib.sm.unset(IbConsts.SM_STATE).verify_result()
            ib.sm.unset(IbConsts.SM_PRIORITY).verify_result()
            ib.sm.unset(IbConsts.SM_SL).verify_result()
            TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(engines.dut)

            output = OutputParsingTool.parse_json_str_to_dictionary(ib.sm.show()).get_returned_value()
            ValidationTool.validate_fields_values_in_output(output_dict=output,
                                                            expected_fields=[IbConsts.SM_STATE, IbConsts.SM_PRIORITY,
                                                                             IbConsts.SM_SL],
                                                            expected_values=[IbConsts.SM_STATE_DISABLE,
                                                                             IbConsts.PRIO_SL_DEFAULT_VALUE,
                                                                             IbConsts.PRIO_SL_DEFAULT_VALUE])

    with allure.step('Run nv unset ib and apply the configuration'):
        ib.sm.unset("").verify_result()
        TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(engines.dut)

    with allure.step('verify changes using the show command out'):
        ib_dict = OutputParsingTool.parse_json_str_to_dictionary(ib.sm.show()).verify_result()
        ValidationTool.verify_field_value_in_output(ib_dict, IbConsts.SM_STATE, IbConsts.SM_STATE_DISABLE).verify_result()
        ValidationTool.verify_field_value_in_output(ib_dict, IbConsts.SM_PRIORITY, IbConsts.PRIO_SL_DEFAULT_VALUE).verify_result()
        ValidationTool.verify_field_value_in_output(ib_dict, IbConsts.SM_SL, IbConsts.PRIO_SL_DEFAULT_VALUE).verify_result()

    with allure.step('Run nv set ib sm {param} {value} and apply the configurations'
                     .format(param=IbConsts.SM_STATE, value=IbConsts.SM_STATE_ENABLE)):
        ib.sm.set(IbConsts.SM_STATE, IbConsts.SM_STATE_ENABLE)
        TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(engines.dut)

        with allure.step("Unset ib and verify output"):
            ib.unset("").verify_result()
            TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(engines.dut)
            output = OutputParsingTool.parse_json_str_to_dictionary(ib.sm.show()).get_returned_value()
            ValidationTool.verify_field_value_in_output(output_dictionary=output,
                                                        field_name=IbConsts.SM_STATE,
                                                        expected_value=IbConsts.SM_STATE_DISABLE)
