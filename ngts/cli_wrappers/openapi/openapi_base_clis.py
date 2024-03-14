import logging

from ngts.nvos_constants.constants_nvos import OpenApiReqType
from ngts.nvos_constants.constants_nvos import OutputFormat
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from .openapi_command_builder import OpenApiCommandHelper

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
                                                   OpenApiReqType.PATCH, engine.ip, resource_path, op_param_name,
                                                   op_param_value)

    @staticmethod
    def unset(engine, resource_path, op_param=""):
        logging.info("Running DELETE method on dut using openApi for {}".format(resource_path))
        return OpenApiCommandHelper.execute_script(engine.engine.username, engine.engine.password,
                                                   OpenApiReqType.DELETE, engine.ip, resource_path, op_param, None)

    @staticmethod
    def _resource_path_to_rest_path(resource_path: str, suffix=''):
        output = resource_path.replace(' ', '/')
        if suffix:
            output += '/' + suffix.replace('/', '%2F').replace(' ', '/')
        return output

    @staticmethod
    def _action_key(action: str):
        return '@' + action

    @staticmethod
    def action(engine, device, action_type: str, resource_path: str, suffix="", param_name="", param_value="",
               output_format=None, expect_reboot=False):
        """See documentation of BaseComponent.action"""
        url = OpenApiBaseCli._resource_path_to_rest_path(resource_path, suffix)
        data = {'state': 'start'}
        if param_name:
            data['parameters'] = {param_name: (True if (param_value == '') else param_value)}
        result = OpenApiCommandHelper.execute_action(
            OpenApiBaseCli._action_key(action_type), engine.engine.username, engine.engine.password, engine.ip,
            url, data)

        if expect_reboot:
            DutUtilsTool.wait_on_system_reboot(engine)

        return result

    @staticmethod
    def action_install_image_with_reboot(engine, device, action_str, resource_path, op_param="", recovery_engine=None):
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
                        "parameters": {"force": True if op_param == "force" else False}
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
        result = OpenApiCommandHelper.execute_action(action_type, engine.engine.username, engine.engine.password,
                                                     engine.ip, resource_path, params[action_type])

        if "Performing reboot" in result:
            logger.info("Waiting for switch shutdown after reload command")
            check_port_status_till_alive(False, engine.ip, engine.ssh_port)
            engine.disconnect()
            logger.info("Waiting for switch to be ready")
            check_port_status_till_alive(True, engine.ip, engine.ssh_port)

            recovery_engine = recovery_engine if recovery_engine else engine
            device.wait_for_os_to_become_functional(recovery_engine).verify_result()
        return result
