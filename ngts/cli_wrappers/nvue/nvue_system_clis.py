import logging

from infra.tools.validations.traffic_validations.ping.send import ping_till_alive
from ngts.cli_wrappers.nvue.nvue_base_clis import NvueBaseCli
from ngts.nvos_constants.constants_nvos import CertificateFiles
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from ngts.nvos_tools.infra.ResultObj import ResultObj
from ngts.tools.test_utils import allure_utils as allure

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
    def action_install_image_with_reboot(engine, device, action_str, resource_path, op_param="", recovery_engine=None):
        resource_path = resource_path.replace('/', ' ')
        cmd = "nv action {action_type} {resource_path} {param}" \
            .format(action_type=action_str, resource_path=resource_path, param=op_param)
        cmd = " ".join(cmd.split())
        logging.info("Running action cmd: '{cmd}' on dut using NVUE".format(cmd=cmd))
        return DutUtilsTool.reload(engine=engine, device=device, command=cmd, confirm=True,
                                   recovery_engine=recovery_engine).verify_result()

    @staticmethod
    def action_general(engine, action_str, resource_path, op_param=""):
        resource_path = resource_path.replace('/', ' ')
        cmd = "nv action {action_type} {resource_path} {param}" \
            .format(action_type=action_str, resource_path=resource_path, param=op_param)
        cmd = " ".join(cmd.split())
        logging.info("Running action cmd: '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_general_with_expected_disconnect(engine, action_str, resource_path, op_param="", timeout=10):
        resource_path = resource_path.replace('/', ' ')
        cmd = "nv action {action_type} {resource_path} {param}" \
            .format(action_type=action_str, resource_path=resource_path, param=op_param)
        cmd = " ".join(cmd.split())
        logging.info("Running action cmd: '{cmd}' on dut using NVUE".format(cmd=cmd))
        return DutUtilsTool.run_cmd_with_disconnect(engine, cmd, timeout=timeout)

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
    def action_install(engine, resource_path, param='', param_val=''):
        cmd = f'nv action install {resource_path.replace("/", " ").strip()} {param} {param_val}'.strip()
        with allure.step("Run action cmd: '{cmd}' onl dut using NVUE".format(cmd=cmd)):
            if 'system/image' in resource_path:
                res = ResultObj(result=False, info='Switch should have rebooted but possible that it did not')
                try:
                    engine.run_cmd(cmd, timeout=30)
                except Exception:
                    logger.info("Waiting for switch to be ready")
                    # check_port_status_till_alive(True, engine.ip, engine.ssh_port)
                    with allure.step('Ping switch until shutting down'):
                        ping_till_alive(should_be_alive=False, destination_host=engine.ip, delay=10, tries=75)
                    with allure.step('Ping switch until back alive'):
                        ping_till_alive(should_be_alive=True, destination_host=engine.ip, delay=5, tries=150)
                    with allure.step('Wait till nvos is up again'):
                        engine.disconnect()
                        res = DutUtilsTool.wait_for_nvos_to_become_functional(engine=engine)
                finally:
                    return res.verify_result()
            else:
                return engine.run_cmd(cmd)

    @staticmethod
    def action_generate_techsupport(engine, resource_path, option="", time=""):
        path = resource_path.replace('/', ' ')
        cmd = "nv action generate {path} {option} {time}".format(path=path, option=option, time=time)
        cmd = " ".join(cmd.split())
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_generate_tpm_quote(engine, resource_path, pcrs='', nonce='', algorithm=''):
        path = resource_path.replace('/', ' ').strip()
        cmd = f'nv action generate {path}'
        for param in [pcrs, nonce]:
            if param:
                cmd += f' {param}'
        if algorithm:
            cmd += f' algorithm {algorithm}'
        cmd = ' '.join(cmd.split())
        logging.info(f"Running '{cmd}' on dut using NVUE")
        return engine.run_cmd(cmd)

    @staticmethod
    def action_upload_tpm_file(engine, resource_path, file_name, remote_url):
        path = resource_path.replace('/', ' ').strip()
        cmd = f'nv action upload {path} {file_name} {remote_url}'
        logging.info(f"Running '{cmd}' on dut using NVUE")
        return engine.run_cmd(cmd)

    @staticmethod
    def action_reboot(engine, device, resource_path, op_param="", should_wait_till_system_ready=True):
        """
        Rebooting the switch
        """
        path = resource_path.replace('/', ' ')
        cmd = "nv action reboot {path} {op_param}".format(path=path, op_param=op_param)
        cmd = " ".join(cmd.split())
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return DutUtilsTool.reload(engine=engine, device=device, command=cmd,
                                   should_wait_till_system_ready=should_wait_till_system_ready,
                                   confirm=True).verify_result()

    @staticmethod
    def action_profile_change(engine, device, resource_path, op_param=""):
        """
        Rebooting the switch
        """
        list_items = [f'{key} {value}' for key, value in op_param.items()]
        op_param = ' '.join(list_items)
        path = resource_path.replace('/', ' ')
        cmd = "nv action change {path} {op_param}".format(path=path, op_param=op_param)
        cmd = " ".join(cmd.split())
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return DutUtilsTool.reload(engine=engine, device=device, command=cmd, confirm=True).verify_result()

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
        return DutUtilsTool.run_cmd_with_disconnect(engine, cmd, timeout=5)

    @staticmethod
    def action_reset(engine, device, comp, param):
        cmd = "nv action reset system {comp} {params}".format(comp=comp, params=param)
        cmd = " ".join(cmd.split())
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return DutUtilsTool.reload(engine=engine, device=device, command=cmd, confirm=True).verify_result()

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

    @staticmethod
    def action_import(engine, resource_path, import_type, cert_id, uri1, uri2, passphrase, data):
        path = resource_path.replace('/', ' ')

        action_import = f"nv action import {path} {cert_id}"
        action_import_dict = {
            CertificateFiles.URI_BUNDLE: f"{action_import} {import_type} {uri1} {CertificateFiles.PASSPHRASE} {passphrase}",
            CertificateFiles.PUBLIC_PRIVATE: f"{action_import} {CertificateFiles.PUBLIC_KEY_FILE} {uri1} {CertificateFiles.PRIVATE_KEY_FILE} {uri2}",
            CertificateFiles.DATA: f"{action_import} {import_type} {data}",
            CertificateFiles.URI: f"{action_import} {import_type} {uri1}"}

        cmd = " ".join(action_import_dict[import_type].split())
        logging.info("Running action cmd: '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)
