
import logging
from typing import Dict
from ngts.nvos_tools.infra.DefaultDict import DefaultDict
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.system.Image import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli


class FilesResource(BaseComponent):

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/files'
        self.parent_obj = parent_obj


class SystemImageFiles(FilesResource):

    def __init__(self, parent_obj):
        super().__init__(parent_obj)
        self.file: Dict[str, SystemImageFile] = DefaultDict(lambda filename: SystemImageFile(self, filename))


# ----------------


class FileResource(BaseComponent):

    def __init__(self, parent_obj, filename):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self.parent_obj = parent_obj
        self._resource_path = f'/{filename}'
        self.filename = filename


class SystemImageFile(FileResource):

    def __init__(self, parent_obj, filename):
        super().__init__(parent_obj, filename)

    def action_install(self, param_force=None, param_reboot=None, engine=None):
        """
        Execute action install on system image file

        :param param_force: if True- send with 'force' option. if None- don't. defaults to None
        :param param_reboot: if 'yes'- send with 'reboot yes' option. if 'no'- send with 'reboot no' option.
            if None- don't send with 'reboot' option. defaults to None
        """
        assert param_force is None or param_reboot is None, f'One of params "param_force"/"param_reboot" must be None.\nActual "param_force"={param_force} ; "param_reboot"={param_reboot}'
        if param_force is not None:
            assert param_force is True, f'Param "param_force" must be in [None, True]. Actual "param_force"={param_force}'
            param, param_val = 'force', ''
        elif param_reboot is not None:
            assert param_reboot in ['yes', 'no'], f'Param "param_reboot" must be in ["yes", "no", None]. Actual "param_reboot"={param_reboot}'
            param, param_val = 'reboot', param_reboot
        else:
            param, param_val = '', ''

        if TestToolkit.tested_api == ApiType.OPENAPI:
            param = {param: param_val} if param else {}

        resource_path = self.get_resource_path()
        if engine is None:
            engine = TestToolkit.engines.dut
        logging.info(f'Run action install on: {resource_path}')
        return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_install,
                                               engine, resource_path, param, param_val)
