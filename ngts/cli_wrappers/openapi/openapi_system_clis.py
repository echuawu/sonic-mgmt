import logging
from ngts.cli_wrappers.openapi.openapi_base_clis import OpenApiBaseCli
from .openapi_command_builder import OpenApiCommandHelper
from ngts.nvos_constants.constants_nvos import OpenApiReqType
from ngts.nvos_constants.constants_nvos import ActionConsts, ActionType
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from infra.tools.validations.traffic_validations.port_check.port_checker import check_port_status_till_alive

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
    def action_files(engine, action_str, resource_path, op_param=""):
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
                                                   engine.ip, resource_path, params[action_type])

    @staticmethod
    def action_install_image_with_reboot(engine, device, action_str, resource_path, op_param=""):
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

            device.wait_for_os_to_become_functional(engine).verify_result()
        return result

    @staticmethod
    def action_general(engine, action_str, resource_path):
        logging.info("Running action: '{action_type}' on dut using OpenApi, resource: '{rsrc}'".
                     format(action_type=action_str, rsrc=resource_path))
        action_type = '@' + action_str
        params = \
            {
                ActionType.CLEAR:
                    {
                        "state": "start"
                    },
                ActionType.GENERATE:
                    {
                        "state": "start",
                    },
                ActionType.ENABLE:
                    {
                        "state": "start",
                    },
                ActionType.DISABLE:
                    {
                        "state": "start",
                    }
            }
        return OpenApiCommandHelper.execute_action(action_type, engine.engine.username, engine.engine.password,
                                                   engine.ip, resource_path, params[action_type])

    @staticmethod
    def action_general_with_expected_disconnect(engine, action_str, resource_path):
        logging.info("Running action: '{action_type}' on dut using OpenApi, resource: '{rsrc}'".
                     format(action_type=action_str, rsrc=resource_path))
        action_type = '@' + action_str
        params = \
            {
                ActionType.CLEAR:
                    {
                        "state": "start"
                    },
                ActionType.GENERATE:
                    {
                        "state": "start",
                    },
                ActionType.ENABLE:
                    {
                        "state": "start",
                    },
                ActionType.DISABLE:
                    {
                        "state": "start",
                    }
            }
        output = OpenApiCommandHelper.execute_action(action_type, engine.engine.username, engine.engine.password,
                                                     engine.ip, resource_path, params[action_type])
        engine.disconnect()
        return output

    @staticmethod
    def action_firmware_install(engine, op_param=""):
        logging.info("Running action: 'firmware install' on dut using OpenApi")

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
                                                   OpenApiReqType.PATCH, engine.ip, "/system/firmware/asic",
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

    @staticmethod
    def action_reset(engine, device, comp, param):
        logging.info("Running action: reset system {} on dut using OpenApi".format(comp))

        assert not param, "params are not supported yet"

        params = {}

        return OpenApiCommandHelper.execute_action(ActionType.RESET, engine.engine.username, engine.engine.password,
                                                   engine.ip, "/system/{}".format(comp), params)

    @staticmethod
    def action_rotate_logs(engine):
        logging.info("Running action: rotate system log on dut using OpenApi")
        params = \
            {
                "state": "start",
            }
        return OpenApiCommandHelper.execute_action(ActionType.ROTATE, engine.engine.username, engine.engine.password,
                                                   engine.ip, "/system/log", params)

    @staticmethod
    def action_reboot(engine, device, resource_path, op_param="", should_wait_till_system_ready=True):
        logging.info("Running action: rotate system log on dut using OpenApi")
        parameters_dict = {}
        if "force" in op_param:
            parameters_dict.update({"force": True})
        if "immediate" in op_param:
            parameters_dict.update({"immediate": True})
        if "proceed" in op_param:
            parameters_dict.update({"proceed": True})
        params = \
            {
                "state": "start"
            }
        if parameters_dict:
            params.update({"parameters": parameters_dict})
        result = OpenApiCommandHelper.execute_action(ActionType.REBOOT, engine.engine.username, engine.engine.password,
                                                     engine.ip, resource_path, params)
        if "Performing reboot" in result:
            logger.info("Waiting for switch shutdown after reload command")
            check_port_status_till_alive(False, engine.ip, engine.ssh_port)
            engine.disconnect()
            logger.info("Waiting for switch to be ready")
            check_port_status_till_alive(True, engine.ip, engine.ssh_port)

        if should_wait_till_system_ready:
            device.wait_for_os_to_become_functional(engine).verify_result()
        return result

    @staticmethod
    def action_change(engine, resource_path, params_dict=None):
        logging.info("Running action: 'change' on dut using OpenApi, resource: {rsrc}".format(rsrc=resource_path))

        params = \
            {
                "state": "start",
                "parameters": params_dict
            }

        return OpenApiCommandHelper.execute_action(ActionType.CHANGE, engine.engine.username, engine.engine.password,
                                                   engine.ip, resource_path, params)

    @staticmethod
    def show_file(engine, file='', exit_cmd=''):
        # TODO not supported yet
        return ""

    @staticmethod
    def action_clear(engine, resource_path, params_dict=None):
        logging.info("Running action: 'clear' on dut using OpenApi, resource: {rsrc}".format(rsrc=resource_path))

        params = \
            {
                "state": "start",
                "parameters": params_dict
            }

        return OpenApiCommandHelper.execute_action(ActionType.CLEAR, engine.engine.username, engine.engine.password,
                                                   engine.ip, resource_path, params)

    @staticmethod
    def action_profile_change(engine, device, resource_path, params_dict=None, should_wait_till_system_ready=True):
        logging.info("Running action: 'profile change' on dut using OpenApi, resource: {rsrc}"
                     .format(rsrc=resource_path))

        params = \
            {
                "state": "start",
                "parameters": params_dict
            }

        result = OpenApiCommandHelper.execute_action(ActionType.CHANGE, engine.engine.username, engine.engine.password,
                                                     engine.ip, resource_path, params)

        if "System will be rebooted" in result:
            logger.info("Waiting for switch shutdown after reload command")
            check_port_status_till_alive(False, engine.ip, engine.ssh_port)
            engine.disconnect()
            logger.info("Waiting for switch to be ready")
            check_port_status_till_alive(True, engine.ip, engine.ssh_port)

        if should_wait_till_system_ready:
            DutUtilsTool.wait_for_nvos_to_become_functional(engine).verify_result()

    @staticmethod
    def action_install(engine, resource_path, param_dict={}, unused_param_val=''):
        logging.info(f'Run action install on: {resource_path}')

        params = {
            'state': 'start',
            'parameters': param_dict
        }

        return OpenApiCommandHelper.execute_action(ActionType.INSTALL, engine.username, engine.password,
                                                   engine.ip, resource_path, params)
