from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.cli_wrappers.nvue.nvue_ib_interface_clis import NvueIbInterfaceCli
from ngts.cli_wrappers.openapi.openapi_ib_interface_clis import OpenApiIbInterfaceCli
from ngts.nvos_constants.constants_nvos import ApiType
import logging

logger = logging.getLogger()


class Ip(BaseComponent):
    address = None
    gateway = None
    dhcp_client = None
    dhcp_client6 = None

    def __init__(self, port_obj):
        self.address = Address(self)
        self.gateway = Gateway(port_obj)
        self.dhcp_client = DhcpClient(self)
        self.dhcp_client6 = DhcpClient6(self)
        self.api_obj = {ApiType.NVUE: NvueIbInterfaceCli, ApiType.OPENAPI: OpenApiIbInterfaceCli}
        self._resource_path = '/ip'
        self.parent_obj = port_obj


class Address(BaseComponent):
    def __init__(self, port_obj):
        self.api_obj = {ApiType.NVUE: NvueIbInterfaceCli, ApiType.OPENAPI: OpenApiIbInterfaceCli}
        self._resource_path = '/address'
        self.parent_obj = port_obj


class Gateway(BaseComponent):
    def __init__(self, port_obj):
        self.api_obj = {ApiType.NVUE: NvueIbInterfaceCli, ApiType.OPENAPI: OpenApiIbInterfaceCli}
        self._resource_path = '/gateway'
        self.parent_obj = port_obj


class Hostname(BaseComponent):
    def __init__(self, port_obj):
        self.api_obj = {ApiType.NVUE: NvueIbInterfaceCli, ApiType.OPENAPI: OpenApiIbInterfaceCli}
        self._resource_path = '/set-hostname'
        self.parent_obj = port_obj


class State(BaseComponent):
    def __init__(self, port_obj):
        self.api_obj = {ApiType.NVUE: NvueIbInterfaceCli, ApiType.OPENAPI: OpenApiIbInterfaceCli}
        self._resource_path = '/state'
        self.parent_obj = port_obj


class DhcpClient(BaseComponent):
    def __init__(self, port_obj):
        self.api_obj = {ApiType.NVUE: NvueIbInterfaceCli, ApiType.OPENAPI: OpenApiIbInterfaceCli}
        self._resource_path = '/dhcp-client'
        self.parent_obj = port_obj


class DhcpClient6(BaseComponent):
    def __init__(self, port_obj):
        self.api_obj = {ApiType.NVUE: NvueIbInterfaceCli, ApiType.OPENAPI: OpenApiIbInterfaceCli}
        self._resource_path = '/dhcp-client6'
        self.parent_obj = port_obj
