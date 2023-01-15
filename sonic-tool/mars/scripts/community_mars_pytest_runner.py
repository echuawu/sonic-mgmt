#!/usr/bin/env python

from __future__ import division

# Built-in modules
import json
import os
import sys
import time
import re

# Third-party libs
from xml.etree import ElementTree
from rpyc.utils.classic import connect, download

# Local modules
from reg2_wrapper.common.error_code import ErrorCode
from reg2_wrapper.utils.parser.cmd_argument import RunningStage
from reg2_wrapper.test_wrapper.standalone_wrapper import StandaloneWrapper

from sig_term_handler.handler_mixin import TermHandlerMixin
from lib.utils import get_allure_project_id


class RunPytest(TermHandlerMixin, StandaloneWrapper):

    def configure_parser(self):
        super(RunPytest, self).configure_parser()

        # Client arguments
        self.add_cmd_argument("--sonic-mgmt-dir", required=True, dest="sonic_mgmt_path",
                              help="Specify dir of the sonic-mgmt repo on player (sonic-mgmt container), for example: \
                                    /root/mars/workspace/sonic-mgmt")
        self.add_cmd_argument("--dut-name", required=True, dest="dut_name",
                              help="DUT name, for example: arc-switch1029")
        self.add_cmd_argument("--sonic-topo", required=True, dest="sonic_topo",
                              help="Topology for SONiC testing, for example: t0, t1, t1-lag, ptf32, etc.")
        self.add_cmd_argument("--test-scripts", required=True, dest="test_scripts",
                              help="The pytest scripts to be executed. Multiple scripts should be separated by \
                                    whitespace. Both absolute or relative path are OK.")
        self.add_cmd_argument("--raw-options", nargs="?",default="", dest="raw_options",
                              help="All the other options that to be passed to py.test")
        self.add_cmd_argument("--json-root-dir", required=True, dest="json_root_dir",
                              help="Root directory for storing json metadata")
        self.add_cmd_argument("--is_python3_test", required=False, default=False, dest="is_python3_test",
                              help="True if test case should run from python3, by default False(use python 2.7)")

    def _parse_junit_xml(self, content):

        result = {}
        try:
            junit_report = ElementTree.fromstring(content)
        except Exception as e:
            self.Logger.error("The junit xml report is not a valid XML file. Exception: %s" % repr(e))
            return result

        if junit_report.tag == "testsuites":
            testsuite = junit_report.getchildren()[0]
        else:
            testsuite = junit_report

        try:
            result["failed"] = int(testsuite.attrib["failures"])
            result["skipped"] = int(testsuite.attrib["skipped"])
            result["errors"] = int(testsuite.attrib["errors"])
        except ValueError as e:
            self.Logger.warning("Converting string to int failed while parsing testsuite. Err: %s" % repr(e))
        except KeyError as e:
            self.Logger.warning("Parse jUnit testsuite info failed. Err=%s" % repr(e))

        all_cases = []
        tag_result_map = {"failure": "failed", "skipped": "skipped", "error": "error"}
        try:
            for testcase in testsuite.getchildren():
                if testcase.tag != "testcase":
                    continue
                case_info = {}
                case_info["name"] = "%s::%s" % (testcase.attrib["file"], testcase.attrib["name"])

                case_children = testcase.getchildren()

                for case_child in case_children:
                    if case_child.tag.lower() in tag_result_map:
                        case_info["result"] = tag_result_map[case_child.tag.lower()]
                        break

                if not "result" in case_info:
                    case_info["result"] = "passed"

                all_cases.append(case_info)

        except KeyError as e:
            self.Logger.warning("Parse jUnit testcase info failed. Err=%s" % repr(e))

        self.Logger.info("All cases: %s" % str(json.dumps(all_cases, indent=4)))

        unique_all_cases = set([case["name"] for case in all_cases])
        result["total"] = len(unique_all_cases)

        # A test case could be both "failed" and "error". Use below code to avoid duplicated test case.
        unique_error_failed_cases = set([case["name"] for case in all_cases if case["result"] in ("failed", "error")])

        result["passed"] = result["total"] - len(unique_error_failed_cases) - result["skipped"]
        try:
            result["pass_rate"] = "{:.0%}".format(result["passed"] / (result["total"] - result["skipped"]))
        except ZeroDivisionError:
            result["pass_rate"] = "0%"
            self.Logger.warning("No test case executed")
        result["testcases_error_failed_list"] = " ".join(["<p>%s</p>" % case for case in unique_error_failed_cases])

        return result

    def dump_metadata(self, json_obj):
        if not self.session_id:
            self.Logger.warning("Metadata Data will not be stored due to rerun command")
            return

        if not json_obj:
            self.Logger.warning("No metadata to be stored")

        # Make json dir
        json_dir = os.path.join(self.json_root_dir, self.session_id)
        if not os.path.isdir(json_dir):
            self.Logger.info("Creating directory %s" % json_dir)
            os.mkdir(json_dir, 0755)

        json_metadata = {"id": self.mars_key_id, "json": json_obj}
        dump_filename = os.path.join(json_dir, self.mars_key_id + ".json")

        self.Logger.info("Ready to dump %s:\n%s" % (dump_filename, json.dumps(json_metadata, indent=4)))

        with open(dump_filename, 'w') as outfile:
            json.dump(json_metadata, outfile)

    def run_pre_commands(self):
        """
        @summary: Override the method of base class. Export environment variables required for pytest scripts.
        """
        for player in self.Players:
            # Ansible depends on the $HOME environment variable to determine SSH ControlPath location.
            #     -o 'ControlPath=/root/mars/workspace/sonic-mgmt/ansible/$HOME/.ansible/cp/ansible-ssh-%h-%p-%r'
            # The test wrapper is executed in a context without $HOME environment variable. The workaround is to
            # explicitly define one here:
            player.putenv("HOME", "/root")
            player.putenv("ANSIBLE_CONFIG", os.path.join(self.sonic_mgmt_path, "ansible"))
        return ErrorCode.SUCCESS

    def run_commands(self):
        rc = ErrorCode.SUCCESS

        self.report_file = "junit_%s_%s.xml" % (self.session_id, self.mars_key_id)

        if '--allure_server_project_id' in self.raw_options:
            allure_proj_pytest_arg = ''
        else:
            allure_proj = get_allure_project_id(self.dut_name, self.test_scripts, get_dut_name_only=False)
            allure_proj_pytest_arg = '--allure_server_project_id={}'.format(allure_proj)

        # If the test case contains a topology mark, add --topology parameter to the pytest raw option
        # This is to support topology variations
        sonic_mgmt_path = os.path.abspath(__file__).split('/')[0:-4]
        test_script_path = self.test_scripts.split('::')[0]
        sonic_mgmt_path.extend(['tests', test_script_path])
        test_script_fullpath = '/'.join(sonic_mgmt_path)
        topology_mark_pattern = r'pytest\.mark\.topology\(.+\)'
        try:
            with open(test_script_fullpath) as test_script_file:
                for line in test_script_file:
                    if re.search(topology_mark_pattern, line):
                        if self.sonic_topo:
                            self.convert_topos()
                            self.raw_options += " --topology %s" % self.topology
                        break
        except Exception as e:
            self.Logger.info("Failed to add '--topology' option for test case {}, failure reason: {}".format(test_script_fullpath, repr(e)))

        pytest_bin_name = "py.test"
        if self.is_python3_test:
            pytest_bin_name = "/var/AzDevOps/env-python3/bin/py.test"

        # The test script file must come first, see explaination on https://github.com/Azure/sonic-mgmt/pull/2131
        cmd = "{PYTEST_BIN_NAME} {SCRIPTS} --inventory=\"../ansible/inventory,../ansible/veos\" --host-pattern {DUT_NAME} --module-path \
               ../ansible/library/ --testbed {DUT_NAME}-{SONIC_TOPO} --testbed_file ../ansible/testbed.csv \
               --allow_recover  --session_id {SESSION_ID} --mars_key_id {MARS_KEY_ID} \
               --junit-xml {REPORT_FILE} --assert plain {OPTIONS} {ALLURE_PROJ} --skip_sanity --dynamic_update_skip_reason"
        cmd = cmd.format(PYTEST_BIN_NAME=pytest_bin_name,
                         SCRIPTS=self.test_scripts,
                         DUT_NAME=self.dut_name,
                         SONIC_TOPO=self.sonic_topo,
                         SESSION_ID=self.session_id,
                         MARS_KEY_ID=self.mars_key_id,
                         REPORT_FILE=self.report_file,
                         OPTIONS=self.raw_options,
                         ALLURE_PROJ=allure_proj_pytest_arg)
        # Take the first epoint as just one is specified in *.setup file. Currently supported are: SONIC_MGMT or NGTS
        # Take the first player as just one is specified in *.setup file
        epoint = self.EPoints[0]
        player = self.Players[0]

        self.Logger.info("Starting pytest on sonic-mgmt player")
        dic_args = self._get_dic_args_by_running_stage(RunningStage.RUN)
        dic_args["epoint"] = epoint
        for i in xrange(self.num_of_processes):
            epoint.Player.putenv("PYTHONPATH", "/devts/")
            epoint.Player.testPath = os.path.join(self.sonic_mgmt_path, "tests")
            epoint.Player.add_remote_test_path(epoint.Player.testPath)
            epoint.Player.run_process(cmd, shell=True, disable_realtime_log=False, delete_files=False)
            # Sleep needed to get logs if tests were not executed or even were not collected and exited immediately.
            time.sleep(2)

        rc = player.wait() or rc
        player.remove_remote_test_path(player.testPath)
        return rc

    def run_post_commands(self):
        self.collect_allure_report_data()

        for player in self.Players:
            try:
                self.Logger.info("Connecting to %s" % player.player_ip)
                conn = connect(player.player_ip)
                self.Logger.info("Connected to %s, socket: %s" % (player.player_ip, str(conn)))

                json_dir = os.path.join(self.json_root_dir, self.session_id)
                if not os.path.isdir(json_dir):
                    self.Logger.info("Creating directory %s" % json_dir)
                    os.mkdir(json_dir, 0755)
                local_report_file = os.path.join(json_dir, self.mars_key_id + ".xml")

                self.Logger.info("Downloading %s from player to %s" % (self.report_file, local_report_file))
                download(conn, self.report_file, local_report_file)
                self.Logger.info("Downloaded report to %s" % local_report_file)

                self.dump_metadata(self._parse_junit_xml(open(local_report_file).read()))
            except Exception, e:
                self.Logger.error(repr(e))
                self.Logger.warning("Failed to get junit xml test report %s from remote player" % self.report_file)
        return ErrorCode.SUCCESS

    def convert_topos(self):
        # Convert the topology name to topology type(for example, t0-64 to t0)
        # and append type "any" for 'any' type in the topology mark
        testbed_type_index = 0
        topos = [self.sonic_topo.split('-')[testbed_type_index]]
        topos.append("any")
        topos.append("util")  # this is only for test_pretest and test_nbr_health
        self.topology = ",".join(topos)

    def collect_allure_report_data(self):
        self.Logger.info('Going to upload allure data to server')

        cmd = 'PYTHONPATH=/devts /ngts_venv/bin/python {}/ngts/scripts/allure_reporter.py --action upload --setup_name {}'.format(self.sonic_mgmt_path, self.dut_name)
        self.Logger.info('Running cmd: {}'.format(cmd))
        self.EPoints[0].Player.run_process(cmd, shell=True, disable_realtime_log=False, delete_files=False)

        self.Players[0].wait()
        self.Logger.info('Finished upload allure data to server')


if __name__ == "__main__":
    run_pytest = RunPytest("RunPytest")
    run_pytest.execute(sys.argv[1:])
