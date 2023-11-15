from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_platform_clis import NvuePlatformCli
from ngts.cli_wrappers.openapi.openapi_platform_clis import OpenApiPlatformCli


class Action(BaseComponent):

    def __init__(self, action_job_id=0, parent_obj=None):
        self.jobid = JobId(self, action_job_id)
        self.api_obj = {ApiType.NVUE: NvuePlatformCli, ApiType.OPENAPI: OpenApiPlatformCli}
        self._resource_path = '/action'
        self.parent_obj = parent_obj

    def set(self, op_param_name="", op_param_value=""):
        raise Exception("set is not implemented for /action")

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for /action")


class JobId(BaseComponent):

    def __init__(self, parent_obj, action_job_id=0):
        self.api_obj = {ApiType.NVUE: NvuePlatformCli, ApiType.OPENAPI: OpenApiPlatformCli}
        if action_job_id == 0:
            self.action_job_id = ''
        else:
            self.action_job_id = action_job_id
        self._resource_path = '/{action_job_id}'
        self.parent_obj = parent_obj

    def get_resource_path(self):
        self_path = self._resource_path.format(action_job_id=self.action_job_id).rstrip("/")
        return "{parent_path}{self_path}".format(
            parent_path=self.parent_obj.get_resource_path() if self.parent_obj else "", self_path=self_path)

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for /action/{action_job_id}")

    def set(self, op_param_name="", op_param_value={}):
        raise Exception("set is not implemented for /action/{action_job_id}")
