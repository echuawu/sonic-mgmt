#!/usr/bin/env python

# Built-in modules
import sys
import os

# Local modules
from reg2_wrapper.common.error_code import ErrorCode
from reg2_wrapper.utils.parser.cmd_argument import RunningStage
from reg2_wrapper.test_wrapper.standalone_wrapper import StandaloneWrapper

sigterm_h_path = os.path.normpath(os.path.join(os.path.split(__file__)[0], "../sig_term_handler"))
sys.path.append(sigterm_h_path)
from handler_mixin import TermHandlerMixin


class RunPytest(TermHandlerMixin, StandaloneWrapper):

    def configure_parser(self):
        super(RunPytest, self).configure_parser()

        # Client arguments
        self.add_cmd_argument("--setup_name", required=True, dest="setup_name",
                              help="Specify setup name, for example: SONiC_tigris_r-tigris-06")
        self.add_cmd_argument("--test_script", required=True, dest="test_script",
                              help="Path to the test script, example: /workspace/tests/")
        self.add_cmd_argument("--raw_options", nargs="?", default="", dest="raw_options",
                              help="All the other options that to be passed to py.test")

    def run_commands(self):
        rc = ErrorCode.SUCCESS

        allure_project = self.get_allure_project_id()

        cmd = '/ngts_venv/bin/pytest --setup_name={} {} --allure_server_project_id={} {}'.format(self.setup_name, self.raw_options, allure_project, self.test_script)

        # Use random allure_project for CI runs
        if 'CI' in allure_project:
            cmd = '/ngts_venv/bin/pytest --setup_name={} {} {}'.format(self.setup_name, self.raw_options, self.test_script)

        for epoint in self.EPoints:
            dic_args = self._get_dic_args_by_running_stage(RunningStage.RUN)
            dic_args["epoint"] = epoint
            for i in xrange(self.num_of_processes):
                epoint.Player.putenv("PYTHONPATH", "/devts/")
                epoint.Player.run_process(cmd, shell=True, disable_realtime_log=False, delete_files=False)

        for player in self.Players:
            rc = player.wait() or rc
            player.remove_remote_test_path(player.testPath)
        return rc

    def get_allure_project_id(self):
        if self.setup_name.startswith('sonic'):
            dut_name = self.setup_name.split('_')[2]  # Get DUT name in case of setup name starts from "sonic"
        else:
            dut_name = '-'.join(self.setup_name.replace('_', '-'))  # Get DUT name in case of CI setup

        allure_proj = dut_name + self.test_script.replace('/', '-').replace('_', '-').replace('.', '-').strip('-')

        return allure_proj

    def run_post_commands(self):
        self.collect_allure_report_data()

    def collect_allure_report_data(self):
        self.Logger.info('Going to upload allure data to server')

        sonic_mgmt_path = self.test_script.split('ngts')[0]
        cmd = 'PYTHONPATH=/devts /ngts_venv/bin/python {}/ngts/scripts/allure_reporter.py --action upload --setup_name {}'.format(sonic_mgmt_path, self.setup_name)
        self.Logger.info('Running cmd: {}'.format(cmd))
        self.EPoints[0].Player.run_process(cmd, shell=True, disable_realtime_log=False, delete_files=False)

        self.Players[0].wait()
        self.Logger.info('Finished upload allure data to server')


if __name__ == "__main__":
    run_pytest = RunPytest("RunPytest")
    run_pytest.execute(sys.argv[1:])
