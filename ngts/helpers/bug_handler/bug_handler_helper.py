import os
import re
import yaml
import json
import logging
import allure
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from ngts.constants.constants import BugHandlerConst, InfraConst
from infra.tools.connection_tools.linux_ssh_engine import LinuxSshEngine
from infra.tools.general_constants.constants import DefaultSTMCred

logger = logging.getLogger()

STM_IP = "10.209.104.106"


def handle_sanitizer_dumps(dump_paths, cli_type, branch, version, setup_name):
    """
    Call bug handler on all sanitizer files in each dump in dump_paths,
    and return list with results
    :param dump_paths: a list of sanitizer dumps paths which were created during the session
    :param cli_type: i.e, Sonic
    :param branch: i.e 202211
    :param version: i.e, SONiC-OS-202211_RC15.1-7ceec30cc_Internal
    :param setup_name: i.e, sonic_lionfish_r-lionfish-14
    :return: A list of dictionaries with results for each dump
    i.e., [{'dump_name': 'dump_test_lags_scale_sanitizer_files_06_21_2022_23_27_04.tar.gz',
    'test_name': 'test_lags_scale',
    'results':
    [{'file_name': '2022-06-21_23-24-07_orchagent-asan.log.40',
    'messages': ['INFO:handle_bug:reading configuration from', ...],
    'rc': 0,
    'decision': 'update'},...]
    },...]
    """
    bug_handler_dumps_results = []
    stm_engine = LinuxSshEngine(STM_IP,
                                DefaultSTMCred.DEFAULT_USERNAME,
                                DefaultSTMCred.DEFAULT_PASS)
    session_id = os.environ.get(InfraConst.ENV_SESSION_ID)
    create_session_tmp_folder(stm_engine, session_id)
    redmine_project = BugHandlerConst.CLI_TYPE_REDMINE_PROJECT[cli_type]
    bug_handler_conf_file = BugHandlerConst.BUG_HANDLER_CONF_FILE[redmine_project]
    conf_path_at_stm = configure_stm_for_bug_handler(stm_engine, bug_handler_conf_file)
    for sanitizer_dump_path in dump_paths:
        with allure.step(f"Run Bug Handler on Sanitizer Dump: {sanitizer_dump_path}"):
            bug_handler_dumps_results.append(handle_sanitizer_dump(stm_engine, conf_path_at_stm,
                                                                   sanitizer_dump_path, redmine_project,
                                                                   branch, version, setup_name))
    clear_files(stm_engine, session_id)
    return bug_handler_dumps_results


def create_session_tmp_folder(stm_engine, session_id):
    stm_engine.run_cmd(f"sudo mkdir /tmp/{session_id}")
    stm_engine.run_cmd(f"sudo chmod 777 /tmp/{session_id}")


def clear_files(stm_engine, session_id):
    stm_engine.run_cmd(f"sudo rm -rf /tmp/{session_id}")
    os.system("rm -rf /tmp/parsed_sanitizer_dumps/")


def configure_stm_for_bug_handler(stm_engine, bug_handler_conf_file):
    logging.info(f"Copy Bug Handler Conf file to STM: {STM_IP}")
    conf_path_at_stm = scp_file_to_stm(bug_handler_conf_file)
    logger.info("Set Environment variable LOG_FORMAT_JSON to get bug handle output in JSON")
    stm_engine.run_cmd("export LOG_FORMAT_JSON=1")
    return conf_path_at_stm


def handle_sanitizer_dump(stm_engine, conf_path_at_stm, dump_path,
                          redmine_project, branch, version, setup_name):
    """
    Call bug handler with ASAN dump files and send email with results
    :param stm_engine: ssh engine for STM
    :param conf_path_at_stm: i.e, /tmp/sonic_bug_handler.conf
    :param dump_path: path to sanitizer dump
    :param redmine_project: i.e, SONiC-Design
    :param branch: i.e 202205
    :param version: i.e 202205_sai_integration.2-36792dcfc_Internal
    :param setup_name: i.e, sonic_lionfish_r-lionfish-14
    :return: dictionary with bug handler results for dump, i.e,
    {'dump_name': 'dump_test_lags_scale_sanitizer_files_06_21_2022_23_27_04.tar.gz',
    'test_name': 'test_lags_scale',
    'results':
    [{'file_name': '2022-06-21_23-24-07_orchagent-asan.log.40',
    'messages': ['INFO:handle_bug:reading configuration from', ...],
    'rc': 0,
    'decision': 'update'},...]
    }
    """
    bug_handler_dump_result = dict()
    bug_handler_dump_result["dump_name"] = Path(dump_path).name
    bug_handler_dump_result["test_name"] = get_test_name_from_sanitizer_dump(bug_handler_dump_result["dump_name"])
    bug_handler_dump_result["results"] = list()
    yaml_parsed_files_dict = parse_sanitizer_dump(dump_path, redmine_project, version, setup_name)
    for sanitizer_file_name, yaml_parsed_file in yaml_parsed_files_dict.items():
        yaml_parsed_file_path_at_stm = scp_file_to_stm(yaml_parsed_file)
        with allure.step(f"Run Bug Handler on sanitizer file: {sanitizer_file_name}"):
            bug_handler_dump_result["results"].append(bug_handler_wrapper(stm_engine, conf_path_at_stm,
                                                                          redmine_project, branch, sanitizer_file_name,
                                                                          yaml_parsed_file_path_at_stm))
    return bug_handler_dump_result


def get_test_name_from_sanitizer_dump(dump_name):
    regex = r"dump_(.*)_sanitizer_files_.*\.tar\.gz"
    return re.search(regex, dump_name).group(1)


def parse_sanitizer_dump(dump_path, project, version, setup_name):
    """
    :param dump_path: path to sanitizer dump
    :param project: i.e SONiC-Design
    :param version: i.e 202205_sai_integration.2-36792dcfc_Internal
    :param setup_name: i.e, sonic_lionfish_r-lionfish-14
    :return: a dictionary with parsed dump files paths for bug handler
    i.e, {'2022-06-21_23-24-07_orchagent-asan.log.40':
    '/tmp/parsed_sanitizer_dumps/dump_..._extracted/yaml_parsed_files/2022-06-21_23-24-07_orchagent-asan.log.40.yaml',
    ...}
    """
    yaml_parsed_files_dict = {}
    dump_base_dir, dump_file_name = os.path.split(dump_path)
    extracted_dump_dir = os.path.join(BugHandlerConst.SANITIZER_PARSED_DUMPS_FOLDER, f"{dump_file_name}_extracted")
    logger.info("Create folder: {} if it doesn't exist".format(extracted_dump_dir))
    Path(extracted_dump_dir).mkdir(parents=True, exist_ok=True)
    logger.info("Created folder - {}".format(extracted_dump_dir))
    with allure.step("Parse sanitizer dump contents"):
        os.system(f"tar -xzvf {dump_path} -C {extracted_dump_dir}")
        for filename in os.listdir(extracted_dump_dir):
            file_path = os.path.join(extracted_dump_dir, filename)
            if os.path.isfile(file_path):
                with allure.step(f"Parse sanitizer dump file: {filename}"):
                    yaml_file_path = parse_sanitizer_file(file_path, dump_path, project, version, setup_name)
                    yaml_parsed_files_dict.update({filename: yaml_file_path})
    return yaml_parsed_files_dict


def parse_sanitizer_file(file_path, dump_path, project, version, setup_name):
    """
    function will create a YAML file in the needed format for bug handler script
    :param file_path: path to sanitizer file
    :param dump_path: path to sanitizer dump
    :param project: i.e SONiC-Design
    :param version: i.e 202205_sai_integration.2-36792dcfc_Internal
    :param setup_name: i.e, sonic_lionfish_r-lionfish-14
    :return: path to parsed YAML file
    """
    file_base_dir, file_name = os.path.split(file_path)
    sanitizer_file_path_at_stm = scp_file_to_stm(file_path)
    dump_path_at_stm = scp_file_to_stm(dump_path)
    yaml_file_dir = os.path.join(file_base_dir, "yaml_parsed_files")
    yaml_file_path = os.path.join(file_base_dir, "yaml_parsed_files", f"{file_name}.yaml")
    Path(yaml_file_dir).mkdir(parents=True, exist_ok=True)
    contents = Path(file_path).read_text()
    contents_without_prefix = remove_error_prefix_from_sanitizer_file(contents)
    yaml_content_as_dict = {'description': contents_without_prefix,
                            'project': project,
                            'uploads': [sanitizer_file_path_at_stm, dump_path_at_stm],
                            'detected_in_version': version,
                            'session_id': os.environ.get(InfraConst.ENV_SESSION_ID),
                            'setup_name': setup_name,
                            'test_name': get_test_name_from_sanitizer_dump(dump_path)}
    yaml_content = yaml.dump(yaml_content_as_dict)
    with open(yaml_file_path, "a") as file:
        file.write(yaml_content)
    return yaml_file_path


def remove_error_prefix_from_sanitizer_file(contents):
    error_prefix_regex = r"(.*\n*=+\n*=+\d+=*ERROR:\s+)"
    error_prefix = re.search(error_prefix_regex, contents, re.IGNORECASE).group(1)
    contents_without_prefix = contents.replace(error_prefix, "")
    return contents_without_prefix


def scp_file_to_stm(file_path):
    """
    will copy given file to stm
    :param file_path: path to file to copy
    :return: copied file path at STM
    """
    file_base_dir, file_name = os.path.split(file_path)
    with allure.step(f"Copy file: {file_name} to STM"):
        file_path_at_stm = os.path.join("/tmp", os.environ.get(InfraConst.ENV_SESSION_ID), file_name)
        cmd = f'sudo sshpass -p "{DefaultSTMCred.DEFAULT_PASS}" scp -o StrictHostKeyChecking=no {file_path} ' \
              f'{DefaultSTMCred.DEFAULT_USERNAME}@{STM_IP}:{file_path_at_stm}'
        logger.info("Copy to STM. CMD: %s" % cmd)
        os.system(cmd)
    return file_path_at_stm


def bug_handler_wrapper(stm_engine, conf_path_at_stm, redmine_project,
                        branch, sanitizer_file_name, yaml_parsed_file):
    """
    call bug handler on sanitizer file and return results as dictionary
    :param stm_engine: ssh engine to STM
    :param conf_path_at_stm: bug handler cfg file path at STM
    :param redmine_project: i.e SONiC-Design
    :param branch: i.e 202205
    :param sanitizer_file_name: i.e, 2023-04-02_16-35-19_wjhd-asan.log.22
    :param yaml_parsed_file: i.e, 2023-04-02_16-35-19_wjhd-asan.log.22.yaml
    :return: dictionary with bug handler results,
    i.e,
    {'file_name': '2022-06-21_23-24-07_orchagent-asan.log.40',
    'messages': ['INFO:handle_bug:reading configuration from', ...],
    'rc': 0,
    'decision': 'update',
    'recommended_action': "Bug handler updated an existing bug, no additional action needed"}
    """
    bug_handler_cmd = f"sudo -E {BugHandlerConst.BUG_HANDLER_PYTHON_PATH} {BugHandlerConst.BUG_HANDLER_SCRIPT} " \
                      f"--cfg {conf_path_at_stm} --project {redmine_project} " \
                      f"--user {BugHandlerConst.BUG_HANDLER_SANITIZER_USER} --branch {branch} " \
                      f"--debug_level 2 --parsed_data {yaml_parsed_file}"
    logger.info(f"Running Bug Handler CMD: {bug_handler_cmd}")
    bug_handler_output = stm_engine.run_cmd(bug_handler_cmd)
    bug_handler_messages, bug_handler_rc, bug_handler_decision, recommended_action = \
        parse_bug_handler_output(bug_handler_output)
    bug_handler_sanitizer_file_result = dict()
    bug_handler_sanitizer_file_result["file_name"] = sanitizer_file_name
    bug_handler_sanitizer_file_result["messages"] = bug_handler_messages
    bug_handler_sanitizer_file_result["rc"] = bug_handler_rc
    bug_handler_sanitizer_file_result["decision"] = bug_handler_decision
    bug_handler_sanitizer_file_result["recommended_action"] = recommended_action
    return bug_handler_sanitizer_file_result


def parse_bug_handler_output(bug_handler_output):
    json_output = json.loads(bug_handler_output)
    bug_handler_messages = json_output["messages"]
    messages = "\n".join(bug_handler_messages)
    bug_handler_rc = json_output["rc"]
    bug_handler_decision = parse_bug_handler_messages(bug_handler_rc, messages)
    recommended_action = get_recommended_action_for_user(bug_handler_rc, bug_handler_decision, messages)
    logger.info(f"Bug Handler RC: {bug_handler_rc}")
    logger.info(f"Bug Handler Decision: {bug_handler_decision}")
    return bug_handler_messages, bug_handler_rc, bug_handler_decision, recommended_action


def parse_bug_handler_messages(bug_handler_rc, bug_handler_messages):
    if bug_handler_rc == InfraConst.RC_SUCCESS:
        decision = re.search(r"decision:\s*(.*)", bug_handler_messages, re.IGNORECASE)
        action_res = re.search(r"bug action:\s*(.*)", bug_handler_messages, re.IGNORECASE)
        if decision:
            bug_handler_decision = decision.group(1)
        if action_res:
            action = action_res.group(1)
            if action == BugHandlerConst.BUG_HANDLER_DECISION_REOPEN:
                bug_handler_decision = BugHandlerConst.BUG_HANDLER_DECISION_REOPEN
    elif bug_handler_rc == BugHandlerConst.RC_ABORT:
        bug_handler_decision = BugHandlerConst.BUG_HANDLER_DECISION_ABORT
    else:
        bug_handler_decision = "not found"
    return bug_handler_decision


def get_recommended_action_for_user(bug_handler_rc, bug_handler_decision, bug_handler_messages):
    recommended_action = "Unknown scenario, please debug bug handler output."
    if bug_handler_decision == BugHandlerConst.BUG_HANDLER_DECISION_UPDATE:
        recommended_action = "Bug handler updated an existing bug, no additional action needed"
    elif bug_handler_decision == BugHandlerConst.BUG_HANDLER_DECISION_CREATE:
        bug_id = get_created_bug_id(bug_handler_messages)
        recommended_action = f"Bug handler had created a new bug for this issue,<br>" \
                             f" Please review ticket and update missing info.<br>" \
                             f"Bug id: {bug_id}."
    elif bug_handler_decision == BugHandlerConst.BUG_HANDLER_DECISION_ABORT:
        recommended_action = f"Bug handler could not compare signature in sanitizer log.<br>" \
                             f"1. If sanitizer log is missing traceback, update sanitizer tool owner.<br>" \
                             f"2. If sanitizer log does not missing traceback, <br>" \
                             f"update bug handler owner team that bug handler " \
                             f"could not parse sanitizer output correctly.<br>" \
                             f"3. Open bug manually for this leak, if an open issue does not exist."
    elif bug_handler_decision == BugHandlerConst.BUG_HANDLER_DECISION_REOPEN:
        recommended_action = "Bug handler had changed the status of an existing bug from fixed/closed to assigned.<br>" \
                             "Review the bug and alert the bug owner that fix is not working or merged."
    elif bug_handler_rc is not InfraConst.RC_SUCCESS:
        recommended_action = f"Bug handler had failed, please review bug handler output.<br>" \
                             f"1. If needed, consult with bug handler owner team about reason for failure.<br>" \
                             f"2. Rerun bug handler after fix or review sanitizer leak manually."
    return recommended_action


def get_created_bug_id(bug_handler_messages):
    bug_id = "could not find bug id in bug handler output, please review regex pattern"
    result = re.search(r"\[INFO\] created bug with id=(\d+)", bug_handler_messages)
    if result:
        bug_id = result.group(1)
    return bug_id


def create_summary_html_report(session_id, setup_name, dumps_folder, sanitizer_dumps_info):
    bug_handler_summary_template = get_xml_template('bug_handler_summary_template.j2')
    bug_handler_summary_output = bug_handler_summary_template.render(session_id=session_id,
                                                                     setup_name=setup_name,
                                                                     dumps_folder=dumps_folder,
                                                                     sanitizer_dumps_info=sanitizer_dumps_info)
    bug_handler_summary_path = os.path.join(dumps_folder, f"bug_handler_summary_report_session_{session_id}.html")
    f = open(bug_handler_summary_path, "w+")
    f.write(bug_handler_summary_output)
    f.close()
    return bug_handler_summary_path


def get_xml_template(template_name):
    p = Path(__file__).parent
    file_loader = FileSystemLoader(str(p))
    env = Environment(loader=file_loader)
    env.trim_blocks = True
    env.lstrip_blocks = True
    env.rstrip_blocks = True
    template = env.get_template(template_name)
    return template


def review_bug_handler_results(bug_handler_results):
    for dump_info in bug_handler_results:
        for bug_handler_result in dump_info["results"]:
            if bug_handler_result["decision"] != BugHandlerConst.BUG_HANDLER_DECISION_UPDATE\
                    or bug_handler_result["rc"] != InfraConst.RC_SUCCESS:
                raise AssertionError("Bug handler found undetected issues, please review summary attached to allure")
