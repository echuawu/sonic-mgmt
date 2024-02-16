
import os
import re
from typing import List
from infra.tools.connection_tools.linux_ssh_engine import LinuxSshEngine

DEFAULT_ACCOUNTING_FILE_PATH = '/var/log/tac.acct'


class AaaAccountingLog:
    def __init__(self, log_row: str) -> None:
        try:
            row_split = log_row.split('cmd=')
            self.cmd: str = row_split[1]

            rest_of_row = row_split[0]
            values = re.split(r'\s+|\t+', rest_of_row)

            self.date: str = ' '.join(values[0:2])
            self.time: str = values[2]
            self.client_ip: str = values[3]
            self.username: str = values[4]
            # self.something = values[5]
            self.client_dn: str = values[6]
            self.op_status: str = values[7]  # start/stop
            self.timestamp = values[8]  # start time
            self.task_id = values[9]
            # self.service = values[10]
        except Exception as e:
            raise Exception(f'Log row does not have the expected format.\nError: {e}')


class AaaAccountingLogsFileContent:
    def __init__(self, raw_content: str) -> None:
        self.raw_content = raw_content
        split_rows: List[str] = raw_content.split('\n')
        self.logs: List[AaaAccountingLog] = [AaaAccountingLog(row) for row in split_rows if row != ""]


class AaaServerManager:
    def __init__(self, ip: str, server_docker_name: str = '') -> None:
        self.ip = ip
        self.server_docker_name: str = server_docker_name
        self.server_engine = LinuxSshEngine(ip, os.getenv('VM_USER'), os.getenv('VM_PASSWORD'))

    def __assert_ip(self):
        assert self.ip, 'Tried to make operation with manager of empty ip!'

    def __op_on_accounting_log_file(self, cmd: str) -> str:
        if self.server_docker_name:
            cmd = f'docker exec {self.server_docker_name} {cmd}'

        return self.server_engine.run_cmd(cmd)

    def __show_op_on_accounting_log_file(self, accounting_file_path: str, show_cmd: str, grep: List[str] = None,
                                         after_time: str = '') -> AaaAccountingLogsFileContent:
        cmd = f'{show_cmd} {accounting_file_path}'
        if grep:
            for gr in grep:
                cmd = f'{cmd} | grep -E "{gr}"'
        if after_time:
            # cmd = f"{cmd} | awk '/{after_time}/" + "{p=1}p'"
            awk_cmd = f'awk -v target_time="{after_time}" ' + "'{if ($0 >= target_time || p) {print; p=1}}'"
            cmd = f'{cmd} | {awk_cmd}'

        return AaaAccountingLogsFileContent(self.__op_on_accounting_log_file(cmd))

    def cat_accounting_logs(self, accounting_file_path: str = DEFAULT_ACCOUNTING_FILE_PATH, grep: List[str] = None,
                            after_time: str = '') -> AaaAccountingLogsFileContent:
        self.__assert_ip()
        return self.__show_op_on_accounting_log_file(accounting_file_path, 'cat', grep, after_time)

    def tail_accounting_logs(self, accounting_file_path: str = DEFAULT_ACCOUNTING_FILE_PATH, grep: List[str] = None,
                             after_time: str = '') -> AaaAccountingLogsFileContent:
        self.__assert_ip()
        return self.__show_op_on_accounting_log_file(accounting_file_path, 'tail', grep, after_time)

    def clear_accounting_logs(self, accounting_file_path: str = DEFAULT_ACCOUNTING_FILE_PATH) -> str:
        self.__assert_ip()
        # return self.__op_on_accounting_log_file(accounting_file_path, 'rm -f')  # remove file
        return self.__op_on_accounting_log_file(f'bash -c "echo -n > {accounting_file_path}"')  # clear content
