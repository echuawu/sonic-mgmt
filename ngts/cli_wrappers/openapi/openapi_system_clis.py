import logging
from ngts.cli_wrappers.openapi.openapi_base_clis import OpenApiBaseCli
from .openapi_command_builder import OpenApiCommandHelper
from ngts.constants.constants_nvos import OpenApiReqType
from ngts.constants.constants_nvos import ActionConsts
logger = logging.getLogger()


class OpenApiSystemCli(OpenApiBaseCli):

    def __init__(self):
        self.cli_name = "System"

    @staticmethod
    def action_image(engine, action_str, action_component_str, op_param=""):
        logging.info("Running action: '{action_type}' on dut using OpenApi".format(action_type=action_str))

        params = \
            {
                ActionConsts.INSTALL:
                    {
                        "image": op_param,
                        "@install": {
                            "state": "inactive",
                            "status": "string",
                            "timeout": 3600
                        }
                    },
                ActionConsts.BOOT_NEXT:
                    {
                        "@boot-next": {
                            "state": "inactive",
                            "status": "string",
                            "timeout": 3600
                        },
                        "image": op_param,
                    },
                ActionConsts.REMOVE:
                    {
                        "@uninstall": {
                            "state": "inactive",
                            "status": "string",
                            "timeout": 3600
                        },
                        "image": op_param,
                    },
                ActionConsts.CLEANUP:
                    {
                        "@cleanup": {
                            "state": "inactive",
                            "status": "string",
                            "timeout": 3600
                        }
                    }
            }

        return OpenApiCommandHelper.execute_script(engine.engine.username, engine.engine.password,
                                                   OpenApiReqType.PATCH, engine.ip, action_component_str,
                                                   params[action_str])

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
