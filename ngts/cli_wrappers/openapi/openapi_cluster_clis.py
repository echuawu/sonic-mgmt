import logging

from ngts.cli_wrappers.openapi.openapi_base_clis import OpenApiBaseCli
from ngts.nvos_constants.constants_nvos import ActionType
from .openapi_command_builder import OpenApiCommandHelper

logger = logging.getLogger()


class OpenApiClusterCli(OpenApiBaseCli):

    def __init__(self):
        self.cli_name = "Cluster"

    @staticmethod
    def action_start_cluster_app(engine, resource_path):
        params = \
            {
                "state": "start",
                "parameters": {
                }
            }

        return OpenApiCommandHelper.execute_action(ActionType.START, engine.engine.username, engine.engine.password,
                                                   engine.ip, resource_path, params)

    @staticmethod
    def action_stop_cluster_app(engine, resource_path):
         params = \
            {
                "state": "start",
                "parameters": {
                }
            }

        return OpenApiCommandHelper.execute_action(ActionType.STOP, engine.engine.username, engine.engine.password,
                                                   engine.ip, resource_path, params)


    @staticmethod
    def action_update_cluster_log_level(engine, resource_path, level):
        logging.info("Running action: 'upload' on dut using OpenApi")
        params = \
            {
                "state": "start",
                "parameters": {
                    'level': level
                }
            }
        return OpenApiCommandHelper.execute_action(ActionType.UPDATE, engine.engine.username, engine.engine.password,
                                                   engine.ip, resource_path, params)

    @staticmethod
    def action_restore_cluster(engine, resource_path):
       params = \
            {
                "state": "start",
                "parameters": {
                }
            }

        return OpenApiCommandHelper.execute_action(ActionType.RESTORE, engine.engine.username, engine.engine.password,
                                                   engine.ip, resource_path, params)

