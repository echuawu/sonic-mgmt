import logging
import os
import signal
import subprocess
import time
from typing import Tuple, List

import ngts.tools.test_utils.allure_utils as allure
from ngts.tests_nvos.system.gnmi.constants import GnmiMode, GnmicErr


class GnmiClient:
    def __init__(self, server_host, server_port, username, password, cmd_time: int = 5, cacert='',
                 verify_tools_installed: bool = False):
        assert cmd_time >= 0, f'unsupported cmd time: {cmd_time}. must be >= 0'

        self.server_host = server_host
        self.server_port = server_port
        self.username = username
        self.password = password
        self.cacert = cacert
        self.cmd_time = cmd_time

        if verify_tools_installed:
            with allure.step('verify gnmic installed on player'):
                self._verify_gnmic_installed()
            with allure.step('verify grpcurl installed on player'):
                self._verify_grpcurl_installed()

        self._live_processes: List[subprocess.Popen] = []

    def __del__(self):
        self._log('close live processes')
        for process in self._live_processes:
            self.close_session_and_get_out_and_err(process)

    def run_subscribe_interface(self, mode: str, interface_name: str, username: str = '', password: str = '',
                                skip_cert_verify: bool = False, cacert='', debug_mode: bool = True,
                                cmd_time=None, wait_till_done: bool = False) -> Tuple[str, str]:
        out, err, _ = self._run_subscribe_interface(mode, interface_name, username, password, skip_cert_verify, cacert,
                                                    debug_mode, cmd_time, False, wait_till_done)
        return out, err

    def run_subscribe_interface_and_keep_session_alive(self, mode: str, interface_name: str, username: str = '',
                                                       password: str = '',
                                                       skip_cert_verify: bool = False, cacert='',
                                                       debug_mode: bool = True) -> subprocess.Popen:

        _, _, process = self._run_subscribe_interface(mode, interface_name, username, password, skip_cert_verify,
                                                      cacert,
                                                      debug_mode, None, True)
        self._live_processes.append(process)
        return process

    def run_capabilities(self, username: str = '', password: str = '', skip_cert_verify: bool = False, cacert='',
                         debug_mode: bool = True, cmd_time=None, wait_till_done: bool = False) -> Tuple[str, str]:
        capabilities_op = "capabilities"
        out, err, _ = self._run_gnmic_op(capabilities_op, skip_cert_verify, cacert, debug_mode, cmd_time, username,
                                         password, wait_till_done=wait_till_done)
        return out, err

    def close_session_and_get_out_and_err(self, process: subprocess.Popen, delay=None, kill_immediately: bool = True) -> \
            Tuple[str, str]:
        if not kill_immediately and process.poll() is None:
            sleep_time = delay or self.cmd_time
            self._log(f'process not finished yet. wait {sleep_time} seconds')
            time.sleep(sleep_time)
        self._log(f'kill process and get output')
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        return self._get_cmd_process_output(process)

    def run_describe(self, username: str = '', password: str = '', skip_cert_verify: bool = True, cacert='',
                     cmd_time=None, service='') -> Tuple[str, str]:
        describe_op = f"describe {service}"
        out, err, _ = self._run_grpcurl_op(describe_op, skip_cert_verify, cacert, cmd_time, username,
                                           password)
        return out, err

    def _run_subscribe_interface(self, mode: str, interface_name: str, username: str = '', password: str = '',
                                 skip_cert_verify: bool = False, cacert='', debug_mode: bool = True,
                                 cmd_time=None, keep_session_alive: bool = False, wait_till_done: bool = False) -> \
            Tuple[str, str, subprocess.Popen]:
        allowed_modes = GnmiMode.ALL_MODES if not keep_session_alive else [GnmiMode.STREAM, GnmiMode.POLL]
        assert mode in allowed_modes, f'unsupported gnmi subscribe mode: "{mode}"'
        mode = f"--mode {mode}" if mode != GnmiMode.STREAM else GnmiMode.STREAM
        subscribe_op = (f"subscribe --prefix 'interfaces/interface[name={interface_name}]/state' --path 'description' "
                        f"--target netq {mode} --format flat")
        return self._run_gnmic_op(subscribe_op, skip_cert_verify, cacert, debug_mode, cmd_time, username, password,
                                  keep_session_alive, wait_till_done)

    def _run_gnmic_op(self, gnmi_op: str, skip_cert_verify: bool, cacert: str, debug_mode: bool, cmd_time,
                      username: str = '', password: str = '', keep_session_alive: bool = False,
                      wait_till_done: bool = False) -> Tuple[
            str, str, subprocess.Popen]:
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
            return self._run_cmd_in_process(gnmic_cmd, cmd_time, keep_session_alive, wait_till_done)

    def _run_grpcurl_op(self, grpcurl_op: str, is_insecure: bool, cacert: str, cmd_time, username: str = '',
                        password: str = '', keep_session_alive: bool = False) -> Tuple[
            str, str, subprocess.Popen]:
        with allure.step('compose the grpcurl command'):
            username = username or self.username
            password = password or self.password

            if is_insecure:
                cert_flag = '-insecure'
            else:
                cacert_to_use = cacert or self.cacert
                assert cacert_to_use, 'cacert path was not specified'
                cert_flag = f'-cacert {cacert_to_use}'

            grpcurl_cmd = (f"grpcurl {cert_flag} -H username:{username} -H password:{password} "
                           f"{self.server_host}:{self.server_port} {grpcurl_op}")
        with allure.step('run grpcurl command in process'):
            return self._run_cmd_in_process(grpcurl_cmd, cmd_time, keep_session_alive)

    def _verify_gnmic_installed(self):
        cmd = 'gnmic version'
        output = self._run_cmd_in_process(cmd, wait_till_done=True)
        assert GnmicErr.GNMIC_NOT_INSTALLED not in output, f"gnmic is not installed on player.\n{cmd}\n{output}"

    def _verify_grpcurl_installed(self):
        cmd = 'grpcurl -version'
        output = self._run_cmd_in_process(cmd, wait_till_done=True)
        assert GnmicErr.GNMIC_NOT_INSTALLED not in output, f"grpcurl is not installed on player.\n{cmd}\n{output}"

    def _run_cmd_in_process(self, cmd: str, cmd_time=None, keep_process_alive: bool = False,
                            wait_till_done: bool = False) -> Tuple[
            str, str, subprocess.Popen]:
        self._log(f"run: {cmd}")
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   preexec_fn=os.setsid)

        if keep_process_alive:
            self._log(f"keeping process alive and returning it")
            return '', '', process

        if wait_till_done:
            self._log(f"wait till cmd is done and get output")
            out, err = self._get_cmd_process_output(process)
            return out, err, None

        output, err = self.close_session_and_get_out_and_err(process, cmd_time, kill_immediately=False)
        return output, err, None

    def _get_cmd_process_output(self, process: subprocess.Popen):
        output, err = process.communicate()
        output = output.decode('utf-8')
        err = err.decode('utf-8')
        self._log(f"output: {output}")
        self._log(f"err: {err}")
        return output, err

    def _log(self, msg: str):
        logging.info(f"[GnmiClient] {msg}")
