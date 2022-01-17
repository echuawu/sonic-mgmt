import logging
import yaml
import os
import re
import requests
import subprocess

from abc import ABCMeta, abstractmethod
from ngts.tools.redmine.redmine_api import is_redmine_issue_active


logger = logging.getLogger()


class DynamicLaConsts:
    CUSTOM_TEST_SKIP_PLATFORM_TYPE = 'dynamic_tests_skip_platform_type'
    CUSTOM_TEST_SKIP_BRANCH_NAME = 'dynamic_tests_skip_branch_name'

    LA_DYNAMIC_IGNORES_LIST = 'LA_DYNAMIC_IGNORES_LIST'
    ERRORS_LIST = 'Errors_list'
    REDMINE = 'Redmine'
    PLATFORM = 'Platform'
    AFFECTED_TEST_CASES = 'Affected_test_cases'
    CONDITIONS = 'Conditions'
    BRANCH = 'Branch'
    GITHUB = 'GitHub'


def pytest_collection(session):
    initialize_cached_variables(session)


def initialize_cached_variables(session):
    session.config.cache.set(DynamicLaConsts.LA_DYNAMIC_IGNORES_LIST, None)


def pytest_runtest_call(item):
    """
    Pytest hook which run for each test case and extend loganalyzer ignore list by errors which should be ignored for
    specific test case
    :param item: pytest build-in
    """
    loganalyzer = item.funcargs['loganalyzer']

    if loganalyzer:
        extended_ignore_list = []

        dynamic_la_ignore_list = read_la_dynamic_ignore_file(item)

        for ignore_block in dynamic_la_ignore_list:

            errors_regexp_to_be_ignored_list = ignore_block.get(DynamicLaConsts.ERRORS_LIST)
            if not errors_regexp_to_be_ignored_list:
                raise Exception('Errors list not provided for dynamic LA errors ignore. Check YAML file.')
            conditions_dict = ignore_block.get(DynamicLaConsts.CONDITIONS)
            if not conditions_dict:
                raise Exception('LA dynamic errors ignore condition not provided in ignore block: {}.'
                                'Check YAML file and fix it'.format(ignore_block))

            for condition_dict_entry in conditions_dict:
                operand = 'and' if is_nested_dict(condition_dict_entry) else 'or'
                is_error_ignore_required = get_checkers_result(condition_dict_entry, item, operand=operand)
                if is_error_ignore_required:
                    extended_ignore_list.extend(errors_regexp_to_be_ignored_list)
                    # Found match on the first condition block, no need to check others
                    break

        if extended_ignore_list:
            logger.info('New dynamic errors ignore will be added: {}'.format(extended_ignore_list))
            extend_la_ignore_regex(loganalyzer, extended_ignore_list)
        else:
            logger.info('No dynamic errors ignore will be added')


def extend_la_ignore_regex(loganalyzer, extended_ignore_list):
    """
    Extend LogAnalyzerd ignore regex list
    :param loganalyzer: loganalyzer obj
    :param extended_ignore_list: list of ignores which should be added
    """
    if isinstance(loganalyzer, dict):
        # Community LA
        for host in loganalyzer:
            loganalyzer[host].ignore_regex.extend(extended_ignore_list)
    else:
        # Canonical LA
        loganalyzer.ignore_regex.extend(extended_ignore_list)


def read_la_dynamic_ignore_file(item):
    """
    Read loganalyzer dynamic ignore file
    :param item: pytest build-in
    :return: list
    """
    ignore_list = item.session.config.cache.get(DynamicLaConsts.LA_DYNAMIC_IGNORES_LIST, None)

    if ignore_list:
        logger.info('Reading dynamic errors ignore data from cache')
    else:
        logger.info('Reading dynamic errors ignore data from file')
        la_dynamic_ignore_folder_path = os.path.dirname(__file__)
        path_to_dynamic_la_ignore_file = os.path.join(la_dynamic_ignore_folder_path, 'dynamic_loganalyzer_ignores.yaml')

        with open(path_to_dynamic_la_ignore_file) as dynamic_la_ignore_obj:
            ignore_list = yaml.load(dynamic_la_ignore_obj, Loader=yaml.FullLoader)

        item.session.config.cache.set(DynamicLaConsts.LA_DYNAMIC_IGNORES_LIST, ignore_list)

    return ignore_list


def is_nested_dict(dict_obj):
    nested_dict_min_len = 2
    return len(dict_obj) >= nested_dict_min_len


def get_checkers_result(condition_dict_entry, item, operand='or'):
    """
    Check if errors should be added to ignored errors. Check conditions based operand.
    If operand "or" - check if one condition matched - then return True
    If operand "and" - check if all conditions matched - then return True, if some condition not matched and operand
    "and" - break(do not run all other checkers for save time) and return False
    :param condition_dict_entry: dictionary with conditions which should be checked - dynamic_loganalyzer_ignores.yaml
    :param item: pytest build-in
    :param operand: operand - "or" or "and"
    :return:
    """
    available_checkers = {DynamicLaConsts.AFFECTED_TEST_CASES: AffectedTestCaseDynamicErrorsIgnore,
                          DynamicLaConsts.PLATFORM: PlatformDynamicErrorsIgnore,
                          DynamicLaConsts.BRANCH: BranchDynamicErrorsIgnore,
                          DynamicLaConsts.REDMINE: RedmineDynamicErrorsIgnore,
                          DynamicLaConsts.GITHUB: GitHubDynamicErrorsIgnore}

    checkers_result = []

    # Run the less time-consuming checkers first
    checkers_ordered_by_prio_list = [DynamicLaConsts.AFFECTED_TEST_CASES, DynamicLaConsts.PLATFORM,
                                     DynamicLaConsts.BRANCH, DynamicLaConsts.REDMINE, DynamicLaConsts.GITHUB]

    for checker in checkers_ordered_by_prio_list:
        if checker in condition_dict_entry:
            checker_obj = available_checkers[checker](condition_dict_entry, item)
            is_checker_matched = checker_obj.is_checker_match()
            checkers_result.append(is_checker_matched)
            # Do not continue if operand "and" and we already have failed checker
            if not is_checker_matched and operand == 'and':
                break

    if operand == 'or':
        ignore_error_required = any(checkers_result)
    else:
        ignore_error_required = all(checkers_result)

    return ignore_error_required


def run_cmd_on_dut(pytest_item_obj, cmd):
    """
    Run command on DUT using ansible and return output
    """
    host = pytest_item_obj.session.config.option.ansible_host_pattern
    inventory = pytest_item_obj.session.config.option.ansible_inventory
    inv = get_inventory_argument(inventory)
    output = subprocess.check_output('ansible {} {} -a "{}"'.format(host, inv, cmd), shell=True)
    return output


def get_inventory_argument(inventory):
    """
    Get Ansible inventory arguments
    """
    inv = ''

    if type(inventory) is list:
        for inv_item in inventory:
            inv += ' -i {}'.format(inv_item)
    else:
        for inv_item in inventory.split(','):
            inv += ' -i {}'.format(inv_item)

    return inv


class LaDynamicErrorsIgnore:
    __metaclass__ = ABCMeta

    def __init__(self, conditions_dict, pytest_item_obj):
        # self.name = 'CustomSkipIf'  # Example: Platform, Jira, Redmine - should be defined in each child class
        self.conditions_dict = conditions_dict
        self.pytest_item_obj = pytest_item_obj

    @abstractmethod
    def is_checker_match(self):
        """
        Decide whether or not to add ignore for errors
        :return: True/False
        """
        pass


class AffectedTestCaseDynamicErrorsIgnore(LaDynamicErrorsIgnore):
    def __init__(self, conditions_dict, pytest_item_obj):
        super(AffectedTestCaseDynamicErrorsIgnore, self).__init__(conditions_dict, pytest_item_obj)
        self.validation_name = DynamicLaConsts.AFFECTED_TEST_CASES

    def is_checker_match(self):
        is_errors_ignore_required = True

        if self.conditions_dict.get(self.validation_name):
            is_errors_ignore_required = False
            for test_prefix in self.conditions_dict[self.validation_name]:
                if str(self.pytest_item_obj.nodeid).startswith(test_prefix):
                    is_errors_ignore_required = True
                    break

        return is_errors_ignore_required


class BranchDynamicErrorsIgnore(LaDynamicErrorsIgnore):
    def __init__(self, conditions_dict, pytest_item_obj):
        super(BranchDynamicErrorsIgnore, self).__init__(conditions_dict, pytest_item_obj)
        self.current_branch = self.get_branch_name()
        self.validation_name = DynamicLaConsts.BRANCH

    def get_branch_name(self):
        """
        Get current branch name using ansible and store it in pytest.session.config.cache
        :return: platform_type - string with current branch name
        """
        branch_name = self.pytest_item_obj.session.config.cache.get(DynamicLaConsts.CUSTOM_TEST_SKIP_BRANCH_NAME, None)
        if not branch_name:
            logger.debug('Getting branch name from DUT')
            try:
                release_output = run_cmd_on_dut(self.pytest_item_obj,
                                                "sonic-cfggen -y /etc/sonic/sonic_version.yml -v release").strip()
                branch_name = self.get_branch_from_release_output(release_output)
                self.pytest_item_obj.session.config.cache.set(DynamicLaConsts.CUSTOM_TEST_SKIP_BRANCH_NAME, branch_name)
            except Exception as err:
                logger.error('Unable to get branch name. Custom skip by branch impossible. Error: {}'.format(err))
        else:
            logger.debug('Getting branch from pytest cache')

        logger.debug('Current branch is: {}'.format(branch_name))
        return branch_name

    @staticmethod
    def get_branch_from_release_output(release_output):
        """
        Get branch name from "sonic-cfggen -y /etc/sonic/sonic_version.yml -v release" output
        :param release_output: output of ansible command "sonic-cfggen -y /etc/sonic/sonic_version.yml -v release"
        :return: string with branch name, example: '202012'
        example of release_output:
            'r-lionfish-13 | CHANGED | rc=0 >>\nnone'
            'r-lionfish-13 | CHANGED | rc=0 >>\n202012'
        """
        branch_name = release_output.splitlines()[1]
        # master branch always has release "none"
        if branch_name == "none":
            branch_name = "master"
        return branch_name

    def is_checker_match(self):
        is_errors_ignore_required = True

        if self.conditions_dict.get(self.validation_name):
            is_errors_ignore_required = False
            for branch in self.conditions_dict[self.validation_name]:
                if str(branch) == self.current_branch:
                    is_errors_ignore_required = True
                    break

        return is_errors_ignore_required


class PlatformDynamicErrorsIgnore(LaDynamicErrorsIgnore):
    def __init__(self, conditions_dict, pytest_item_obj):
        super(PlatformDynamicErrorsIgnore, self).__init__(conditions_dict, pytest_item_obj)
        self.current_platform = self.get_platform_type()
        self.validation_name = DynamicLaConsts.PLATFORM

    def get_platform_type(self):
        """
        Get current platform type using ansible and store it in pytest.session.config.cache
        :return: platform_type - string with current platform type
        """
        platform_type = self.pytest_item_obj.session.config.cache.get(DynamicLaConsts.CUSTOM_TEST_SKIP_PLATFORM_TYPE,
                                                                      None)
        if not platform_type:
            logger.debug('Getting platform from DUT')
            try:
                show_platform_summary_raw_output = run_cmd_on_dut(self.pytest_item_obj, 'show platform summary')
                platform_type = self.get_platform_from_platform_summary(show_platform_summary_raw_output)
                self.pytest_item_obj.session.config.cache.set(DynamicLaConsts.CUSTOM_TEST_SKIP_PLATFORM_TYPE,
                                                              platform_type)
            except Exception as err:
                logger.error('Unable to get platform type. Custom skip by platform impossible. Error: {}'.format(err))
        else:
            logger.debug('Getting platform from pytest cache')

        logger.debug('Current platform type is: {}'.format(platform_type))
        return platform_type

    @staticmethod
    def get_platform_from_platform_summary(platform_output):
        """
        Get platform from 'show platform summary' output
        :param platform_output: 'show platform summary' command output
        :return: string with platform name, example: 'x86_64-mlnx_msn3420-r0'
        """
        platform = re.search(r'Platform:\s(.*)', platform_output, re.IGNORECASE).group(1)
        return platform

    def is_checker_match(self):
        is_errors_ignore_required = True

        if self.conditions_dict.get(self.validation_name):
            is_errors_ignore_required = False
            for platform in self.conditions_dict[self.validation_name]:
                if str(platform) in self.current_platform:
                    is_errors_ignore_required = True
                    break

        return is_errors_ignore_required


class RedmineDynamicErrorsIgnore(LaDynamicErrorsIgnore):
    def __init__(self, conditions_dict, pytest_item_obj):
        super(RedmineDynamicErrorsIgnore, self).__init__(conditions_dict, pytest_item_obj)
        self.validation_name = DynamicLaConsts.REDMINE

    def is_checker_match(self):
        is_errors_ignore_required = True

        if self.conditions_dict.get(self.validation_name):
            is_errors_ignore_required = False
            rm_issues_list = self.conditions_dict[self.validation_name]
            try:
                is_issue_active, issue_id = is_redmine_issue_active(rm_issues_list)
                if is_issue_active:
                    is_errors_ignore_required = True
            except Exception as err:
                logger.error('Got error: {} during getting info about RM issues: {} status'.format(err, rm_issues_list))

        return is_errors_ignore_required


class GitHubDynamicErrorsIgnore(LaDynamicErrorsIgnore):
    def __init__(self, conditions_dict, pytest_item_obj):
        super(GitHubDynamicErrorsIgnore, self).__init__(conditions_dict, pytest_item_obj)
        self.validation_name = DynamicLaConsts.GITHUB
        self.credentials = self.get_cred()
        self.github_username = self.credentials.get('user')
        self.api_token = self.credentials.get('api_token')
        self.auth = (self.github_username, self.api_token)

    @staticmethod
    def get_cred():
        """
        Get GitHub API credentials
        :return: dictionary with GitHub credentials {'user': aaa, 'api_token': 'bbb'}
        """
        cred_file_name = 'credentials.yaml'
        plugins_folder_path = os.path.dirname(__file__)
        parent_folder_path = plugins_folder_path.rstrip('loganalyzer_dynamic_errors_ignore')
        cred_file_path = os.path.join(parent_folder_path, 'custom_skipif', cred_file_name)

        with open(cred_file_path) as cred_file:
            cred = yaml.load(cred_file, Loader=yaml.FullLoader)

        return cred

    @staticmethod
    def get_github_issue_api_url(issue_url):
        """
        Get correct github api URL based on browser URL from user
        :param issue_url: github issue url
        :return: github issue api url
        """
        return issue_url.replace('github.com', 'api.github.com/repos')

    def make_github_request(self, url):
        """
        Send API request to github
        :param url: github api url
        :return: dictionary with data
        """
        response = requests.get(url, auth=self.auth)
        response.raise_for_status()
        return response.json()

    def is_github_issue_active(self, issue_url):
        """
        Check that issue active or not
        :param issue_url:  github issue URL
        :return: True/False
        """
        issue_url = self.get_github_issue_api_url(issue_url)
        response = self.make_github_request(issue_url)
        if response.get('state') == 'closed':
            if self.is_duplicate(response):
                logger.warning('GitHub issue: {} looks like duplicate and was closed. Please re-check and ignore'
                               'the test on the parent issue'.format(issue_url))
            return False
        return True

    @staticmethod
    def is_duplicate(issue_data):
        """
        Check if issue duplicate or note
        :param issue_data: github response dict
        :return: True/False
        """
        for label in issue_data['labels']:
            if 'duplicate' in label['name'].lower():
                return True
        return False

    def is_checker_match(self):
        is_errors_ignore_required = True

        if self.conditions_dict.get(self.validation_name):
            is_errors_ignore_required = False

            for github_issue in self.conditions_dict[self.validation_name]:
                if self.is_github_issue_active(github_issue):
                    is_errors_ignore_required = True
                    break

        return is_errors_ignore_required
