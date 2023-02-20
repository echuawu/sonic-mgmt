import allure
import logging
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli


class Ntp(BaseComponent):

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/ntp'
        self.parent_obj = parent_obj
        self.servers = NtpBaseResources(self, resource='server')
        self.keys = NtpBaseResources(self, resource='key')
        self.vrfs = NtpBaseResources(self, resource='vrf')


class NtpBaseResources(BaseComponent):
    def __init__(self, parent_obj, resource):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self.resource = resource
        self._resource_path = '/{resource}'.format(resource=resource)
        self.parent_obj = parent_obj
        self.resources_dict = {}

    def set_resource(self, resource_id, expected_str='', apply=False, ask_for_confirmation=False):
        with allure.step("Set {} with id : {}".format(self.resource, resource_id)):
            logging.info("Set {} with id : {}".format(self.resource, resource_id))
            resource_value = {} if TestToolkit.tested_api == ApiType.OPENAPI else ""
            result_obj = self.set(op_param_name=resource_id, op_param_value=resource_value, expected_str=expected_str,
                                  apply=apply, ask_for_confirmation=ask_for_confirmation)
            resource = NtpBaseResource(self, resource_id)
            self.resources_dict.update({resource_id: resource})
            return result_obj

    def unset_resource(self, resource_id, apply=False, ask_for_confirmation=False):
        result_obj = self.resources_dict[resource_id].unset(apply=apply, ask_for_confirmation=ask_for_confirmation)
        self.resources_dict.pop(resource_id)
        return result_obj


class NtpBaseResource(NtpBaseResources):
    def __init__(self, parent_obj, resource_id):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/{resource_id}'.format(resource_id=resource_id)
        self.parent_obj = parent_obj
        self.resource_id = resource_id
