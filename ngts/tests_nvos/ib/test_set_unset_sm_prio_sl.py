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
    with allure.step('set/unset sm priority'):
        set_param_positive(engines.dut, IbConsts.SM_PRIORITY)


@pytest.mark.system
def test_set_ib_sm_prio_negative(engines):
    with allure.step('sm priority - invalid value'):
        set_param_negative(IbConsts.SM_PRIORITY)


@pytest.mark.system
def test_set_ib_sm_sl_positive(engines):
    with allure.step('set/unset sm sl'):
        set_param_positive(engines.dut, IbConsts.SM_SL)


@pytest.mark.system
def test_set_ib_sm_sl_negative(engines):
    with allure.step('sm sl - invalid value'):
        set_param_negative(IbConsts.SM_SL)


def set_param_positive(engine, param):
    """
    :param engine: dut engine
    :param param: sm-sl or sm-priority
    flow:
        1. select random value between 1 and 15
        2. run nv set ib sm <param>
        3. run nv config apply
        4. run nv show ib sm
        5. verify <param> value = random value
        6. run nv unset ib sm <param>
        7. run nv show ib sm
        8. verify <param> value = 0 (default value)
    """
    ib = Ib(None)
    with allure.step('set {param} to a random value between 1 and 15'):
        with allure.step('select random value between 1 and 15'):
            random_val = random.randint(1, 15)
            logger.info('selected value = {val}'.format(val=random_val))

        with allure.step('Run nv set ib sm {param} {value} and apply the configuration'.format(param=param, value=random_val)):
            ib.sm.set(param, str(random_val))
            TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(engine)

    with allure.step('verify changes using the show command out'):
        sm_dict = OutputParsingTool.parse_json_str_to_dictionary(ib.sm.show()).verify_result()
        ValidationTool.verify_field_value_in_output(sm_dict, param, str(random_val)).verify_result()

    with allure.step('Run nv unset ib sm {param} and apply the configuration'.format(param=param)):
        ib.sm.unset(param)
        TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(engine)

    with allure.step('verify changes using the show command out'):
        sm_dict = OutputParsingTool.parse_json_str_to_dictionary(ib.sm.show()).verify_result()
        ValidationTool.verify_field_value_in_output(sm_dict, param, IbConsts.PRIO_SL_DEFAULT_VALUE).verify_result()


def set_param_negative(param):
    """
    :param param: sm-sl or sm-priority
    flow:
        1. select random invalid positive number
        2. run nv set ib sm <param> <random_value_positive>
        3. verify the output includes "Invalid Command: set ib sm"
        4. select random invalid negative number
        5. run nv set ib sm <param> <random_value_negative>
        6. verify the output includes "Invalid Command: set ib sm"
    """
    ib = Ib(None)
    with allure.step('set invalid {param} values'.format(param=param)):
        with allure.step('select random value between 16 and 100'):
            random_val = random.randint(16, 100)
            logger.info('selected value = {val}'.format(val=random_val))
            with allure.step('Run nv set ib sm {param} {value}'.format(param=param, value=random_val)):
                output = ib.sm.set(param, str(random_val))
            assert 'Invalid Command: set ib sm' in output.info, "{val} is invalid for {param}".format(val=random_val, param=param)

        with allure.step('select random value between -100 and -1'):
            random_val = random.randint(-100, -1)
            logger.info('selected value = {val}'.format(val=random_val))
            output = ib.sm.set(param, str(random_val))
            assert 'Invalid Command: set ib sm' in output.info, "{val} is invalid for {param}".format(val=random_val, param=param)
