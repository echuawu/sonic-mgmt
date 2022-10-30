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


@pytest.mark.system
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
    ib = Ib(None)
    with allure.step('select random value for {param}'.format(param=IbConsts.SM_PRIORITY)):
        with allure.step('select random value between 1 and 15'):
            random_val = random.randint(1, 15)
            logger.info('selected value = {val}'.format(val=random_val))

        with allure.step('Run nv set ib sm {param} {value}'.format(param=IbConsts.SM_PRIORITY, value=random_val)):
            ib.sm.set(IbConsts.SM_PRIORITY, str(random_val))

    with allure.step('select random value for {param}'.format(param=IbConsts.SM_SL)):
        with allure.step('select random value between 1 and 15'):
            random_val = random.randint(1, 15)
            logger.info('selected value = {val}'.format(val=random_val))

        with allure.step('Run nv set ib sm {param} {value}'.format(param=IbConsts.SM_SL, value=random_val)):
            ib.sm.set(IbConsts.SM_SL, str(random_val))

    with allure.step('Run nv set ib sm {param} {value} and apply the configurations'.format(param=IbConsts.SM_STATE, value=IbConsts.SM_STATE_ENABLE)):
        ib.sm.set(IbConsts.SM_STATE, IbConsts.SM_STATE_ENABLE)
        TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(engines.dut)

    with allure.step('Run nv unset ib and apply the configuration'):
        ib.unset()
        TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(engines.dut)

    with allure.step('verify changes using the show command out'):
        ib_dict = OutputParsingTool.parse_json_str_to_dictionary(ib.sm.show()).verify_result()
        ValidationTool.verify_field_value_in_output(ib_dict, IbConsts.SM_STATE, IbConsts.SM_STATE_DISABLE).verify_result()
        ValidationTool.verify_field_value_in_output(ib_dict, IbConsts.SM_PRIORITY, IbConsts.PRIO_SL_DEFAULT_VALUE).verify_result()
        ValidationTool.verify_field_value_in_output(ib_dict, IbConsts.SM_SL, IbConsts.PRIO_SL_DEFAULT_VALUE).verify_result()
