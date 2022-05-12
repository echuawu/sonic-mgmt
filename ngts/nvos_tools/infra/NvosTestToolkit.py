from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import ApiType
import logging
import allure

logger = logging.getLogger()


class TestToolkit:
    tested_ports = None
    api_ib = ApiType.NVUE_IB
    api_show = ApiType.NVUE_SHOW_CMDS
    api_general = ApiType.NVUE_GENERAL
    engines = None

    api_str = {ApiType.NVUE_IB: "NVUE", ApiType.NVUE_SHOW_CMDS: "NVUE", ApiType.NVUE_GENERAL: "NVUE",
               ApiType.REST_IB: "REST", ApiType.REST_GENERAL: "REST", ApiType.REST_SHOW_CMDS: "REST"}

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
        with allure.step("Update apis in TestTookit"):
            if api_type == ApiType.NVUE:
                TestToolkit.api_ib = ApiType.NVUE_IB
                TestToolkit.api_show = ApiType.NVUE_SHOW_CMDS
                TestToolkit.api_general = ApiType.NVUE_GENERAL
            else:
                TestToolkit.api_ib = ApiType.REST_IB
                TestToolkit.api_show = ApiType.REST_SHOW_CMDS
                TestToolkit.api_general = ApiType.REST_GENERAL
            logging.info("API updated to: " + api_type)

    @staticmethod
    def update_port_output_dictionary(port_obj, engine=None):
        with allure.step("Run 'show' command and update output dictionary"):
            logging.info("Run 'show' command and update output dictionary")
            port_obj.update_output_dictionary(engine if engine else TestToolkit.engines.dut)
