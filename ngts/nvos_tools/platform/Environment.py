import allure
import logging
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.platform.Voltage import Voltage


class Environment(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/environment')
        self.voltage = Voltage(self)
        self.fan = BaseComponent(self, self.api_obj, '/fan')
        self.led = BaseComponent(self, self.api_obj, '/led')
        self.psu = BaseComponent(self, self.api_obj, '/psu')
        self.temperature = BaseComponent(self, self.api_obj, '/temperature')

    def unset(self, op_param=""):
        raise Exception("unset is not implemented")

    def set(self, op_param_name="", op_param_value={}):
        raise Exception("set is not implemented")

    def action_turn(self, turn_type="", led=""):
        with allure.step("Turn {type} led {led}".format(type=turn_type, led=led)):
            logging.info("Turn {type} led {led}".format(type=turn_type, led=led))
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_turn,
                                                   TestToolkit.engines.dut, turn_type, led)
