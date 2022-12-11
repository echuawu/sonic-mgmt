import logging
from ngts.cli_wrappers.openapi.openapi_base_clis import OpenApiBaseCli
from .openapi_command_builder import OpenApiCommandHelper
from ngts.nvos_constants.constants_nvos import OpenApiReqType
from ngts.nvos_constants.constants_nvos import ActionConsts, ActionType
logger = logging.getLogger()


class OpenApiSystemCli(OpenApiBaseCli):

    def __init__(self):
        self.cli_name = "System"

    @staticmethod
    def action_image(engine, action_str, action_component_str, op_param=""):
        logging.info("Running image action: '{action_type}' on dut using OpenApi".format(action_type=action_str))
        action_type = '@' + action_str
        params = \
            {
                ActionType.BOOT_NEXT:
                    {
                        "state": "start",
                        "parameters": {"partition": op_param}
                    },
                ActionType.UNINSTALL:
                    {
                        "state": "start",
                        "parameters": {"force": True if op_param == "force" else False}
                    },
                ActionType.FETCH:
                    {
                        "state": "start",
                        "parameters": {"remote-url": op_param}
                    }
            }
        return OpenApiCommandHelper.execute_action(action_type, engine.engine.username, engine.engine.password,
                                                   engine.ip, action_component_str, params[action_type])

    @staticmethod
    def action_files(engine, action_str, action_component_str, file, op_param=""):
        logging.info("Running file action: '{action_type}' on dut using OpenApi".format(action_type=action_str))
        action_type = '@' + action_str
        params = \
            {
                ActionType.DELETE:
                    {
                        "state": "start"
                    },
                ActionType.INSTALL:
                    {
                        "state": "start",
                        "parameters": {"force": op_param}
                    },
                ActionType.RENAME:
                    {
                        "state": "start",
                        "parameters": {"new-name": op_param}
                    },
                ActionType.UPLOAD:
                    {
                        "state": "start",
                        "parameters": {"remote-url": op_param}
                    }
            }
        return OpenApiCommandHelper.execute_action(action_type, engine.engine.username, engine.engine.password,
                                                   engine.ip, action_component_str, params[action_type])

    @staticmethod
    def action_firmware_install(engine, action_str, action_component_str, op_param=""):
        logging.info("Running action: 'firmware install' on dut using OpenApi".format(action_type=action_str))

        params = \
            {
                "asic-component": op_param,
                "auto-update": "enable",
                "default": "image",
                "@install": {
                    "state": "inactive",
                    "status": "string",
                    "timeout": 3600
                }
            }

        return OpenApiCommandHelper.execute_script(engine.engine.username, engine.engine.password,
                                                   OpenApiReqType.PATCH, engine.ip, action_component_str,
                                                   params)

    @staticmethod
    def action_generate_techsupport(engine, resource_path, field, value):
        logging.info("Running action: 'generate' on dut using OpenApi")

        params = \
            {
                "state": "start",
                "parameters": {
                    "since": value
                }
            }

        return OpenApiCommandHelper.execute_action(ActionType.GENERATE, engine.engine.username, engine.engine.password,
                                                   engine.ip, resource_path, params)
