import logging
from ngts.cli_wrappers.openapi.openapi_base_clis import OpenApiBaseCli
from ngts.nvos_constants.constants_nvos import ActionConsts, ActionType
from .openapi_command_builder import OpenApiCommandHelper
from ngts.nvos_constants.constants_nvos import OpenApiReqType
from ngts.cli_wrappers.openapi.openapi_base_clis import OpenApiBaseCli

logger = logging.getLogger()


class OpenApiPlatformCli(OpenApiBaseCli):

    def __init__(self):
        self.cli_name = "Platform"

    def action_turn(engine, turn_type="", led=""):
        logging.info("Running action: 'turn' on dut using OpenApi")
        if led[-2] == '/':
            led = led.replace('/', '%2F')
        resource_path = '/platform/environment/led/{led}'.format(led=led)
        params = {"state": "start"}
        if turn_type == 'on':
            action = ActionType.TURNON
        else:
            action = ActionType.TURNOFF
        return OpenApiCommandHelper.execute_action(action, engine.engine.username, engine.engine.password,
                                                   engine.ip, resource_path, params)
