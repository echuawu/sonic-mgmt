
import os
import re
from typing import List
from infra.tools.connection_tools.linux_ssh_engine import LinuxSshEngine

DEFAULT_ACCOUNTING_FILE_PATH = '/var/log/tac.acct'


class AaaAccountingLog:
    def __init__(self, log_row: str) -> None:
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


class AaaAccountingLogsFileContent:
    def __init__(self, raw_content: str) -> None:
        split_rows: List[str] = raw_content.split('\n')
        self.logs: List[AaaAccountingLog] = [AaaAccountingLog(row) for row in split_rows]


class AaaServerManager:
    def __init__(self, ip: str) -> None:
        self.server_engine = LinuxSshEngine(ip, os.getenv('VM_USER'), os.getenv('VM_PASSWORD'))

    def __show_accounting_log(self, accounting_file_path: str, show_cmd: str, grep: str = '') -> AaaAccountingLogsFileContent:
        cmd = '{op} {file}'.format(op=show_cmd, file=accounting_file_path)
        if grep:
            cmd = f'{cmd} | grep -E "{grep}"'
        output = self.server_engine.run_cmd(cmd)
        return AaaAccountingLogsFileContent(output)

    def cat_accounting_log(self, accounting_file_path: str = DEFAULT_ACCOUNTING_FILE_PATH, grep: str = '') -> AaaAccountingLogsFileContent:
        return self.__show_accounting_log(accounting_file_path, 'cat', grep)

    def tail_accounting_log(self, accounting_file_path: str = DEFAULT_ACCOUNTING_FILE_PATH, grep: str = '') -> AaaAccountingLogsFileContent:
        return self.__show_accounting_log(accounting_file_path, 'tail', grep)
