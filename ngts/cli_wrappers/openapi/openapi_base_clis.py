import logging
from ngts.nvos_constants.constants_nvos import OutputFormat
from .openapi_command_builder import OpenApiCommandHelper
from ngts.nvos_constants.constants_nvos import OpenApiReqType

logger = logging.getLogger()


class OpenApiBaseCli:
    cli_name = ""

    @staticmethod
    def show(engine, resource_path, op_param="", output_format=OutputFormat.json):
        logging.info("Running GET method on dut using openApi for {}".format(resource_path))
        return OpenApiCommandHelper.execute_script(engine.engine.username, engine.engine.password,
                                                   OpenApiReqType.GET, engine.ip, resource_path, op_param)

    @staticmethod
    def set(engine, resource_path, op_param_name="", op_param_value=""):
        logging.info("Running PATCH method on dut using openApi for {}".format(resource_path))
        return OpenApiCommandHelper.execute_script(engine.engine.username, engine.engine.password,
                                                   OpenApiReqType.PATCH, engine.ip, resource_path, op_param_name, op_param_value)

    @staticmethod
    def unset(engine, resource_path, op_param=""):
        logging.info("Running DELETE method on dut using openApi for {}".format(resource_path))
        return OpenApiCommandHelper.execute_script(engine.engine.username, engine.engine.password,
                                                   OpenApiReqType.DELETE, engine.ip, resource_path, op_param)
