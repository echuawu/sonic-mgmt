import logging
from ngts.cli_wrappers.nvue.nvue_base_clis import NvueBaseCli
from ngts.nvos_constants.constants_nvos import ActionConsts

logger = logging.getLogger()


class NvueSystemCli(NvueBaseCli):

    def __init__(self):
        self.cli_name = "System"

    @staticmethod
    def action_image(engine, action_str, action_component_str, op_param=""):
        cmd = "nv action {action_type} system {action_component} {param}".format(action_type=action_str,
                                                                                 action_component=action_component_str,
                                                                                 param=op_param)
        logging.info("Running action cmd: '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_firmware_install(engine, action_component_str, op_param=""):
        cmd = "nv action install system {action_component} {param}".format(action_component=action_component_str,
                                                                           param=op_param)
        logging.info("Running action cmd: '{cmd}' onl dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_generate(engine, resource_path, option="", time=""):
        path = resource_path.replace('/', ' ')
        cmd = "nv action generate {path} {option} {time}".format(path=path, option=option, time=time)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_reboot(engine, resource_path, option="", op_param=""):
        """
        Rebooting the switch
        """
        path = resource_path.replace('/', ' ')
        cmd = "nv action reboot {path} {option} {op_param}".format(path=path, option=option, op_param=op_param)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.reload(cmd)

    @staticmethod
    def show_log(engine, log_type='', param='', exit_cmd=''):
        cmd = "nv show system {type}log {param}".format(type=log_type, param=param)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd_after_cmd([cmd, exit_cmd])

    @staticmethod
    def action_rotate_logs(engine):
        rotate_log_cmd = 'nv action rotate system log'
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=rotate_log_cmd))
        return engine.run_cmd(rotate_log_cmd)

    @staticmethod
    def action_rotate_debug_logs(engine):
        rotate_log_cmd = 'nv action rotate system debug-log'
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=rotate_log_cmd))
        return engine.run_cmd(rotate_log_cmd)

    @staticmethod
    def action_write_to_logs(engine):
        permission_cmd = "sudo chmod 777 /var/log/syslog"
        write_content_cmd = "sudo sh -c 'echo regular_log >> /var/log/syslog'"
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=write_content_cmd))
        return engine.run_cmd_set([permission_cmd, write_content_cmd])

    @staticmethod
    def action_write_to_debug_logs(engine):
        permission_cmd = "sudo chmod 777 /var/log/debug"
        write_content_cmd = "sudo sh -c 'echo debug_log >> /var/log/debug'"
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=write_content_cmd))
        return engine.run_cmd_set([permission_cmd, write_content_cmd])

    @staticmethod
    def action_set_system_log_component(engine, component, log_level=""):
        cmd = "nv set system log component {component} level {level}".format(component=component, level=log_level)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_unset_system_log_component(engine, component):
        cmd = "nv unset system log component {component} level ".format(component=component)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_upload(engine, log_file_type="", logging_file="", path=""):
        cmd = "nv action upload system {type}log files {log_file} {path}".format(type=log_file_type,
                                                                                 log_file=logging_file,
                                                                                 path=path)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_delete(engine, log_file_type="", logging_file=""):
        cmd = "nv action delete system {type}log files {log_file}".format(type=log_file_type, log_file=logging_file)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_disconnect(engine, path):
        cmd = "nv action disconnect {path}".format(path=path)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)
