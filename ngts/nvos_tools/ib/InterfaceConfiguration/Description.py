from .ConfigurationBase import ConfigurationBase
from .CmdBase import CmdBase
from .nvos_consts import IbInterfaceConsts
from .IbInterfaceDecorators import *
import logging
import allure

logger = logging.getLogger()


class Description(ConfigurationBase, CmdBase):
    def __init__(self, port_obj):
        ConfigurationBase.__init__(self,
                                   port_obj=port_obj,
                                   label=IbInterfaceConsts.DESCRIPTION,
                                   description="Details about the interface",
                                   field_name_in_db={},
                                   output_hierarchy=IbInterfaceConsts.DESCRIPTION)

    @operation_wrapper
    def set(self, value, dut_engine=None, apply=True, user_input=''):
        with allure.step('Set `description` to {value}'.format(value=value)):
            if not dut_engine:
                dut_engine = TestToolkit.engines.dut
            return CmdBase.set_interface(engine=dut_engine, field_name=IbInterfaceConsts.DESCRIPTION,
                                         port_name=self.port_obj.name,
                                         output_hierarchy=self.output_hierarchy, value=value, apply=apply,
                                         user_input=user_input)

    @operation_wrapper
    def unset(self, dut_engine=None, apply=True, user_input=''):
        with allure.step('Unset `description`'):
            if not dut_engine:
                dut_engine = TestToolkit.engines.dut
            return CmdBase.unset_interface(engine=dut_engine, field_name=IbInterfaceConsts.DESCRIPTION,
                                           output_hierarchy=self.output_hierarchy, apply=apply, user_input=user_input)
