import logging
from ngts.cli_wrappers.nvue.nvue_base_clis import NvueBaseCli
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool

logger = logging.getLogger()


class NvueSystemCli(NvueBaseCli):

    def __init__(self):
        self.cli_name = "System"

    @staticmethod
    def action_image(engine, action_str, action_component_str, op_param=""):
        cmd = "nv action {action_type} system image {param}".format(action_type=action_str, param=op_param)
        cmd = " ".join(cmd.split())
        logging.info("Running action cmd: '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_upload(engine, path, file_name, url, op_param=""):
        path = path.replace('/', ' ')
        cmd = "nv action upload {path} {filename} {url}".format(path=path, filename=file_name, url=url)
        cmd = " ".join(cmd.split())
        logging.info("Running action cmd: '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_delete(engine, path, file_name, op_param=""):
        path = path.replace('/', ' ')
        cmd = "nv action delete {path} {filename}".format(path=path, filename=file_name)
        cmd = " ".join(cmd.split())
        logging.info("Running action cmd: '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_files(engine, action_str, resource_path, op_param=""):
        resource_path = resource_path.replace('/', ' ')
        cmd = "nv action {action_type} {resource_path} {param}" \
            .format(action_type=action_str, resource_path=resource_path, param=op_param)
        cmd = " ".join(cmd.split())
        logging.info("Running action cmd: '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_install_image_with_reboot(engine, action_str, resource_path, op_param=""):
        resource_path = resource_path.replace('/', ' ')
        cmd = "nv action {action_type} {resource_path} {param}" \
            .format(action_type=action_str, resource_path=resource_path, param=op_param)
        cmd = " ".join(cmd.split())
        logging.info("Running action cmd: '{cmd}' on dut using NVUE".format(cmd=cmd))
        return DutUtilsTool.reload(engine=engine, command=cmd, confirm=True).verify_result()

    @staticmethod
    def action_general(engine, action_str, resource_path, op_param=""):
        resource_path = resource_path.replace('/', ' ')
        cmd = "nv action {action_type} {resource_path} {param}" \
            .format(action_type=action_str, resource_path=resource_path, param=op_param)
        cmd = " ".join(cmd.split())
        logging.info("Running action cmd: '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_firmware_install(engine, param=""):
        cmd = "nv action install system firmware asic files {param}".format(param=param)
        logging.info("Running action cmd: '{cmd}' onl dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_firmware_image(engine, action_str, action_component_str, op_param=""):
        cmd = "nv action {action_type} system firmware asic {param}".format(action_type=action_str, param=op_param)
        cmd = " ".join(cmd.split())
        logging.info("Running action cmd: '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_install(engine, action_component_str, file=""):
        cmd = "nv action install system {action_component} files {file}".format(action_component=action_component_str, file=file)
        logging.info("Running action cmd: '{cmd}' onl dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_generate_techsupport(engine, resource_path, option="", time=""):
        path = resource_path.replace('/', ' ')
        cmd = "nv action generate {path} {option} {time}".format(path=path, option=option, time=time)
        cmd = " ".join(cmd.split())
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_reboot(engine, resource_path, op_param="", should_wait_till_system_ready=True):
        """
        Rebooting the switch
        """
        path = resource_path.replace('/', ' ')
        cmd = "nv action reboot {path} {op_param}".format(path=path, op_param=op_param)
        cmd = " ".join(cmd.split())
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return DutUtilsTool.reload(engine=engine, command=cmd, should_wait_till_system_ready=should_wait_till_system_ready,
                                   confirm=True).verify_result()

    @staticmethod
    def action_profile_change(engine, resource_path, op_param=""):
        """
        Rebooting the switch
        """
        path = resource_path.replace('/', ' ')
        cmd = "nv action change {path} profile {op_param}".format(path=path, op_param=op_param)
        cmd = " ".join(cmd.split())
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return DutUtilsTool.reload(engine=engine, command=cmd, confirm=True).verify_result()

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
    def action_fetch(engine, resource_path, remote_url):
        path = resource_path.replace('/', ' ')
        cmd = "nv action fetch {} {}".format(path, remote_url)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_export(engine, resource_path, file_name):
        path = resource_path.replace('/', ' ')
        cmd = "nv action export {} {}".format(path, file_name)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_write_to_logs(engine):
        permission_cmd = "sudo chmod 777 /var/log/syslog"
        write_content_cmd = "sudo sh -c 'echo regular_log >> /var/log/syslog'"
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=write_content_cmd))
        return engine.run_cmd_set([permission_cmd, write_content_cmd])

    @staticmethod
    def action_write_to_debug_logs(engine):
        write_content_cmd = "sudo sh -c 'echo debug_log >> /var/log/debug'"
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=write_content_cmd))
        return engine.run_cmd(write_content_cmd)

    @staticmethod
    def action_disconnect(engine, path):
        cmd = "nv action disconnect {path}".format(path=path)
        cmd = " ".join(cmd.split())
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_reset(engine, comp, param):
        cmd = "nv action reset system {comp} {params}".format(comp=comp, params=param)
        cmd = " ".join(cmd.split())
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return DutUtilsTool.reload(engine=engine, command=cmd, confirm=True).verify_result()

    @staticmethod
    def show_health_report(engine, param='', exit_cmd=''):
        cmd = "nv show system health history {param}".format(param=param)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd_after_cmd([cmd, exit_cmd])

    @staticmethod
    def action_change(engine, resource_path, op_params=""):
        path = resource_path.replace('/', ' ')
        cmd = "nv action change {path} {params}".format(path=path, params=op_params)
        cmd = " ".join(cmd.split())
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def show_file(engine, file='', exit_cmd=''):
        cmd = "nv show system stats files {file}".format(file=file)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd_after_cmd([cmd, exit_cmd])

    @staticmethod
    def action_clear(engine, resource_path, op_params=''):
        path = resource_path.replace('/', ' ')
        cmd = f"nv action clear {path} {op_params}"
        logging.info(f"Running '{cmd}' on dut using NVUE")
        return engine.run_cmd(cmd)
