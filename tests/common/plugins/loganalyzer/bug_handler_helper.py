import os
import json
import logging
from pathlib import Path
from infra.tools.redmine.redmine_api import REDMINE_ISSUES_URL
import time
from paramiko.ssh_exception import SSHException
import pathlib
from retry.api import retry

from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure
from ngts.constants.constants import BugHandlerConst, InfraConst
from ngts.nvos_constants.constants_nvos import SystemConsts

from ngts.helpers.bug_handler.bug_handler_helper import create_session_tmp_folder, clear_files, bug_handler_wrapper, \
    create_log_analyzer_yaml_file, group_log_errors_by_timestamp, summarize_la_bug_handler
from ngts.scripts.allure_reporter import predict_allure_report_link

logger = logging.getLogger()


def handle_log_analyzer_errors(cli_type, branch, test_name, duthost, log_analyzer_bug_metadata, testbed,
                               bug_handler_action):
    """
    Call bug handler on all log errors and return list of dictionaries with results
    :param cli_type: i.e, Sonic
    :param branch: i.e 202211
    :param test_name: i.e, test_lags_scale
    :param duthost: duthost object
    :param log_analyzer_bug_metadata: dictionary with info that we want to add to log analyzer bug
    :param testbed: testbed
    :param bug_handler_action: dictionary include if need to create or update the RM issue when err msg found.
    :return: A list of dictionaries with results for each optional bug
    i.e., ['test_name': 'test_lags_scale',
            'results':
    [{'file_name': '2022-06-21_23-24-07_orchagent-asan.log.40',
    'messages': ['INFO:handle_bug:reading configuration from', ...],
    'rc': 0,
    'decision': 'update'},...]
    },...]
    """

    with allure.step("Log Analyzer bug handler"):
        bug_handler_dumps_results = []
        hostname = duthost.hostname
        log_errors_dir_path = Path(BugHandlerConst.LOG_ERRORS_DIR_PATH.format(hostname=hostname))
        if log_errors_dir_path.exists():
            session_id = os.environ.get(InfraConst.ENV_SESSION_ID)
            if not session_id:
                timestamp = time.strftime("%Y-%m-%d-%H:%M:%S", time.gmtime())
                session_id = f"manual_run_{timestamp}"
            session_tmp_folder = create_session_tmp_folder(session_id)
            redmine_project = BugHandlerConst.CLI_TYPE_REDMINE_PROJECT[cli_type]
            conf_path = BugHandlerConst.BUG_HANDLER_CONF_FILE[redmine_project]

            bug_handler_create_action = bug_handler_action.get("create", False)
            bug_handler_update_action = bug_handler_action.get("update", False)
            bug_handler_no_action = not (bug_handler_create_action and bug_handler_update_action)

            if bug_handler_no_action:
                tar_file_path = None
            else:
                tar_file_path = get_tech_support_from_switch(duthost, testbed, session_id, cli_type)

            for log_errors_file_path in log_errors_dir_path.iterdir():
                with log_errors_file_path.open("r") as log_errors_file:
                    data = json.load(log_errors_file)
                error_groups = group_log_errors_by_timestamp(data.get("log_errors", ""))
                log_errors_file_path.unlink()

                for error_group in error_groups:
                    yaml_file_path = create_log_analyzer_yaml_file(error_group, session_tmp_folder, redmine_project,
                                                                   test_name, tar_file_path, hostname,
                                                                   log_analyzer_bug_metadata)

                    if yaml_file_path:
                        with allure.step("Run Bug Handler on Log Analyzer error"):
                            logger.info(f"Run Bug Handler on Log Analyzer error: {error_group}")
                            error_dict = {BugHandlerConst.LA_ERROR: error_group}
                            error_dict.update(bug_handler_wrapper(conf_path, redmine_project, branch,
                                                                  tar_file_path, yaml_file_path,
                                                                  BugHandlerConst.BUG_HANDLER_LOG_ANALYZER_USER,
                                                                  BugHandlerConst.BUG_HANDLER_SCRIPT,
                                                                  bug_handler_no_action, bug_handler_action))
                            bug_handler_dumps_results.append(error_dict)

            clear_files(session_id)
        return summarize_la_bug_handler(bug_handler_dumps_results)


def get_tech_support_from_switch(duthost, testbed, session_id, cli_type):
    """
    generate tech support from the switch and copy it to player
    :param duthost: duthost object
    :param testbed: testbed name
    :param session_id: MARS session id
    :return: file path
    """
    if cli_type == "Sonic":
        tar_file_path_on_switch = _generate_sonic_techsupport(duthost)
    elif cli_type == "NVUE":
        tar_file_path_on_switch = _generate_nvue_techsupport(duthost)
    else:
        raise Exception(f"No such cli_type: {cli_type}")

    tar_file_name = tar_file_path_on_switch.split('/')[-1]
    dumps_folder = os.environ.get(InfraConst.ENV_LOG_FOLDER)
    if not dumps_folder:  # default value is empty string, defined in steps file
        dumps_folder = create_result_dir(testbed, session_id, InfraConst.CASES_DUMPS_DIR)

    tar_file_path = dumps_folder + '/'

    duthost.fetch(src=tar_file_path_on_switch, dest=tar_file_path, flat=True)
    return os.path.join(dumps_folder, tar_file_name)


@retry(Exception, tries=5, delay=20)
def _generate_sonic_techsupport(duthost):
    return duthost.shell('sudo generate_dump -s \"-{} hours\"'.format(2))["stdout_lines"][-1]


def _generate_nvue_techsupport(duthost):
    dump_file = duthost.shell('nv action generate system tech-support')["stdout_lines"][-2].split(' ')[-1]
    return SystemConsts.TECHSUPPORT_FILES_PATH + dump_file


def create_result_dir(testbed, session_id, suffix_path_name):
    """
    Create directory for test artifacts in shared location
    :param testbed: name of the testbed
    :param session_id: MARS session id
    :param suffix_path_name: End part of the directory name
    :return: created directory path
    """
    folder_path = '/'.join([InfraConst.REGRESSION_SHARED_RESULTS_DIR, testbed, session_id, suffix_path_name])
    logging.info("Create folder: {} if it doesn't exist".format(folder_path))
    pathlib.Path(folder_path).mkdir(parents=True, exist_ok=True)
    logging.info("Created folder - {}".format(folder_path))
    return folder_path


def log_analyzer_bug_handler(duthost, request):
    """
    If the run_log_analyzer_bug_handler is True, run this function to handle the err msg detected in the loganalyzer
    """
    if not request:
        logger.warning("Skip the loganalyzer bug handler, To run the it, 'request' is needed when create LogAnalyzer")
        return
    if "rep_setup" in request.node.__dict__ and request.node.rep_setup.failed:
        logger.warning("Skip the loganalyzer bug handler: the test failed in the fixture setup, "
                       "no need to run the bug handler")
        return
    if "rep_call" in request.node.__dict__ and request.node.rep_call.failed:
        logger.warning("Skip the loganalyzer bug handler: the test is failed, no need to run the bug handler")
        return
    test_name = request.node.name
    bug_handler_actions = get_bug_handler_actions(request)
    run_log_analyzer_bug_handler = is_log_analyzer_bug_handler_enabled(bug_handler_actions)

    if run_log_analyzer_bug_handler:
        log_analyzer_handler_info = get_log_analyzer_handler_info(duthost)

        if "allure_server_project_id" in request.config.option:
            allure_project = request.config.getoption('--allure_server_project_id')
            allure_report_url = predict_allure_report_link(InfraConst.ALLURE_SERVER_URL, allure_project)
        else:
            current_time = str(time.time()).replace('.', '')
            request.session.config.option.allure_server_project_id = current_time
            allure_report_url = \
                f"{InfraConst.ALLURE_SERVER_URL}/allure-docker-service/projects/{current_time}/reports/1/index.html"

        logger.info("--------------- Start Log Analyzer Bug Handler ---------------")
        # for community test case, it has --testbed, for canonical test cases, it has --setup_name
        if "setup_name" in request.config.option:
            setup_name = request.config.getoption('--setup_name')
        else:
            setup_name = request.config.getoption('--testbed')

        system_type = duthost.facts['hwsku']

        bug_handler_dict = {'test_description': request.node.function.__doc__,
                            'pytest_cmd_args': " ".join(request.node.config.invocation_params.args),
                            'system_type': system_type,
                            'detected_in_version': log_analyzer_handler_info['version'],
                            'setup_name': setup_name,
                            'report_url': allure_report_url}
        log_analyzer_res = handle_log_analyzer_errors(log_analyzer_handler_info['cli_type'],
                                                      log_analyzer_handler_info['branch'], test_name, duthost,
                                                      bug_handler_dict, setup_name, bug_handler_actions)
        logger.info(f"Log Analyzer result: {json.dumps(log_analyzer_res, indent=2)}")
        error_msg = ''
        if log_analyzer_res[BugHandlerConst.NO_ACTION_MODE]:
            error_msg += f"There are err msg detected under the {BugHandlerConst.NO_ACTION_MODE} mode:\n"
            for err_with_no_action in log_analyzer_res[BugHandlerConst.NO_ACTION_MODE]:
                bug_id = err_with_no_action[BugHandlerConst.BUG_HANDLER_BUG_ID]
                err_logs = err_with_no_action[BugHandlerConst.LA_ERROR]
                if bug_id:
                    error_msg += f"Relative bug is #{bug_id} detected for the err logs: {err_logs} \n"
                else:
                    error_msg += f"No relative bug detected for the err logs: {err_logs} \n"

        if log_analyzer_res[BugHandlerConst.BUG_HANDLER_DECISION_CREATE]:
            created_bug_items = log_analyzer_res[BugHandlerConst.BUG_HANDLER_DECISION_CREATE]
            error_msg += f"There are {len(created_bug_items)} new Log Analyzer bugs Created: \n"
            for i, (bug_id, bug_title) in enumerate(created_bug_items.items(), start=1):
                error_msg += f"{i}) {REDMINE_ISSUES_URL+str(bug_id)}:  {bug_title}\n"

        if log_analyzer_res[BugHandlerConst.BUG_HANDLER_FAILURE]:
            error_msg = error_msg + f"\nThe log analyzer bug handler has failed, due to the following:" \
                                    f"{json.dumps(log_analyzer_res[BugHandlerConst.BUG_HANDLER_FAILURE], indent=2)}"
        if error_msg:
            raise Exception(error_msg)


def is_log_analyzer_bug_handler_enabled(bug_handler_actions):
    """
    Check if need to run the log analyzer bug handler based on the bug handler actions.
    """
    return bug_handler_actions['only_check'] or bug_handler_actions['create'] or bug_handler_actions['update']


def get_log_analyzer_handler_info(duthost):

    log_analyzer_handler_info = {
        'branch': '',
        'cli_type': '',
        'version': ''
    }
    cli_type = os.environ.get("CLI_TYPE")
    if not cli_type:
        try:
            duthost.shell("show version")
            cli_type = "Sonic"
        except:  # noqa: E722
            cli_type = "NVUE"

    log_analyzer_handler_info['cli_type'] = cli_type
    log_analyzer_handler_info['branch'] = get_sonic_branch(duthost, cli_type)
    log_analyzer_handler_info['version'] = duthost.os_version

    return log_analyzer_handler_info


def get_bug_handler_actions(request):
    """
    Get the bug handler actions, the return is a dictionary with 3 keys, "create", "update" and "only_check"
    """

    bug_handler_actions = {
        'create': False,
        'update': False,
        'only_check': True
    }

    project_bug_create_map = {
        "regression": True,
        "sonic_mgmt_ci": True,
        "sonic_main": True,
        "sonic_public": True,
        "sonic_dpu_build": True,
        "sonic_ci": False,
        "sonic_dpu_ci": False
    }

    project_bug_update_map = {
        "regression": True,
        "sonic_mgmt_ci": True,
        "sonic_main": True,
        "sonic_public": True,
        "sonic_dpu_build": True,
        "sonic_ci": True,
        "sonic_dpu_ci": True
    }

    project_bug_only_check_map = {
        "regression": False,
        "sonic_mgmt_ci": False,
        "sonic_main": False,
        "sonic_public": False,
        "sonic_dpu_build": False,
        "sonic_ci": False,
        "sonic_dpu_ci": False
    }

    project = os.environ.get("REGRESSION_TYPE")
    bug_handler_actions['create'] = project_bug_create_map.get(project, False)
    bug_handler_actions['update'] = project_bug_update_map.get(project, False)
    bug_handler_actions['only_check'] = project_bug_only_check_map.get(project, True)

    _update_bug_handler_actions(request, bug_handler_actions)

    logger.info(f"The bug handler actions for the {project} is: {bug_handler_actions}")

    return bug_handler_actions


def _update_bug_handler_actions(request, bug_handler_actions):
    """
    Update the bug handler actions with the value specified in the param enable_bug_handler
    """
    bug_handler_params = request.config.getoption('--bug_handler_params')
    if bug_handler_params == "enable":
        bug_handler_actions['create'] = True
        bug_handler_actions['update'] = True
    elif bug_handler_params == "only_check":
        bug_handler_actions['create'] = False
        bug_handler_actions['update'] = False
        bug_handler_actions['only_check'] = True


def get_sonic_branch(duthost, cli_type):
    """
    Get the SONiC branch based on release field from /etc/sonic/sonic_version.yml
    :return: branch name
    """
    try:
        release_output = duthost.shell("sonic-cfggen -y /etc/sonic/sonic_version.yml -v release")['stdout_lines']
        branch = release_output[0]
    except SSHException as err:
        branch = 'Unknown'
        logger.error(f'Unable to get branch. Assuming that the device is not reachable. Setting the branch as Unknown. '
                     f'Got error: {err}')
    # master branch always has release "none"
    except Exception as nvueerr:
        if cli_type == 'NVUE':
            branch = "master"
            logger.warning(f'unable to run sonic cmd on dut. Assuming that sonic image is not installed on this device '
                           f'Got error: {nvueerr}')
        else:
            raise nvueerr
    if branch == "none":
        branch = "master"
    return branch.strip()
