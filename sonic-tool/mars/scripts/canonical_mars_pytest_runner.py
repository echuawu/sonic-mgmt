#!/usr/bin/env python

# Built-in modules
import sys
import os
import re

from reg2_wrapper.common.error_code import ErrorCode
from reg2_wrapper.utils.parser.cmd_argument import RunningStage
from reg2_wrapper.test_wrapper.standalone_wrapper import StandaloneWrapper

from sig_term_handler.handler_mixin import TermHandlerMixin
from lib.utils import get_allure_project_id
import time

ErrorCode.NO_COLLECTION = 5


class RunPytest(TermHandlerMixin, StandaloneWrapper):

    def configure_parser(self):
        super(RunPytest, self).configure_parser()

        # Client arguments
        self.add_cmd_argument("--setup_name", required=True, dest="setup_name",
                              help="Specify setup name, for example: SONiC_tigris_r-tigris-06")
        self.add_cmd_argument("--sonic-topo", required=False, dest="sonic_topo",
                              help="Topology for SONiC testing, for example: t0, t1, t1-lag, ptf32, etc.")
        self.add_cmd_argument("--test_script", required=True, dest="test_script",
                              help="Path to the test script, example: /workspace/tests/")
        self.add_cmd_argument("--raw_options", nargs="?", default="", dest="raw_options",
                              help="All the other options that to be passed to py.test")
        self.add_cmd_argument("--test_type", required=False, default="", dest="test_type",
                              help="Decide the pytest marker we want to use in the CI test")

    def run_commands(self):
        rc = ErrorCode.SUCCESS

        if self.test_type:
            if self.test_type != "default":
                self.raw_options = re.sub(r" -m \".+\"", "", self.raw_options)
                self.raw_options = re.sub(r" -m \S+", "", self.raw_options)
            if self.test_type == "yaml":
                self.raw_options += " -m yaml"

        allure_project = get_allure_project_id(self.setup_name, self.test_script)
        if self.sonic_topo:
            random_seed = int(time.time())
            cmd_template = '/ngts_venv/bin/pytest --setup_name={} --sonic-topo={} --session_id={} --mars_key_id={} {} ' \
                           '--dynamic_update_skip_reason --allure_server_project_id={} {} --random_seed={} '
            cmd = cmd_template.format(self.setup_name, self.sonic_topo, self.session_id, self.mars_key_id,
                                      self.raw_options, allure_project, self.test_script, random_seed)
        else:
            cmd_template = '/ngts_venv/bin/pytest --setup_name={} --session_id={} --mars_key_id={} {} --dynamic_update_skip_reason --allure_server_project_id={} {}'
            cmd = cmd_template.format(self.setup_name, self.session_id, self.mars_key_id,
                                      self.raw_options, allure_project, self.test_script)

        for epoint in self.EPoints:
            dic_args = self._get_dic_args_by_running_stage(RunningStage.RUN)
            dic_args["epoint"] = epoint
            for i in xrange(self.num_of_processes):
                epoint.Player.putenv("PYTHONPATH", "/devts/")
                epoint.Player.run_process(cmd, shell=True, disable_realtime_log=False, delete_files=False)

        for player in self.Players:
            rc = player.wait() or rc
            player.remove_remote_test_path(player.testPath)
        if rc == ErrorCode.NO_COLLECTION:
            rc = 0  # In case no tests are collected, should not fail mars step
        return rc

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
