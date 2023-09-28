import logging
import pexpect

from infra.tools.general_constants.constants import DefaultConnectionValues


class PexpectTool:
    def __init__(self, spawn_cmd: str = '', default_expect_err_msg: str = 'Expect failed'):
        self.child = None
        self.expect_error_msg = default_expect_err_msg
        if spawn_cmd:
            self.spawn(spawn_cmd)

    def __del__(self):
        self.child.close()

    def spawn(self, cmd):
        logging.info(f'Spawn: {cmd}')
        self.child = pexpect.spawn(cmd)
        self.child.delaybeforesend = DefaultConnectionValues.PEXPECT_DELAYBEFORESEND

    def expect(self, expect_msg, error_message=''):
        err_msg = error_message if error_message else self.expect_error_msg
        if isinstance(expect_msg, list):
            logging.info(f'Expect: {expect_msg}')
            expect_list = expect_msg + [pexpect.EOF]
        else:
            logging.info(f'Expect: "{expect_msg}"')
            expect_list = [expect_msg, pexpect.EOF]

        try:
            res_index = self.child.expect(expect_list)
            logging.info(f'Output:\n{(self.child.before + self.child.after).decode()}')
            assert res_index != len(expect_list) - 1, err_msg
        except pexpect.exceptions.TIMEOUT as timeout_exception:
            logging.info(f'Got pexpect TIMEOUT exception.\n{err_msg}')
            raise timeout_exception

        return res_index

    def send(self, send_str):
        print_to_log = "\\r" if send_str == "\r" else send_str
        logging.info(f'Send: "{print_to_log}"')
        self.child.send(send_str)

    def sendline(self, send_str):
        print_to_log = "\\r" if send_str == "\r" else send_str
        logging.info(f'Send line: "{print_to_log}"')
        self.child.sendline(send_str)
