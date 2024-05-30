import logging
import os
import signal
import subprocess
import time

import ngts.tools.test_utils.allure_utils as allure
from ngts.tests_nvos.system.gnmi.constants import GnmiMode, ERR_GNMIC_NOT_INSTALLED


class GnmiClient:
    def __init__(self, server_host, server_port, username, password, cmd_time: int = 5, cacert=''):
        assert cmd_time >= 0, f'unsupported cmd time: {cmd_time}. must be >= 0'

        self.server_host = server_host
        self.server_port = server_port
        self.username = username
        self.password = password
        self.cacert = cacert
        self.cmd_time = cmd_time

        with allure.step('verify gnmic installed on player'):
            self._verify_gnmic_installed()

    def run_subscribe_interface(self, mode: str, interface_name: str, username: str = '', password: str = '',
                                skip_cert_verify: bool = False, cacert='', debug_mode: bool = True,
                                cmd_time=None) -> str:
        assert mode in GnmiMode.ALL_MODES, f'unsupported gnmi subscribe mode: "{mode}"'
        subscribe_op = (f"subscribe --prefix 'interfaces/interface[name={interface_name}]/state' --path 'description' "
                        f"--target netq {mode} --format flat")
        return self._run_gnmic_op(subscribe_op, skip_cert_verify, cacert, debug_mode, cmd_time, username, password)

    def run_capabilities(self, username: str = '', password: str = '', skip_cert_verify: bool = False, cacert='',
                         debug_mode: bool = True, cmd_time=None) -> str:
        capabilities_op = "capabilities"
        return self._run_gnmic_op(capabilities_op, skip_cert_verify, cacert, debug_mode, cmd_time, username, password)

    def _run_gnmic_op(self, gnmi_op: str, skip_cert_verify: bool, cacert: str, debug_mode: bool, cmd_time,
                      username: str = '', password: str = '', ) -> str:
        with allure.step('compose the gnmic command'):
            username = username or self.username
            password = password or self.password

            if skip_cert_verify:
                cert_flag = '--skip-verify'
            else:
                cacert_to_use = cacert or self.cacert
                assert cacert_to_use, 'cacert path was not specified'
                cert_flag = f'--tls-ca {cacert_to_use}'

            gnmic_cmd = (f"gnmic -a {self.server_host} --port {self.server_port} {cert_flag} "
                         f"-u {username} -p {password} {gnmi_op}") + (" -d" if debug_mode else "")
        with allure.step('run gnmic command in process'):
            return self._run_cmd_in_process(gnmic_cmd, cmd_time)

    def _verify_gnmic_installed(self):
        cmd = 'gnmic version'
        output = self._run_cmd_in_process(cmd)
        assert ERR_GNMIC_NOT_INSTALLED not in output, f"gnmic is not installed on player.\n{cmd}\n{output}"

    def _run_cmd_in_process(self, cmd: str, cmd_time=None) -> str:
        self._log(f"run: {cmd}")
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   preexec_fn=os.setsid)
        if process.poll() is None:
            sleep_time = cmd_time or self.cmd_time
            self._log(f'process not finished yet. wait {sleep_time} seconds')
            time.sleep(sleep_time)
            self._log(f'wait time is up. kill process and get output')
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        output, err = process.communicate()
        output = output.decode('utf-8')
        err = err.decode('utf-8')
        self._log(f"output: {output}")
        self._log(f"err: {err}")
        return output

    def _log(self, msg: str):
        logging.info(f"[GnmiClient] {msg}")
