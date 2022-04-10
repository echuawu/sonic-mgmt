from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import ApiType
import logging

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
    def update_apis(api_type):
        if api_type == ApiType.NVUE:
            TestToolkit.api_ib = ApiType.NVUE_IB
            TestToolkit.api_show = ApiType.NVUE_SHOW_CMDS
            TestToolkit.api_general = ApiType.NVUE_GENERAL
        else:
            TestToolkit.api_ib = ApiType.REST_IB
            TestToolkit.api_show = ApiType.REST_SHOW_CMDS
            TestToolkit.api_general = ApiType.REST_GENERAL

    @staticmethod
    def update_port_output_dictionary(port_obj, engine=None):
        logging.info("Running 'show' command before returning fields' value")
        port_obj.update_output_dictionary(engine if engine else TestToolkit.engines.dut)
