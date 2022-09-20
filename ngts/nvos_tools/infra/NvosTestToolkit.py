from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.cli_wrappers.openapi.openapi_general_clis import OpenApiGeneralCli
import logging
import allure

logger = logging.getLogger()


class TestToolkit:
    tested_ports = None
    engines = None
    tested_api = ApiType.NVUE
    GeneralApi = {ApiType.NVUE: NvueGeneralCli, ApiType.OPENAPI: OpenApiGeneralCli}

    @staticmethod
    def update_tested_ports(tested_ports):
        with allure.step("Update tested ports in TestTookit"):
            logging.info("Testes port/s: " + str(tested_ports))
            TestToolkit.tested_ports = tested_ports

    @staticmethod
    def update_engines(engines):
        with allure.step("Update engines object in TestTookit"):
            TestToolkit.engines = engines

    @staticmethod
    def update_apis(api_type):
        with allure.step("Update api in TestTookit to " + api_type):
            TestToolkit.tested_api = api_type
            logging.info("API updated to: " + api_type)

    @staticmethod
    def update_port_output_dictionary(port_obj, engine=None):
        with allure.step("Run 'show' command and update output dictionary"):
            logging.info("Run 'show' command and update output dictionary")
            port_obj.update_output_dictionary(engine if engine else TestToolkit.engines.dut)
