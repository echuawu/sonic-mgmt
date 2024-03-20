import logging
from ngts.cli_wrappers.nvue.nvue_base_clis import NvueBaseCli
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_base_clis import OpenApiBaseCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.PortFastRecovery import PortFastRecovery
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.system.Firmware import Firmware
from ngts.nvos_tools.system.Health import Health
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_tools.ib.InterfaceConfiguration.Interface import Interface

logger = logging.getLogger()


class Fae(BaseComponent):
    def __init__(self, parent_obj=None, port_name='eth0'):
        BaseComponent.__init__(self, parent=parent_obj,
                               api={ApiType.NVUE: NvueBaseCli, ApiType.OPENAPI: OpenApiBaseCli}, path='/fae')
        self.system = BaseComponent(self, {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}, '/system')
        self.firmware = Firmware(self)
        self.ipoibmapping = BaseComponent(self, path='/ipoib-mapping')
        self.health = Health(self)
        self.port = MgmtPort(port_name, self)
        self.fast_recovery = PortFastRecovery(self)
        self.ib = Ib(self)
        self.sonic_cli = SonicCli(self)
        self.platform = Platform(self)
        self.interface = Interface(self, port_name)


class Ib(BaseComponent):
    def __init__(self, parent_obj=None):
        super().__init__(parent=parent_obj, path='/ib')
        self.ufm_mad = BaseComponent(self, path='/ufm-mad')


class SonicCli(BaseComponent):
    def __init__(self, parent_obj=None):
        super().__init__(parent=parent_obj,
                         api={ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}, path='/sonic-cli')

    def action_general(self, action_str):
        return SendCommandTool.execute_command(
            self.api_obj[TestToolkit.tested_api].action_general_with_expected_disconnect,
            TestToolkit.engines.dut, action_str, self.get_resource_path())
