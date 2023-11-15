import logging
import re
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_platform_clis import NvuePlatformCli
from ngts.cli_wrappers.openapi.openapi_platform_clis import OpenApiPlatformCli
from ngts.tools.test_utils import allure_utils as allure

logger = logging.getLogger()


class Voltage(BaseComponent):
    def __init__(self, parent_obj):
        self.platform_component_id = ""
        self.api_obj = {ApiType.NVUE: NvuePlatformCli, ApiType.OPENAPI: OpenApiPlatformCli}
        self._resource_path = '/voltage'
        self.parent_obj = parent_obj

    def get_sensors_list(self, engine, stringtoadd="VOLTAGE_INFO|"):
        """
        the out of the ls commands will be:
            total 0
            "drwxr-xr-x 2 root root 120 Jul  4 10:51 SENSOR NAME 1"
            "drwxr-xr-x 2 root root 120 Jul  4 10:51 SENSOR NAME 2"
            "drwxr-xr-x 2 root root 100 Jul  4 10:51 SENSOR NAME 3"

            /var/run/hw-management/ui/voltage/psu1:
            total 0
            "drwxr-xr-x 2 root root 280 Jul  4 12:41 SENSOR NAME 4"

        :return: list of sensors names, the returned value for the example:
            [SENSOR NAME 1, SENSOR NAME 2, SENSOR NAME 3, SENSOR NAME 4]
        """
        with allure.step('run ls command using voltage path'):
            sensors_path = '/var/run/hw-management/ui/voltage/*'
            sensors = engine.run_cmd('ls -l {} '.format(sensors_path)).splitlines()

        with allure.step('get the sensors list'):
            list_full_path = [x for x in sensors if x.startswith('dr')]
            sensors_list = []
            with allure.step('generate the database table name for each sensor'):
                for item in list_full_path:
                    sensors_list.append(self.get_file_name(item, stringtoadd))

        return sensors_list

    @staticmethod
    def get_file_name(file_full_detailes, stringtoadd=""):
        match = re.search("'([^']+)'", file_full_detailes)
        return stringtoadd + match.group(1)
