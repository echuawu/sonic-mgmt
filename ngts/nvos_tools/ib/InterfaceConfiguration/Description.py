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

    def set(self, value, dut_engine=None, apply=True):
        with allure.step('Set `description` to {value} for {port_name}'.format(value=value,
                                                                               port_name=self.port_obj.name)):
            if not dut_engine:
                dut_engine = TestToolkit.engines.dut
            return CmdBase.set_interface(engine=dut_engine, field_name=IbInterfaceConsts.DESCRIPTION,
                                         port_obj=self.port_obj,
                                         output_hierarchy=self.output_hierarchy, value=value, apply=apply)

    def unset(self, dut_engine=None, apply=True):
        with allure.step('Unset `description` for {port_name}'.format(port_name=self.port_obj.name)):
            if not dut_engine:
                dut_engine = TestToolkit.engines.dut
            return CmdBase.unset_interface(engine=dut_engine, field_name=IbInterfaceConsts.DESCRIPTION,
                                           port_obj=self.port_obj, output_hierarchy=self.output_hierarchy, apply=apply)
