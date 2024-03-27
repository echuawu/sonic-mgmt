#!/usr/bin/env python
import logging
import os
import re
import datetime
import argparse
import subprocess
import shutil
import sys
import json
import traceback
import pandas as pd
import xml.etree.ElementTree as ET
from ngts.helpers.general_helper import get_all_setups, get_all_setups_platform
from ngts.constants.constants import DbConstants, InfraConst, ResultUploaderConst, \
    MarsConstants, SonicConst, LinuxConsts
from infra.tools.connection_tools.linux_ssh_engine import LinuxSshEngine
from infra.tools.redmine.redmine_api import get_issue_development_items
from ngts.scripts.upload_regression_results_to_msft.oracle_db import OracleDb

logger = logging.getLogger()

stm_user = os.getenv("STM_USER")
stm_password = os.getenv("STM_PASSWORD")
sonic_mgmt_user = os.getenv("SONIC_MGMT_USER")
sonic_mgmt_password = os.getenv("SONIC_MGMT_PASSWORD")


def validate_env_variables():
    assert all([stm_user, stm_password, sonic_mgmt_user, sonic_mgmt_password]), \
        f"One or more environment variables was not located," \
        f"STM_USER: {stm_user}, STM_PASSWORD: {stm_password}, " \
        f"SONIC_MGMT_USER: {sonic_mgmt_user}, SONIC_MGMT_PASSWORD: {sonic_mgmt_password}"


def init_parser():
    description = ('Functionality of the script: \n'
                   'Use case #1: create an excel to review regression results for a given image.\n'
                   'Use case #2: Modify results - '
                   '             2.1: Update Redmine issues in skips to community issues/user message.\n'
                   '             2.1: Remove testcases from xml per user request.\n'
                   'Use case #3: Compare the results to MSFT/MARS database.\n'
                   'Use case #4: Save sessions to MARS database.\n'
                   'Use case #5: Upload the results to MSFT database and save them based on an approved excel.\n')
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('--sonic_version', dest='sonic_version',
                        help='sonic image version, i.e, '
                             '202305_RC.57-a21ec72e5_Internal', required=True)
    parser.add_argument('-l', '--log_level', dest='log_level', default=logging.INFO, help='log verbosity')

    subparsers = parser.add_subparsers(help='help for subcommand', dest="subcommand")

    parser_collect_results = subparsers.add_parser('collect', help='arguments for collecting results')
    parser_modify_results = subparsers.add_parser('modify', help='arguments for modifying results')
    parser_export_results = subparsers.add_parser('export', help='arguments for exporting results for MSFT database')
    parser_compare_results = subparsers.add_parser('compare', help='arguments for comparing results to MSFT database')
    parser_save_results = subparsers.add_parser('save', help='arguments for save sessions to MARS database')
    parser_concat_results = subparsers.add_parser('concat', help='arguments for concating several '
                                                                 'excel tables into 1 table')

    # COLLECT ARGUMENTS
    group = parser_collect_results.add_mutually_exclusive_group(required=True)

    group.add_argument('--last_days', dest='last_days',
                       help='Collect sessions for image from the last X days')

    group.add_argument('--user_sessions', dest='user_sessions', default=[], nargs='+',
                       help='sessions manually provided by user, i.e, 8354462 2998422.. ')

    parser_collect_results.add_argument('--filter_platforms', dest='platform_list',
                                        default=ResultUploaderConst.MSFT_PLATFORMS, nargs='+')
    parser_collect_results.add_argument('--filter_sessions_started_by', dest='sessions_started_by_regexes',
                                        default=ResultUploaderConst.SESSION_STARTED_BY_REGEX, nargs='+')
    # MODIFY ARGUMENTS
    parser_modify_results.add_argument('--user_excel_table_path', dest='user_excel_table_path',
                                       help='Path to excel table file that should be modified')
    parser_modify_results.add_argument('--redmine_issues_to_update', dest='redmine_issues_to_update',
                                       default="{}", help='Specify redmine issues that should '
                                       'be updated to some other message in JSON format.'
                                       'JSON format should be {redmine_issue_url: message_text}'
                                       'i.e. {"https://redmine.mellanox.com/issues/3651153": '
                                       '"test issue for nvidia platform, work in progress", ...}')
    # EXPORT ARGUMENTS
    parser_export_results.add_argument('--export_excel', dest='export_excel_path',
                                       help='Path to excel table file that should be exported to MSFT.',
                                       required=True)
    parser_export_results.add_argument('--sonic_mgmt_ip', dest='sonic_mgmt_ip', default="",
                                       help='sonic mgmt container ip, e.g. 10.210.25.102')

    # COMPARE ARGUMENTS
    parser_compare_results.add_argument('--compare_excel', dest='compare_excel_path',
                                        help='Path to excel table file that should be compared to MSFT database.',
                                        required=True)
    parser_compare_results.add_argument('--msft_results_path', dest='msft_results_path',
                                        help='Path to a directory containing results from MSFT database.',
                                        required=True)
    # SAVE ARGUMENTS
    parser_save_results.add_argument('--sessions_to_save', dest='sessions_to_save', default=[], nargs='+',
                                     help='sessions manually provided by user, i.e, 8354462 2998422.. ')

    # CONCAT ARGUMENTS
    parser_concat_results.add_argument('--excel_tables', dest='excel_tables', default=[], nargs='+',
                                       help='excel tables manually provided by user, i.e, path1 path2 .. ')

    arguments, unknown = parser.parse_known_args()

    if unknown:
        raise Exception("unknown argument(s): {}".format(unknown))
    return arguments


def set_logger(log_level):
    logging.basicConfig(level=log_level,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M')


class ReleaseResultsUploader:

    def __init__(self, arguments):
        self.command = arguments.subcommand
        self.script_running_date = datetime.datetime.now().strftime('%y-%m-%d_%a_%H:%M:%S')
        self.sonic_version = arguments.sonic_version
        self.sonic_version_release_results_dir, self.updated_files_dir = self.make_release_results_dir()
        self.excel_table_name = f"{self.script_running_date}_{self.sonic_version}.xlsx"
        self.excel_table_path = os.path.join(self.sonic_version_release_results_dir,
                                             f"collected_results_{self.excel_table_name}")
        self.tmp_sonic_mgmt_git_dir = "/tmp/sonic-mgmt-get-new-tests"
        if self.command == "collect":
            self.last_days = arguments.last_days
            self.user_sessions = arguments.user_sessions
            self.platform_list = arguments.platform_list
            self.started_by_regexes = arguments.sessions_started_by_regexes
            self.git_path = self.clone_sonic_mgmt_public_repo()
            self.all_setups = get_all_setups()
            self.all_setups_platforms = get_all_setups_platform()
        elif self.command == "modify":
            self.user_excel_table_path = arguments.user_excel_table_path
            self.redmine_issues_to_update = json.loads(arguments.redmine_issues_to_update)
            self.user_modified_excel_table_path = os.path.join(self.sonic_version_release_results_dir,
                                                               f"user_modified_{self.excel_table_name}")
        elif self.command == "export":
            self.sonic_mgmt_ip = arguments.sonic_mgmt_ip
            self.export_excel_table_path = arguments.export_excel_path
            self.exported_results_excel_table_path = os.path.join(self.sonic_version_release_results_dir,
                                                                  f'exported_results_{self.excel_table_name}')
            self.result_folder = os.path.join(DbConstants.METADATA_PATH,
                                              f"{self.sonic_version}_results",
                                              f"results_exported_{self.script_running_date}")
        elif self.command == "compare":
            self.compare_excel_table_path = arguments.compare_excel_path
            self.msft_results_path = arguments.msft_results_path
            self.compare_results_excel_table_path = os.path.join(self.sonic_version_release_results_dir,
                                                                 f'compare_msft_{self.excel_table_name}')
            self.msft_topo_hwsku_results_set = set()
        elif self.command == "save":
            self.sessions_to_save = arguments.sessions_to_save
        elif self.command == "concat":
            self.excel_tables = arguments.excel_tables
            self.concated_results_excel_table_path = os.path.join(self.sonic_version_release_results_dir,
                                                                  f'concated_results_{self.excel_table_name}')

        self.sheet_name = "community_tests"
        self.branch = self.get_branch_from_sonic_version()
        self.redmine_bugs = set()
        self.community_issues_redmine_bugs = dict()
        self.nvidia_community_tests = set()
        self.hosts = set()
        self.sessions_testbed_properties = dict()
        self.modified_xml_path = dict()
        file_dir_path = os.path.dirname(os.path.realpath(__file__))
        self.build_mail_table = os.path.join(file_dir_path, "build_mail_table.txt")
        if os.path.exists(self.build_mail_table):
            os.remove(self.build_mail_table)

    def make_release_results_dir(self):
        sonic_version_release_results_dir = os.path.join(InfraConst.RELEASE_RESULTS_DIR,
                                                         self.sonic_version)
        access = 0o777
        if not os.path.exists(sonic_version_release_results_dir):
            os.mkdir(sonic_version_release_results_dir)
            os.chmod(sonic_version_release_results_dir, access)
        updated_files_dir = os.path.join(sonic_version_release_results_dir, "updated_junit_xml_files")
        if not os.path.exists(updated_files_dir):
            os.mkdir(updated_files_dir)
            os.chmod(updated_files_dir, access)
        return sonic_version_release_results_dir, updated_files_dir

    def get_branch_from_sonic_version(self):
        return re.search(r"(\d{6}).*", self.sonic_version).group(1)

    def clone_sonic_mgmt_public_repo(self):
        if os.path.exists(self.tmp_sonic_mgmt_git_dir):
            shutil.rmtree(self.tmp_sonic_mgmt_git_dir, ignore_errors=True)
        os.mkdir(self.tmp_sonic_mgmt_git_dir)
        cmd = "git clone https://github.com/sonic-net/sonic-mgmt.git".split()
        p = subprocess.Popen(cmd, cwd=self.tmp_sonic_mgmt_git_dir)
        p.wait(timeout=180)
        return os.path.join(self.tmp_sonic_mgmt_git_dir, "sonic-mgmt")

    def exec_command_on_regression_results_to_msft(self):
        """
        Functionality of the script:
        Use case #1: create an excel to review regression results for a given image.
        Use case #2: Modify results -
                2.1: Update Redmine issues in skips to community issues/user message
                2.1: Remove test cases from xml per user request
         Use case #3: Upload the results to MSFT database and save them based on an approved excel.
        :return: raise assertion error in case of script failure
        """
        try:
            if self.command == "collect":
                self.collect_results()
            elif self.command == "modify":
                self.modify_results()
            elif self.command == "export":
                self.upload_user_approved_results()
            elif self.command == "compare":
                self.compare_results()
            elif self.command == "save":
                self.save_sessions_for_image(sessions_ids=self.sessions_to_save)
            elif self.command == "concat":
                self.concat_results()

        finally:
            if os.path.exists(self.tmp_sonic_mgmt_git_dir):
                shutil.rmtree(self.tmp_sonic_mgmt_git_dir, ignore_errors=True)

    def collect_results(self):
        logger.info(f"Start collecting results for {self.sonic_version} | {self.branch}")
        sessions = self.user_sessions if self.user_sessions else self.query_sessions_for_image()
        logger.info(f'Session are: {sessions}')
        self.update_sessions_testbed_properties(sessions)
        platform_filtered_sessions = self.filter_sessions(sessions)
        logger.info(f'Platform filtered Sessions are: {platform_filtered_sessions}')
        self.create_excel_table(platform_filtered_sessions)
        logger.info(f'Collected excel results table is at : {self.excel_table_path}')
        setups_in_results = self.get_setups_from_results(self.all_setups)
        setups_not_in_results = set(self.all_setups).difference(setups_in_results)
        filter_setups_not_in_results = self.filter_setups(setups_not_in_results)
        self.compose_collect_results_mail(setups_in_results, filter_setups_not_in_results)

    def modify_results(self):
        df = pd.read_excel(self.user_excel_table_path, sheet_name=self.sheet_name, index_col=0)
        row_idx_to_remove = []
        host_commercial_name_col = []
        for i in range(len(df)):
            self.update_xml_path_if_modified(df, i)
            session_id = df.loc[i, "session_id"]
            result = df.loc[i, "result"]
            message = df.loc[i, "message"]
            junit_xml_path = df.loc[i, "xml_path"]
            modify_xml = df.loc[i, "modify_xml"]
            test_name = df.loc[i, "test name"]
            old_hostname = df.loc[i, "host"]
            platform = df.loc[i, "platform"]
            new_hostname = self.get_new_hostname(old_hostname, platform)
            df.loc[i, "test name"] = test_name.replace(old_hostname, new_hostname)
            test_name = df.loc[i, "test name"]
            df.loc[i, "testbed"] = df.loc[i, "testbed"].replace(old_hostname, new_hostname)
            host_commercial_name_col.append(new_hostname)
            junit_xml_path = self.handle_sanitize_data(df, i, junit_xml_path, session_id,
                                                       old_hostname, new_hostname, test_name, result)
            junit_xml_path = self.handle_redmine_url_update(df, i, junit_xml_path, session_id, result, message)
            self.handle_remove_failures(row_idx_to_remove, i, session_id, junit_xml_path, test_name, modify_xml)
            self.update_xml_path_if_modified(df, i)
        self.handle_update_of_modified_xml_path(df)
        new_host_col = pd.DataFrame({'host': host_commercial_name_col})
        if row_idx_to_remove:
            logger.info(f"The following rows are dropped from results per user request: {row_idx_to_remove}")
            df = df.drop(row_idx_to_remove)
            new_host_col = new_host_col.drop(row_idx_to_remove)
            df.reset_index(drop=True, inplace=True)
        df.update(new_host_col)
        df.to_excel(self.user_modified_excel_table_path, sheet_name=self.sheet_name)
        logger.info(f'Modified excel results table is at : {self.user_modified_excel_table_path}')
        self.compose_modify_results_mail(self.user_modified_excel_table_path)

    def get_new_hostname(self, old_hostname, platform):
        new_hostname = old_hostname
        internal_name = self.get_internal_name(old_hostname)
        if internal_name:
            commercial_name = re.search(r"x86_64-\w*_(\w+\d{4}\w*)-.*", platform).group(1)
            new_hostname = old_hostname.replace(internal_name, commercial_name)
        return new_hostname

    @staticmethod
    def get_internal_name(old_hostname):
        for internal_name in ResultUploaderConst.HOST_INTERNAL_NAMES_LIST:
            if re.search(internal_name, old_hostname):
                return internal_name
        return None

    def handle_update_of_modified_xml_path(self, df):
        for i in range(len(df)):
            self.update_xml_path_if_modified(df, i)

    def update_xml_path_if_modified(self, df, row_idx):
        junit_xml_path = df.loc[row_idx, "xml_path"]
        if junit_xml_path in self.modified_xml_path.keys():
            junit_xml_path = self.modified_xml_path[junit_xml_path]
            df.loc[row_idx, "xml_path"] = junit_xml_path
            df.loc[row_idx, "was_xml_updated"] = True

    def handle_redmine_url_update(self, df, row_idx, junit_xml_path, session_id, result, message):
        updated_junit_xml_path, redmine_issue, updated_info = self.update_redmine_url(junit_xml_path,
                                                                                      session_id,
                                                                                      result, message)
        if updated_junit_xml_path:
            df.loc[row_idx, "xml_path"] = updated_junit_xml_path
            df.loc[row_idx, "was_xml_updated"] = True
            if redmine_issue and updated_info:
                updated_message = message.replace(redmine_issue, updated_info)
                df.loc[row_idx, "message"] = updated_message
            return updated_junit_xml_path
        return junit_xml_path

    def update_redmine_url(self, junit_xml_path, session_id, result, message):
        updated_junit_xml_path, redmine_issue, updated_info = None, None, None
        redmine_issue, community_issue_url = self.review_result(result, message)
        if redmine_issue and community_issue_url:
            updated_junit_xml_path = self.update_redmine_issue_in_xml(junit_xml_path, session_id,
                                                                      redmine_issue, community_issue_url)
            updated_info = community_issue_url
        elif redmine_issue in self.redmine_issues_to_update.keys():
            updated_info = self.redmine_issues_to_update[redmine_issue]
            updated_junit_xml_path = self.update_redmine_issue_in_xml(junit_xml_path, session_id,
                                                                      redmine_issue,
                                                                      updated_info)
        return updated_junit_xml_path, redmine_issue, updated_info

    def review_result(self, result, message):
        redmine_issue = None
        community_issue_url = None
        if result == "skipped":
            redmine_issue = re.search(r"https:\/\/redmine\.mellanox\.com\/issues\/(\d+)", str(message))
            if redmine_issue:
                redmine_id = redmine_issue.group(1)
                redmine_issue = redmine_issue.group()
                if self.community_issues_redmine_bugs.get(redmine_issue):
                    community_issue_url = self.community_issues_redmine_bugs[redmine_issue]
                else:
                    community_issue_url = self.get_redmine_community_issue(redmine_id)
                    if community_issue_url:
                        self.community_issues_redmine_bugs[redmine_issue] = community_issue_url
                if not community_issue_url:
                    self.redmine_bugs.add(redmine_issue)
        return redmine_issue, community_issue_url

    @staticmethod
    def get_redmine_community_issue(redmine_id):
        community_issue_url = None
        development_items = get_issue_development_items(redmine_id)
        if development_items:
            for development_item in development_items:
                url = development_item['url']
                if 'github.com' in url and 'issues' in url:
                    community_issue_url = url
        return community_issue_url

    def update_redmine_issue_in_xml(self, junit_xml_path, session, redmine_issue, updated_info):
        with open(junit_xml_path) as f:
            contents = f.read()
            updated_contents = contents.replace(redmine_issue, updated_info)
        updated_junit_xml_path = self.get_updated_junit_xml_path(junit_xml_path, session)
        with open(updated_junit_xml_path, 'w+') as updated_junit_xml:
            updated_junit_xml.write(updated_contents)
        os.chmod(updated_junit_xml_path, 0o777)
        logger.debug(f"Update: {redmine_issue} to {updated_info}")
        logger.debug(f"Create: new updated xml at {updated_junit_xml_path}")
        return updated_junit_xml_path

    def get_updated_junit_xml_path(self, junit_xml_path, session, delete_updated=True):
        filename = os.path.basename(junit_xml_path)
        if filename.endswith(".updated"):
            updated_junit_xml_path = junit_xml_path
            if delete_updated:
                os.remove(updated_junit_xml_path)
        else:
            updated_junit_xml_path = os.path.join(self.updated_files_dir, f"{session}_{filename}.updated")
            self.modified_xml_path[junit_xml_path] = updated_junit_xml_path
        return updated_junit_xml_path

    def handle_remove_failures(self, row_idx_to_remove, row_idx, session_id, junit_xml_path, test_name, modify_xml):
        updated_junit_xml_path = self.remove_failures(session_id, junit_xml_path, test_name, modify_xml)
        if updated_junit_xml_path:
            row_idx_to_remove.append(row_idx)

    def remove_failures(self, session, junit_xml_path, test_name_to_remove, modify_xml):
        updated_junit_xml_path = None
        if modify_xml == ResultUploaderConst.REMOVE_FAILED_TESTCASE:
            mytree = ET.parse(junit_xml_path)
            myroot = mytree.getroot()
            for idx, testsuite in enumerate(myroot.findall('testsuite')):
                for testcase in testsuite.findall('testcase'):
                    classname_path = self.parse_classname(testcase.attrib['classname'])
                    test_name = f"{classname_path}::{testcase.attrib['name']}"
                    if test_name == test_name_to_remove:
                        testsuite.remove(testcase)
            updated_junit_xml_path = self.get_updated_junit_xml_path(junit_xml_path, session)
            mytree.write(updated_junit_xml_path)
            logger.info(f"Remove: {test_name_to_remove} from {junit_xml_path}")
            logger.info(f"Create: new updated xml at {updated_junit_xml_path}")
        return updated_junit_xml_path

    def handle_sanitize_data(self, df, row_idx, junit_xml_path, session,
                             old_hostname, new_hostname, test_name_to_update, result):
        junit_xml_path = self.handle_sanitize_hostname_data(junit_xml_path, session, old_hostname, new_hostname)
        junit_xml_path = self.handle_sanitize_error_message(df, row_idx, session, junit_xml_path,
                                                            test_name_to_update, result)
        return junit_xml_path

    def handle_sanitize_hostname_data(self, junit_xml_path, session, old_hostname, new_hostname):
        updated_junit_xml_path = junit_xml_path
        if new_hostname != old_hostname:
            with open(junit_xml_path) as f:
                contents = f.read()
                updated_contents = contents.replace(old_hostname, new_hostname)
            updated_junit_xml_path = self.get_updated_junit_xml_path(junit_xml_path, session, delete_updated=False)
            if updated_junit_xml_path != junit_xml_path:
                with open(updated_junit_xml_path, 'w+') as updated_junit_xml:
                    updated_junit_xml.write(updated_contents)
                os.chmod(updated_junit_xml_path, 0o777)
                logger.debug(f"Update: {old_hostname} to {new_hostname}")
                logger.debug(f"Create: new updated xml at {updated_junit_xml_path}")
        return updated_junit_xml_path

    def handle_sanitize_error_message(self, df, row_idx, session, junit_xml_path, test_name_to_update, result):
        updated_junit_xml_path = junit_xml_path
        if result == 'fail':
            mytree = ET.parse(junit_xml_path)
            myroot = mytree.getroot()
            for idx, testsuite in enumerate(myroot.findall('testsuite')):
                for testcase in testsuite.findall('testcase'):
                    classname_path = self.parse_classname(testcase.attrib['classname'])
                    test_name = f"{classname_path}::{testcase.attrib['name']}"
                    if test_name == test_name_to_update:
                        error = testcase.findall('error')
                        if error:
                            error[0].attrib['message'] = 'error logs were found during the test run'
                            df.loc[row_idx, "message"] = error[0].attrib['message']
                        break
            updated_junit_xml_path = self.get_updated_junit_xml_path(junit_xml_path, session)
            mytree.write(updated_junit_xml_path)
            logger.debug(f"Updated: {test_name_to_update} message")
            logger.debug(f"Create: new updated xml at {updated_junit_xml_path}")
        return updated_junit_xml_path

    def upload_user_approved_results(self):
        self.copy_xml_results_to_result_folder()
        self.create_final_results_table()
        assert not self.redmine_bugs, f"The following Redmine issues were found in results: {self.redmine_bugs}, " \
                                      f"export is aborted"
        # self.export_results()
        sessions_ids = list(self.sessions_testbed_properties.keys())
        # self.save_sessions_for_image(sessions_ids)
        self.compose_export_results_mail(self.exported_results_excel_table_path)

    def compare_results(self):
        missing_from_junit_df, missing_from_pbi_df = self.compare_results_to_pbi_report()
        msft_df, nvda_df, missing_tests_df = self.compare_results_to_msft()
        with pd.ExcelWriter(self.compare_results_excel_table_path) as writer:
            msft_df.to_excel(writer, sheet_name="msft_results")
            nvda_df.to_excel(writer, sheet_name="nvda_results")
            missing_tests_df.to_excel(writer, sheet_name="msft_missing_results")
            missing_from_junit_df.to_excel(writer, sheet_name="junit_missing_results")
            missing_from_pbi_df.to_excel(writer, sheet_name="pbi_missing_results")
        self.compose_compare_results_mail()

    def concat_results(self):
        frames = []
        for path in self.excel_tables:
            df = pd.read_excel(path, sheet_name=self.sheet_name, index_col=0)
            frames.append(df)
        result = pd.concat(frames)
        result.reset_index(drop=True, inplace=True)
        result.to_excel(self.concated_results_excel_table_path, sheet_name=self.sheet_name)
        self.compose_concat_results_mail()

    def compare_results_to_pbi_report(self):
        df = pd.read_excel(self.compare_excel_table_path, sheet_name=self.sheet_name, index_col=0)
        sessions_ids_as_int = set(df["session_id"].tolist())
        sessions_ids_as_str = [f"\'{sessions_id}\'" for sessions_id in sessions_ids_as_int]
        sessions = ','.join(sessions_ids_as_str)
        community_dbs = ','.join(self.get_community_dbs_list())
        query = f"SELECT session_id, local_key_id, database_name, test_name, case_name, case_result, case_url " \
                f"FROM NBU_ENG_WH.MARS_SONIC_CASES_RESULTS " \
                f"WHERE session_id IN ({sessions}) AND " \
                f"((database_name = \'pretest.db\' AND case_name = \'pretest\') OR " \
                f"database_name IN ({community_dbs}))"
        mars_cases_df = OracleDb().select_into_df(query)
        mars_local_key_ids = set(mars_cases_df["LOCAL_KEY_ID"].tolist())
        junit_xml_local_key_ids = set(df["mars_key_id"].tolist())
        missing_from_junit = mars_local_key_ids.difference(junit_xml_local_key_ids)
        missing_from_pbi = junit_xml_local_key_ids.difference(mars_local_key_ids)
        missing_from_junit_df = mars_cases_df[mars_cases_df["LOCAL_KEY_ID"].isin(missing_from_junit)]
        missing_from_pbi_df = df[df["mars_key_id"].isin(missing_from_pbi)]
        return missing_from_junit_df, missing_from_pbi_df

    @staticmethod
    def get_community_dbs_list():
        path = os.path.abspath(__file__)
        sonic_mgmt_path = path.split('/ngts/')[0]
        community_dbs_dir = os.path.join(sonic_mgmt_path, ResultUploaderConst.COMMUNITY_DBS_RELATIVE_PATH)
        community_dbs_names = [db for db in os.walk(community_dbs_dir)][0][2]
        community_dbs_names.remove("pretest.db")
        community_dbs_names = [f"\'{db_name}\'" for db_name in community_dbs_names]
        return community_dbs_names

    def compare_results_to_msft(self):
        msft_df = self.parse_msft_xmls()
        nvda_df = pd.read_excel(self.compare_excel_table_path, sheet_name=self.sheet_name, index_col=0)
        missing_tests_df = self.find_missing_tests(msft_df, nvda_df)
        return msft_df, nvda_df, missing_tests_df

    def parse_msft_xmls(self):
        worksheet_content = []
        for root, dirs, files in os.walk(self.msft_results_path):
            for filename in files:
                if filename.endswith(".xml"):
                    junit_xml_path = os.path.join(root, filename)
                    worksheet_content += self.get_parsed_msft_junit_file(junit_xml_path)
        df = pd.DataFrame(worksheet_content, columns=ResultUploaderConst.MSFT_XLSX_HEADER)
        return df

    def find_missing_tests(self, msft_df, nvda_df):
        sanitized_testcases_list = msft_df["sanitized_testname"].tolist()
        sanitized_testcases = [sanitized_testcase for sanitized_testcase in
                               sanitized_testcases_list if sanitized_testcase]
        msft_sanitized_testcases = set(sanitized_testcases)
        nvda_sanitized_testcases = set(nvda_df["sanitized_testname"].tolist())
        diff = msft_sanitized_testcases.difference(nvda_sanitized_testcases)
        missing_testcases_content = {"missing_testcases": list(diff)}
        missing_testcases_df = pd.DataFrame(missing_testcases_content)
        return missing_testcases_df

    def query_sessions_for_image(self):
        """
        :return: None
        """
        stm_engine = LinuxSshEngine(ip=InfraConst.STM_IP, username=stm_user, password=stm_password)
        sessions_list = []
        for group in SonicConst.SONIC_NOGA_GROUPS:
            logger.info(f"Query sessions for {group}")

            remote_cmd = f"python {ResultUploaderConst.QUERY_SESSIONS_SCRIPT}" \
                         f" --action query --description query_sessions " \
                         f"--lts_info version:SONiC.{self.sonic_version}" \
                         f" --group {group} --last_days {self.last_days}"

            logger.info("CMD: %s" % remote_cmd)
            output = stm_engine.run_cmd(remote_cmd, validate=False)
            sessions_started_by_tuple_list = \
                re.findall(r"Session: (\d+)\s+Status:\w+\s+StartedBy:(.*)\s+Active state:.*", output)
            for session, started_by in sessions_started_by_tuple_list:
                if any([re.search(regex, started_by) for regex in self.started_by_regexes]):
                    sessions_list.append(session)
        assert sessions_list, f"No sessions were collected for {self.sonic_version} " \
                              f"in the last {self.last_days} days with " \
                              f"started_by regex which match {self.started_by_regexes}"
        return sessions_list

    def update_sessions_testbed_properties(self, sessions):
        session_without_properties = []
        for session in sessions:
            self.update_session_testbed_properties(session)
            if not self.sessions_testbed_properties.get(session):
                session_without_properties.append(session)
        sessions_with_properties = " ".join(list(self.sessions_testbed_properties.keys()))
        assert not session_without_properties, \
            f"Didn't find session properties for sessions: {session_without_properties},\n" \
            f"session properties were found only for:\n{sessions_with_properties}\n" \
            f"please verify manually session status"

    def update_session_testbed_properties(self, session_id):
        """
        Function review metadata collected for the session, in case it founds an xml file which has session
        properties, such as topology, platform, hwsku, etc.. it returns the session properties.

        session properties will be the same all through out the session so only need to find them once.
        session could not have session properties found in cases
        of session terminated with no tests run/ all tests in session are skipped
        (in that case the xml does not contain the session properties).
        :param session_id: i.e, 8254248
        :return: None, update session properties in dict if found
        """
        session_metadata = os.path.join(DbConstants.METADATA_PATH, session_id)
        for root, dirs, files in os.walk(session_metadata):
            for filename in files:
                if filename.endswith(".xml"):
                    junit_xml_path = os.path.join(root, filename)
                    testbed_properties = self.get_junit_testbed_properties(junit_xml_path)
                    testbed = testbed_properties.get('testbed', "")
                    topology = testbed_properties.get('topology', "")
                    host = testbed_properties.get('host', "")
                    asic = testbed_properties.get('asic', "")
                    platform = testbed_properties.get('platform', "")
                    hwsku = testbed_properties.get('hwsku', "")
                    os_version = testbed_properties.get('os_version', "")
                    if testbed and topology and host and asic and platform and hwsku and os_version:
                        self.sessions_testbed_properties[session_id] = testbed_properties
                        break

    @staticmethod
    def get_junit_testbed_properties(junit_xml_path):
        mytree = ET.parse(junit_xml_path)
        myroot = mytree.getroot()
        testbed_properties = {}
        for idx, testsuite in enumerate(myroot.findall('testsuite')):
            assert idx == 0, 'Assumption is that there is only 1 testsuite in XML, please review file content'
            if testsuite.findall('properties'):
                properties = testsuite.findall('properties')[0]
                for testsuite_property in properties:
                    testbed_properties[testsuite_property.attrib['name']] = testsuite_property.attrib['value']
        return testbed_properties

    def filter_sessions(self, sessions):
        filtered_sessions = []
        for session in sessions:
            session_hwsku = self.sessions_testbed_properties[session]['hwsku']
            if any([platform in session_hwsku for platform in self.platform_list]):
                filtered_sessions.append(session)
                self.hosts.add(self.sessions_testbed_properties[session]['host'])
        assert filtered_sessions, f"No sessions remained after applying platform filter for: {self.platform_list}"
        return filtered_sessions

    def create_excel_table(self, sessions):
        worksheet_content = []
        for session in sessions:
            session_metadata = os.path.join(DbConstants.METADATA_PATH, session)
            for root, dirs, files in os.walk(session_metadata):
                for filename in files:
                    if filename.endswith(".xml"):
                        junit_xml_path = os.path.join(root, filename)
                        worksheet_content += self.get_parsed_community_junit_file(junit_xml_path, session)
        df = pd.DataFrame(worksheet_content, columns=ResultUploaderConst.XLSX_HEADER)
        df.to_excel(self.excel_table_path, sheet_name=self.sheet_name)

    @staticmethod
    def update_worksheet_header(worksheet):
        row = 0
        for col_idx, header_item in enumerate(ResultUploaderConst.XLSX_HEADER):
            worksheet.write(row, col_idx, header_item)

    def get_parsed_community_junit_file(self, junit_xml_path, session):
        excel_rows = self.parse_junit_file(session, junit_xml_path)
        if excel_rows:
            testcase_name = excel_rows[0][ResultUploaderConst.XLSX_HEADER.index("test name")]
            full_test_path = self.get_full_test_path(testcase_name)
            test_exist_in_remote = self.is_test_exist_in_remote(full_test_path)
            if not test_exist_in_remote:
                self.nvidia_community_tests.add(full_test_path)
                return []
        return excel_rows

    def get_parsed_msft_junit_file(self, junit_xml_path):
        mytree = ET.parse(junit_xml_path)
        myroot = mytree.getroot()
        excel_rows = []
        for idx, testsuite in enumerate(myroot.findall('testsuite')):
            assert idx == 0, 'Assumption is that there is only 1 testsuite in XML, please review file content'
            testbed_properties = self.parse_testbed_properties(testsuite)
            for testcase in testsuite.findall('testcase'):
                excel_row_content = []
                testcase_properties = self.parse_testcase_properties(testcase)
                hostname = testbed_properties.get('host', "")
                excel_row_content.append(testbed_properties.get('testbed', ""))
                excel_row_content.append(testcase_properties['test_name'])
                excel_row_content.append(testcase_properties.get('start', ""))
                excel_row_content.append(testcase_properties.get('end', ""))
                excel_row_content.append(testcase_properties['result'])
                excel_row_content.append(testcase_properties['message'])
                excel_row_content.append(testbed_properties.get('topology', ""))
                excel_row_content.append(hostname)
                excel_row_content.append(testbed_properties.get('asic', ""))
                excel_row_content.append(testbed_properties.get('platform', ""))
                excel_row_content.append(testbed_properties.get('hwsku', ""))
                excel_row_content.append(testbed_properties.get('os_version', ""))
                excel_row_content.append(junit_xml_path)
                sanitized_testname = ""
                if hostname:
                    sanitized_testname = \
                        testcase_properties['test_name'].replace(hostname, ResultUploaderConst.SANITIZED_HOSTNAME)
                excel_row_content.append(sanitized_testname)
                excel_rows.append(excel_row_content)

                if testbed_properties.get('topology', "") and testbed_properties.get('hwsku', ""):
                    topology = testbed_properties.get('topology', "")
                    hwsku = testbed_properties.get('hwsku', "")
                    self.msft_topo_hwsku_results_set.add(f"{hwsku}_{topology}")
        if not excel_rows:
            logger.warning(f"Couldn't parse any testcase in junit file {junit_xml_path}")
        return excel_rows

    def parse_junit_file(self, session_id, junit_xml_path):
        """
        return a list of the parsed excel row for each test case in the junit file.
        difference between failure and error is that in case of failure,
        test had raised some sort of assertion error (in Allure, the failure will be marked in red).
        in case of error, for example, ansible module had failed during the run of the test
        (in Allure, the error will be marked in yellow).
        :param session_id: i.e, 8254248
        :param junit_xml_path: path to junit xml file
        :return: a list of excel rows for each test case in the xml file
        """
        mytree = ET.parse(junit_xml_path)
        myroot = mytree.getroot()
        excel_rows = []
        was_xml_updated = False
        modify_xml = "None"
        for idx, testsuite in enumerate(myroot.findall('testsuite')):
            for testcase in testsuite.findall('testcase'):
                excel_row_content = []
                testcase_properties = self.parse_testcase_properties(testcase)

                """
                ["session_id", "mars_key_id", "testbed", "test name", "start", "end", "result", "message",
                   "topology", "host", "asic", "platform", "hwsku", "os_version", "xml_path",
                   "was_xml_updated", "modify_xml"]
                """
                excel_row_content.append(session_id)
                excel_row_content.append(self.get_mars_key_id(junit_xml_path))
                excel_row_content.append(self.sessions_testbed_properties[session_id]['testbed'])
                excel_row_content.append(testcase_properties['test_name'])
                excel_row_content.append(testcase_properties.get('start', ""))
                excel_row_content.append(testcase_properties.get('end', ""))
                excel_row_content.append(testcase_properties['result'])
                excel_row_content.append(testcase_properties['message'])
                excel_row_content.append(self.sessions_testbed_properties[session_id]['topology'])
                excel_row_content.append(self.sessions_testbed_properties[session_id]['host'])
                excel_row_content.append(self.sessions_testbed_properties[session_id]['asic'])
                excel_row_content.append(self.sessions_testbed_properties[session_id]['platform'])
                excel_row_content.append(self.sessions_testbed_properties[session_id]['hwsku'])
                excel_row_content.append(self.sessions_testbed_properties[session_id]['os_version'])
                excel_row_content.append(junit_xml_path)
                excel_row_content.append(was_xml_updated)
                excel_row_content.append(modify_xml)
                sanitized_testname = \
                    testcase_properties['test_name'].replace(self.sessions_testbed_properties[session_id]['host'],
                                                             ResultUploaderConst.SANITIZED_HOSTNAME)
                excel_row_content.append(sanitized_testname)
                excel_rows.append(excel_row_content)
        if not excel_rows:
            logger.warning(f"Couldn't parse any testcase in junit file {junit_xml_path}")
        return excel_rows

    @staticmethod
    def get_mars_key_id(junit_xml_path):
        filename = os.path.basename(junit_xml_path)
        mars_key_id = re.search(r"([\d|\.]*)\.xml", filename).group(1)
        return mars_key_id

    def parse_testcase_properties(self, testcase):
        testcase_properties = {}
        if testcase.findall('properties'):
            test_properties = testcase.findall('properties')[0]
            for testcase_property in test_properties:
                testcase_properties[testcase_property.attrib['name']] = testcase_property.attrib['value']
        classname_path = self.parse_classname(testcase.attrib['classname'])
        testcase_properties['test_name'] = f"{classname_path}::{testcase.attrib['name']}"

        failure = testcase.findall('failure')
        skipped = testcase.findall('skipped')
        error = testcase.findall('error')
        if failure or error:
            testcase_properties['result'] = 'fail'
            if error:
                testcase_properties['message'] = error[0].attrib['message']
            if failure:
                testcase_properties['message'] = failure[0].attrib['message']
        elif skipped:
            testcase_properties['result'] = 'skipped'
            testcase_properties['message'] = skipped[0].attrib['message']
            redmine_issue = re.search(r"https:\/\/redmine\.mellanox\.com\/issues\/(\d+)",
                                      testcase_properties['message'])
            if redmine_issue:
                self.redmine_bugs.add(redmine_issue.group())
        else:
            testcase_properties['result'] = 'pass'
            testcase_properties['message'] = ""
        return testcase_properties

    @staticmethod
    def parse_testbed_properties(testsuite):
        testbed_properties = {}
        if testsuite.findall('properties'):
            properties = testsuite.findall('properties')[0]
            for testsuite_property in properties:
                testbed_properties[testsuite_property.attrib['name']] = testsuite_property.attrib['value']
        return testbed_properties

    @staticmethod
    def parse_classname(testcase_classname):
        testcase_class_path_list = testcase_classname.split(".")
        class_name = testcase_class_path_list[-1]
        if "test_" in class_name:
            file_name = f"{class_name}.py"
            path_component_list = testcase_class_path_list[:-1] + [file_name]
            testcase_classname_path = "/".join(path_component_list)
        else:
            file_name = f"{testcase_class_path_list[-2]}.py"
            path_component_list = testcase_class_path_list[:-2] + [file_name]
            testcase_classname_path = f'{"/".join(path_component_list)}::{class_name}'
        return testcase_classname_path

    @staticmethod
    def get_full_test_path(testcase_name):
        test_path, test_name = testcase_name.split(".py::")
        correct_test_path = test_path + ".py"
        full_test_path = os.path.join("tests", correct_test_path)
        return full_test_path

    def is_test_exist_in_remote(self, full_test_path):
        if full_test_path in self.nvidia_community_tests:
            return False
        else:
            command = f"cd {self.git_path} && git cat-file -e origin/{self.branch}:{full_test_path} && echo file exists"
            stream = os.popen(command)
            output = stream.read()
            return "file exists" in output

    def copy_xml_results_to_result_folder(self):
        """
        By default, the junit_xml_parser.py expects certain patterns of xml files.
        tr.xml, test_*.xml, `*test*.xml
        that's the reason for the test prefix in the new_file_name
        :return:
        """
        if not os.path.exists(self.result_folder):
            os.makedirs(self.result_folder, exist_ok=True)
        logger.info(f"Copy all Junit XML files to {self.result_folder}")
        df = pd.read_excel(self.export_excel_table_path, sheet_name=self.sheet_name, index_col=0)
        df.reset_index(drop=True, inplace=True)
        copied_xmls = set()
        for i in range(len(df)):
            session = df.loc[i, "session_id"]
            hwsku = df.loc[i, "hwsku"]
            topology = df.loc[i, "topology"]
            xml_path = df.loc[i, "xml_path"]
            if xml_path not in copied_xmls:
                folder_name = f"{hwsku}_{topology}"
                hwsku_topo_folder = os.path.join(self.result_folder, folder_name)
                if not os.path.exists(hwsku_topo_folder):
                    os.mkdir(hwsku_topo_folder)
                filename = os.path.basename(xml_path)
                new_file_name = f"test_{session}_{filename}"
                new_file_path = os.path.join(hwsku_topo_folder, new_file_name)
                shutil.copyfile(xml_path, new_file_path)
                copied_xmls.add(xml_path)

    def create_final_results_table(self):
        worksheet_content = []
        for root, dirs, files in os.walk(self.result_folder):
            for filename in files:
                if filename.endswith(".xml") or filename.endswith(".xml.updated"):
                    junit_xml_path = os.path.join(root, filename)
                    session = re.search(r"test_(\d+)_.*", filename).group(1)
                    if session not in self.sessions_testbed_properties.keys():
                        self.update_session_testbed_properties(session)
                    worksheet_content += self.parse_junit_file(session, junit_xml_path)
        df = pd.DataFrame(worksheet_content, columns=ResultUploaderConst.XLSX_HEADER)
        df.to_excel(self.exported_results_excel_table_path, sheet_name=self.sheet_name)

    def export_results(self):
        uploader_script_path = os.path.join(MarsConstants.SONIC_MGMT_DIR,
                                            ResultUploaderConst.UPLOADER_SCRIPT_RELATIVE_PATH)
        report_id_dirs = [x[0] for x in os.walk(self.result_folder)]
        report_id_dirs.remove(self.result_folder)
        for report_id_dir in report_id_dirs:
            export_results_command = f'python3 {uploader_script_path} -c "test_result" ' \
                                     f'{report_id_dir} {ResultUploaderConst.DATABASE_NAME}'
            logger.info(f"CMD: {export_results_command}")
            if self.sonic_mgmt_ip:
                logger.info(f"User provided sonic-mgmt IP: {self.sonic_mgmt_ip}")
                sonic_mgmt_engine = LinuxSshEngine(ip=self.sonic_mgmt_ip,
                                                   username=sonic_mgmt_user,
                                                   password=sonic_mgmt_password)
                # output = sonic_mgmt_engine.run_cmd(export_results_command, validate=False)
            else:
                logger.info(f"User didn't provided sonic-mgmt IP, "
                            f"assumption is that script is already running from sonic-mgmt docker")
                # output = os.system(export_results_command)
            logger.info(f"CMD output: {output}")
            # TODO: add output validation

    def save_sessions_for_image(self, sessions_ids):
        stm_engine = LinuxSshEngine(ip=InfraConst.STM_IP, username=stm_user, password=stm_password)
        str_sessions_ids = [str(session_id) for session_id in sessions_ids]
        sessions_list = ",".join(str_sessions_ids)
        remote_cmd = f"python {ResultUploaderConst.SAVE_SESSIONS_SCRIPT}" \
                     f" --action save --description {self.sonic_version}_msft_uploaded_sessions" \
                     f" --sessions_id {sessions_list}"
        logger.info("CMD: %s" % remote_cmd)
        output = stm_engine.run_cmd(remote_cmd, validate=False)
        for session_id in sessions_ids:
            assert re.search(rf"Session\s+{session_id}\s+actions:save_session", output), \
                f"Not found session:{session_id} in saved sessions output, verify session has been saved"
        logger.info(f"Saved sessions are: {sessions_list}")
        self.compose_save_results_mail(sessions_ids)

    def get_setups_from_results(self, setups_list):
        setups_in_results = []
        setups_not_found = []
        for host in self.hosts:
            host_setup_name = self.get_host_setup_name(host, setups_list)
            if host_setup_name:
                setups_in_results.append(host_setup_name)
            else:
                setups_not_found.append(host)
        assert not setups_not_found, f"No setup name was found for the following hosts {setups_not_found}, " \
                                     f"please review setups list"
        return setups_in_results

    @staticmethod
    def get_host_setup_name(host, setups_list):
        host_setup_name = None
        for setup_name in setups_list:
            if host in setup_name:
                host_setup_name = setup_name
        return host_setup_name

    def filter_setups(self, setups):
        filter_setups = []
        for setup in setups:
            setup_platform = self.all_setups_platforms[setup]
            if any([platform in setup_platform for platform in self.platform_list]):
                filter_setups.append(setup)
        return filter_setups

    def compose_collect_results_mail(self, setups_in_results, setups_not_in_results):
        build_table_dict_content = {
            "Collected Results Summary": {"Collected Results Excel Table": self.excel_table_path},
            "Nvidia tests excluded in excel": {self.get_list_in_html_format(self.nvidia_community_tests): ""},
            "Setups in collected results": {self.get_list_in_html_format(setups_in_results): ""},
            "Setups not in collected results": {self.get_list_in_html_format(setups_not_in_results): ""},
            "unresolved Redmine bugs": {self.get_list_in_html_format(self.redmine_bugs): ""}
        }
        self.compose_build_tables_content(build_table_dict_content)

    @staticmethod
    def get_list_in_html_format(items_list):
        items_li = [f"<li>{item}</li>" for item in items_list]
        li_str = "".join(items_li)
        return f"<ul>{li_str}</ul>"

    def compose_build_tables_content(self, build_tables_dict_content):
        tables = ["<!-- HEAD BANNER -->"]
        for table_title, table_dict_content in build_tables_dict_content.items():
            build_table_content = []
            for item_key, item_value in table_dict_content.items():
                build_table_content.append(f"<tr><td>{item_key}</td><td>{item_value}</td><tr>")
            info_details = "".join(build_table_content)
            table = """
            <table class="section">
                <tr class="tr-title">
                    <td class="td-title-main" colspan=2>
                        {title}
                    </td>
                   {info}
                </table>
                <BR>
            """.format(title=table_title, info=info_details)
            tables.append(table)
        on_the_fly_head_banners = "".join(tables)
        with open(self.build_mail_table, 'w') as f:
            f.write(on_the_fly_head_banners)

    def compose_modify_results_mail(self, excel_path):
        unresolved_redmine_bugs = set(self.redmine_bugs).difference(set(self.community_issues_redmine_bugs.keys()))
        unresolved_redmine_bugs = unresolved_redmine_bugs.difference(set(self.redmine_issues_to_update.keys()))
        build_table_dict_content = {
            "Modified Results Summary": {"Modified Results Excel Table": excel_path},
            "Unresolved Redmine bugs": {self.get_list_in_html_format(unresolved_redmine_bugs): ""},
            "User Updated Redmine Issues": self.redmine_issues_to_update,
            "Redmine Issues Updated as Community Issues": self.community_issues_redmine_bugs,
            "Updated XML files": self.modified_xml_path
        }
        self.compose_build_tables_content(build_table_dict_content)

    def get_exported_hwsku_topologies(self):
        report_id_dirs = [x[0] for x in os.walk(self.result_folder)]
        report_id_dirs.remove(self.result_folder)
        report_id_dir_names = [os.path.basename(os.path.normpath(report_id_dir)) for report_id_dir in report_id_dirs]
        exported_hwsku_topologies = {}
        for report_id_dir_name in report_id_dir_names:
            hwsku, topology = report_id_dir_name.split("_")
            exported_hwsku_topologies[hwsku] = topology
        return exported_hwsku_topologies

    def compose_export_results_mail(self, excel_path):
        build_table_dict_content = {
            "Exported Results Summary": {
                "Exported Results Excel Table": excel_path,
                "Results Folder": self.result_folder
            },
            "Exported Hwsku-topologies": self.get_exported_hwsku_topologies()
        }
        self.compose_build_tables_content(build_table_dict_content)

    def compose_compare_results_mail(self):
        build_table_dict_content = {
            "Compare Results Summary": {"Compared Results Excel Table": self.compare_results_excel_table_path}
        }
        self.compose_build_tables_content(build_table_dict_content)

    def compose_save_results_mail(self, saved_sessions):
        build_table_dict_content = {
            "Saved sessions": {self.get_list_in_html_format(saved_sessions): ""},
        }
        self.compose_build_tables_content(build_table_dict_content)

    def compose_concat_results_mail(self):
        build_table_dict_content = {
            "Concat Results Summary": {"Concat Results Excel Table": self.concated_results_excel_table_path}
        }
        self.compose_build_tables_content(build_table_dict_content)


if __name__ == '__main__':
    try:
        arguments = init_parser()
        validate_env_variables()
        set_logger(arguments.log_level)
        ReleaseResultsUploader(arguments).exec_command_on_regression_results_to_msft()
        logger.info('Script Finished!')

    except Exception as e:
        traceback.print_exc()
        sys.exit(LinuxConsts.error_exit_code)
