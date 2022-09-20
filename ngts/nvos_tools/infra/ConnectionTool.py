import allure
import logging
from infra.tools.connection_tools.linux_ssh_engine import LinuxSshEngine
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ResultObj import ResultObj

logger = logging.getLogger()


class ConnectionTool:
    @staticmethod
    def create_ssh_conn(ip, username, password):
        """

        :param ip:dut ip
        :param username: username
        :param password: password
        :return:
        """
        with allure.step('create ssh connection with the username {username}'.format(username=username)):
            result_obj = ResultObj(False, "")

            ssh_conn = LinuxSshEngine(ip=ip, username=username, password=password)

            if ConnectionTool.is_connected(ssh_conn).verify_result():
                result_obj.returned_value = ssh_conn
                result_obj.result = True

            return result_obj

    @staticmethod
    def is_connected(engine):
        """
        for me: using  lslogins cmd parser -> running processes label value
        :param engine:
        :return:
        """
        with allure.step('check number of running processes for {username} on {ip}'.format(username=engine.username, ip=engine.ip)):
            running_processes = OutputParsingTool.parse_lslogins_cmd(engine.run_cmd('lslogins {username}'.format(
                username=engine.username))).verify_result()[SystemConsts.PASSWORD_HARDENING_RUNNING_PROCESSES]

            return ResultObj(running_processes, "", "connected to {number}".format(number=running_processes))
