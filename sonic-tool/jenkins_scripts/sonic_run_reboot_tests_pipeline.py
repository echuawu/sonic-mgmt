import os
import sys
import argparse
import json
import logging

workspace_dir = os.environ['WORKSPACE']
sys.path.append(os.path.join(workspace_dir, 'sonic-mgmt'))
from ngts.tools.mars_test_cases_results.Connect_to_MSSQL import ConnectMSSQL
from ngts.constants.constants import DbConstants, CliType


logger = logging.getLogger(__name__)

# Get env variables
fast_reboot_executors = os.environ.get('fast_reboot_executors')
fast_reboot_iterations_number = os.environ['fast_reboot_iterations_number']
warm_reboot_executors = os.environ.get('warm_reboot_executors')
warm_reboot_iterations_number = os.environ['warm_reboot_iterations_number']
base_version = os.environ['base_version']
target_version = os.environ.get('target_version')

f_reboot_setups_list = []
if fast_reboot_executors:
    f_reboot_setups_list = fast_reboot_executors.split(',')
w_reboot_setups_list = []
if warm_reboot_executors:
    w_reboot_setups_list = warm_reboot_executors.split(',')
tests_results_file_path = os.path.join(workspace_dir, 'results.json')
email_report_file_path = os.path.join(workspace_dir, 'email_report.html')


DB_FILE_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<DBDEF>
<global>
    <default_params_type> basic_setup_step_params </default_params_type>
    <DB>
        <info> {test_name} </info>
        <owner> SONiC </owner>
        <group> SONiC </group>
        <pre></pre>
        <post></post>
    </DB>
    <Test>
    </Test>
    <Case>
    </Case>
</global>
<test>
    <cases> sonic-mgmt/{test_type}_reboot.cases </cases>
</test>
</DBDEF>

'''


CASES_FILE_HEADER_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<CASEDEF>
    <global>
        <Test>
            <info> {test_name} Test </info>
            <name> {test_name} </name>
            <owner> </owner>
        </Test>
        <Case>
            <wrapper> [[run_time:db_tests_path]]/sonic-mgmt/sonic-tool/mars/scripts/community_mars_pytest_runner.py  </wrapper>
            <tout> 86400 </tout>
        </Case>
    </global>
'''

CASES_FILE_REBOOT_TESTCASE_TEMPLATE = '''<case>
    <info> {test_name} Case </info>
    <name> {test_name} </name>
    <tout> 3600 </tout>
    <cmd>
         <params>
             <static_args> --sonic-mgmt-dir /root/mars/workspace/[[conf:extra_info.sonic_mgmt_repo_name]] --dut-name [[conf:extra_info.dut_name]] --sonic-topo [[conf:extra_info.topology]] --json-root-dir [[conf:extra_info.json_root_dir]] --raw-options "\\\'--log-cli-level debug  --show-capture=no -ra --showlocals  --clean-alluredir --alluredir=/tmp/allure-results --allure_server_project_id=\\\"\\\" --allure_server_addr=\\\"10.215.11.120\\\"\\\'" --test-scripts platform_tests/test_advanced_reboot.py::test_{test_type}_reboot </static_args>
         </params>
    </cmd>
</case>
'''

CASES_FILE_REBOOT_WITH_UPGRADE_TESTCASE_TEMPLATE = '''<case>
    <info> {test_name} Case </info>
    <name> {test_name} </name>
    <tout> 3600 </tout>
    <cmd>
         <params>
             <static_args> --sonic-mgmt-dir /root/mars/workspace/[[conf:extra_info.sonic_mgmt_repo_name]] --dut-name [[conf:extra_info.dut_name]] --sonic-topo [[conf:extra_info.topology]] --json-root-dir [[conf:extra_info.json_root_dir]] --raw-options "\\\'--log-cli-level debug  --show-capture=no -ra --showlocals --upgrade_type={test_type} --base_image_list={base_versions_list} --target_image_list={target_version} --clean-alluredir --alluredir=/tmp/allure-results --allure_server_project_id=\\\"\\\" --allure_server_addr=\\\"10.215.11.120\\\"\\\'" --test-scripts upgrade_path/test_upgrade_path.py::test_upgrade_path </static_args>
         </params>
    </cmd>
</case>
'''

CASES_FILE_END_LINE_TEMPLATE = '''
</CASEDEF>

'''


def prepare_db_files(reboot_types_list, is_upgrade_test=False):
    """
    Prepare DB files and store them into sonic-mgmt folder
    """
    for r_type in reboot_types_list:
        test_name = '{} Reboot'.format(r_type.upper())
        if is_upgrade_test:
            test_name = test_name + ' with Upgrade'

        db_file_name = '{}_reboot.db'.format(r_type)
        sonic_mgmt_path = os.path.dirname(os.path.abspath(__file__)).split('sonic-tool')[0]
        db_file_path = os.path.join(sonic_mgmt_path, db_file_name)
        with open(db_file_path, 'w') as file:
            file_data = DB_FILE_TEMPLATE.format(test_name=test_name, test_type=r_type)
            file.write(file_data)


def prepare_cases_files(reboot_type_iterations_dict, base_ver_list=None, target_ver=None):
    """
    Prepare CASES files and store them into sonic-mgmt folder
    """
    for r_type, iterations_number in reboot_type_iterations_dict.items():
        test_name = '{} Reboot'.format(r_type.upper())
        if base_ver_list and target_ver:
            test_name = test_name + ' with Upgrade'

        cases_file_name = '{}_reboot.cases'.format(r_type)
        file_data = CASES_FILE_HEADER_TEMPLATE.format(test_name=test_name)
        for _ in range(iterations_number):
            if base_ver_list and target_ver:
                file_data += CASES_FILE_REBOOT_WITH_UPGRADE_TESTCASE_TEMPLATE.format(test_name=test_name,
                                                                                     test_type=r_type,
                                                                                     base_versions_list=base_ver_list,
                                                                                     target_version=target_ver)
            else:
                file_data += CASES_FILE_REBOOT_TESTCASE_TEMPLATE.format(test_name=test_name, test_type=r_type)
        file_data += CASES_FILE_END_LINE_TEMPLATE

        sonic_mgmt_path = os.path.dirname(os.path.abspath(__file__)).split('sonic-tool')[0]
        cases_file_path = os.path.join(sonic_mgmt_path, cases_file_name)
        with open(cases_file_path, 'w') as file:
            file.write(file_data)


def do_preparation_steps():
    """
    Prepare DB and CASES files and store them into sonic-mgmt folder
    """
    reboot_types_list = []
    reboot_type_iterations_dict = {}

    if fast_reboot_executors:
        reboot_types_list.append('fast')
        reboot_type_iterations_dict['fast'] = int(fast_reboot_iterations_number)
    if warm_reboot_executors:
        reboot_types_list.append('warm')
        reboot_type_iterations_dict['warm'] = int(warm_reboot_iterations_number)

    if not reboot_types_list:
        raise Exception('Looks like setups which will run fast/warm reboot tests did not provided.'
                        'Please specify setups which will run fast/warm reboot tests.')

    is_upgrade_test = True if target_version else False
    prepare_db_files(reboot_types_list, is_upgrade_test)
    prepare_cases_files(reboot_type_iterations_dict, base_ver_list=base_version, target_ver=target_version)


def build_summary_report(results):
    """
    Build report email summary table
    """
    email_body = '<table style="border-collapse: collapse; width: 100%; height: 36px;" border="1">' \
                 '<tbody>' \
                 '<tr style="height: 18px; background-color: #777; color: white; font-weight: bold;">' \
                 '<td style="width: 10%;">Setup Name</td>' \
                 '<td style="width: 15%;">HwSKU</td>' \
                 '<td style="width: 5%;">Number of ports</td>' \
                 '<td style="width: 5%;">Reboot Type</td>' \
                 '<td style="width: 5%;">Total Iterations</td>' \
                 '<td style="width: 15%;">Base Version</td>' \
                 '<td style="width: 15%;">Target Version</td>' \
                 '<td style="width: 5%;">Average Dataplane Loss</td>' \
                 '<td style="width: 5%;">Average Controlplane Loss</td>' \
                 '<td style="width: 10%;">Tests Status</td>' \
                 '</tr>'

    for setup_name, setup_data in results.items():
        test_name = setup_data['reboot_type']
        hwsku = setup_data['extra_data']['hwsku']
        total_iterations = len(setup_data['data'])
        base_ver = setup_data['base_ver']
        target_ver = setup_data['target_ver']
        dataplane_downtime_list = [i['dataplane_downtime'] for i in setup_data['data']]
        controlplane_downtime_list = [i['controlplane_downtime'] for i in setup_data['data']]
        average_dataplane_loss = sum(dataplane_downtime_list) / len(dataplane_downtime_list)
        average_controlplane_loss = sum(controlplane_downtime_list) / len(controlplane_downtime_list)

        test_statuses_list = [i['test_status'] for i in setup_data['data']]
        passed_tests_num = test_statuses_list.count('passed')
        failed_tests_num = len(test_statuses_list) - passed_tests_num
        tests_status = '<span style="font-size:14px; color: green">Passed: {},</span> ' \
                       '<span style="font-size:14px; color: red">Failed: {}</span>'.format(passed_tests_num,
                                                                                           failed_tests_num)

        total_ports_num = setup_data['extra_data']['total_ports']
        active_ports_num = setup_data['extra_data']['active_ports']
        ports = 'Total: {}, Active: {}'.format(total_ports_num, active_ports_num)

        setup_data = '<tr style="height: 18px;">' \
                     '<td style="width: 10%; height: 18px;">{}</td>' \
                     '<td style="width: 15%; height: 18px;">{}</td>' \
                     '<td style="width: 5%; height: 18px;">{}</td>' \
                     '<td style="width: 5%; height: 18px;">{}</td>' \
                     '<td style="width: 5%; height: 18px;">{}</td>' \
                     '<td style="width: 15%; height: 18px;">{}</td>' \
                     '<td style="width: 15%; height: 18px;">{}</td>' \
                     '<td style="width: 5%; height: 18px;">{}</td>' \
                     '<td style="width: 5%; height: 18px;">{}</td>' \
                     '<td style="width: 10%; height: 18px;">{}</td>' \
                     '</tr>'.format(setup_name, hwsku, ports, test_name, total_iterations, base_ver, target_ver,
                                    average_dataplane_loss, average_controlplane_loss, tests_status)

        email_body += setup_data

    email_body += '</tbody>' \
                  '</table>'

    return email_body


def build_setup_report(setup_name, results):
    """
    Build report email table for specific setup
    """
    email_body = '<table style="border-collapse: collapse; width: 100%; height: 36px;" border="1">' \
                 '<tbody>' \
                 '<tr style="height: 18px; background-color: #777; color: white; font-weight: bold;">' \
                 '<td style="width: 5%;">Iteration Number</td>' \
                 '<td style="width: 5%;">Reboot Type</td>' \
                 '<td style="width: 15%;">Base Version</td>' \
                 '<td style="width: 15%;">Target Version</td>' \
                 '<td style="width: 5%;">Test Status</td>' \
                 '<td style="width: 10%;">Dataplane Loss</td>' \
                 '<td style="width: 10%;">Controlplane Loss</td>' \
                 '<td style="width: 20%;">Allure Report URL</td>' \
                 '</tr>'

    iteration_number = 1
    for run in results[setup_name]['data']:
        test_name = results[setup_name]['reboot_type']
        base_ver = results[setup_name]['base_ver']
        target_ver = results[setup_name]['target_ver']
        dataplane_downtime = run['dataplane_downtime']
        controlplane_downtime = run['controlplane_downtime']
        allure_report_url = run['allure']
        test_status = run['test_status']
        color = 'green' if test_status == 'passed' else 'red'

        iteration_data = '<tr style="height: 18px;">' \
                         '<td style="width: 5%; height: 18px;">{}</td>' \
                         '<td style="width: 5%; height: 18px;">{}</td>' \
                         '<td style="width: 15%; height: 18px;">{}</td>' \
                         '<td style="width: 15%; height: 18px;">{}</td>' \
                         '<td style="width: 5%; height: 18px; color: {}">{}</td>' \
                         '<td style="width: 10%; height: 18px;">{}</td>' \
                         '<td style="width: 10%; height: 18px;">{}</td>' \
                         '<td style="width: 20%; height: 18px;">{}</td>' \
                         '</tr>'.format(iteration_number, test_name, base_ver, target_ver, color, test_status,
                                        dataplane_downtime, controlplane_downtime, allure_report_url)

        email_body += iteration_data
        iteration_number += 1

    email_body += '</tbody>' \
                  '</table>'

    return email_body


def parse_args():
    """
    Parse script arguments
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('--do_preparation', dest='do_preparation', action='store_true',
                        help='Generate MARS CASES and DB files')
    parser.add_argument('--session_id', dest='session_id', help='MARS session ID')
    parser.add_argument('--setup_name', dest='setup_name', help='MARS setup name')
    parser.add_argument('--generate_report_email', dest='generate_report_email', action='store_true',
                        help='Provide this arg if want to generate report email')

    return parser.parse_args()


def get_tests_results_dict():
    """
    Get dictionary with tests results(read from file if exist or create new)
    """
    results_dict = {}

    if os.path.exists(tests_results_file_path):
        with open(tests_results_file_path) as data:
            results_dict = json.load(data)

    return results_dict


def get_sql_db_connection():
    """
    Get connection to SQL database
    """
    connections_params = DbConstants.CREDENTIALS[CliType.SONIC]
    sql_connection_obj = ConnectMSSQL(connections_params['server'], connections_params['database'],
                                      connections_params['username'], connections_params['password'])
    sql_connection_obj.connect_db()
    return sql_connection_obj


def get_executed_tests_data_during_mars_session(sql_connection_obj, session_id):
    """
    Get executed tests data during specific MARS session ID
    """
    test_ids_reports_dict = {}
    # Get all executed tests during MARS session: mars_key_id, tests status and allure reports
    query_get = "SELECT mars_key_id,allure_url,mars_result FROM mars_respond WHERE session_id='{}'".format(session_id)
    try:
        sql_connection_obj.cursor.execute(query_get)
        results = sql_connection_obj.cursor.fetchall()
        for item in results:
            mars_key_id = item[0]
            allure_url = item[1]
            test_status = item[2]
            test_ids_reports_dict[mars_key_id] = {'allure': allure_url, 'test_status': test_status}
    except Exception as err:
        logger.error('Got exception during getting data from SQL. Error: {}'.format(err))
    return test_ids_reports_dict


def get_image_ver_and_update_test_data_by_test_run_info(sql_connection_obj, session_id, mars_key_id, test_data):
    # Get test run time and test run id
    query_get = "SELECT test_run_dateTime,test_run_id,DUTImageVersion FROM tests_runs WHERE MarsSessionId='{}' AND MarsKeyId='{}'".format(
        session_id, mars_key_id)
    image_version = 'Unable to get image version'
    try:
        sql_connection_obj.cursor.execute(query_get)
        date, test_run_id, image_version = sql_connection_obj.cursor.fetchone()
        test_data.update({'date': date, 'test_run_id': test_run_id})
    except Exception as err:
        logger.error('Got exception during getting data from SQL. Error: {}'.format(err))

    return image_version


def update_test_data_with_traffic_loss_info(sql_connection_obj, test_data):
    # Get data/control plane loss
    query_get = "SELECT test_attribute,test_attribute_value FROM test_data WHERE test_run_id='{}'".format(
        test_data.get('test_run_id'))
    try:
        sql_connection_obj.cursor.execute(query_get)
        for data in sql_connection_obj.cursor.fetchall():
            key, value = data
            test_data[key] = value
    except Exception as err:
        logger.error('Got exception during getting data from SQL. Error: {}'.format(err))


def update_results_with_setup_extra_data(sql_connection_obj, test_run_id, results_dict):
    query_get = "SELECT SetupExtraInfo FROM rel_test_run_setup WHERE test_run_id='{}'".format(test_run_id)
    try:
        sql_connection_obj.cursor.execute(query_get)
        extra_data = sql_connection_obj.cursor.fetchone()[0]
        results_dict[setup_name]['extra_data'] = json.loads(extra_data)
    except Exception as err:
        logger.error('Got exception during getting data from SQL. Error: {}'.format(err))


def update_sonic_version_info_from_readme_file(setup_name, results_dict):
    versions_list = base_version.split(',')
    versions_list.append(target_version)
    base_ver_list = []
    target_ver = ''

    for version in versions_list:
        # Example: /auto/sw_system_release/sonic/202205.53-84fc3ec7a_Internal/Mellanox/sonic-mellanox.bin
        readme_path = version.split('Mellanox')[0] + 'README'
        if os.path.exists(readme_path):
            with open(readme_path) as ver_data_obj:
                ver_data_lines = ver_data_obj.readlines()
                for line in ver_data_lines:
                    if line.startswith('VERSION_NAME:'):
                        sonic_ver = line.split()[1]  # VERSION_NAME: 202205.53-84fc3ec7a_Internal
                        if versions_list[-1] == version:
                            target_ver = sonic_ver
                        else:
                            base_ver_list.append(sonic_ver)

    results_dict[setup_name]['base_ver'] = ','.join(base_ver_list)
    results_dict[setup_name]['target_ver'] = target_ver


def update_reboot_type_for_setup(setup_name, results_dict):
    """
    Update reboot type in results_dict for specific setup
    """
    reboot_type = 'fast' if setup_name in f_reboot_setups_list else 'warm'
    results_dict[setup_name]['reboot_type'] = reboot_type


def update_test_case_data_results(setup_name, test_ids_reports_dict, results_dict):
    """
    Update results_dict with tests results from test_ids_reports_dict dict
    """
    tests_data_list = []
    for mars_test_key, test_data in test_ids_reports_dict.items():
        data = {'dataplane_downtime': test_data['dataplane'], 'controlplane_downtime': test_data['controlplane'],
                'test_status': test_data['test_status'], 'allure': test_data['allure'], 'date': test_data['date']}
        tests_data_list.append(data)

    # Sort tests list by execution date
    tests_data_list_sorted = sorted(tests_data_list, key=lambda d: d['date'])
    results_dict[setup_name]['data'] = tests_data_list_sorted


def get_results_for_session(session_id, setup_name):
    """
    Generate JSON report file which can be used for generate email report
    """
    sql_connection_obj = get_sql_db_connection()
    results_dict = get_tests_results_dict()
    results_dict[setup_name] = {}

    test_ids_reports_dict = get_executed_tests_data_during_mars_session(sql_connection_obj, session_id)

    # Get data/control plane loss for specific test cases
    for mars_key_id in test_ids_reports_dict:
        test_data = {}
        image_version = get_image_ver_and_update_test_data_by_test_run_info(sql_connection_obj, session_id,
                                                                            mars_key_id, test_data)

        update_test_data_with_traffic_loss_info(sql_connection_obj, test_data)

        # Update HwSKU, total/active ports, image version only one time
        if not results_dict[setup_name].get('base_ver') or not results_dict[setup_name].get('extra_data'):
            results_dict[setup_name]['base_ver'] = image_version
            test_run_id = test_data.get('test_run_id')
            update_results_with_setup_extra_data(sql_connection_obj, test_run_id, results_dict)

        # Update results for test iteration
        test_ids_reports_dict[mars_key_id].update(test_data)

    results_dict[setup_name]['target_ver'] = ''
    if target_version:  # If upgrade - get base/target images version from README file
        update_sonic_version_info_from_readme_file(setup_name, results_dict)

    update_reboot_type_for_setup(setup_name, results_dict)

    update_test_case_data_results(setup_name, test_ids_reports_dict, results_dict)

    with open(tests_results_file_path, 'w') as data_file_obj:
        json.dump(results_dict, data_file_obj, default=str)


def generate_email_report_html():
    """
    Generate email HTML report which can be send to users
    """
    email_body = ''
    email_header = '<p style="font-size:14px">Hi All,</p>' \
                   '<p style="font-size:14px">Please see below the results of the reboot tests execution</p>'
    email_body += email_header

    try:
        with open(tests_results_file_path) as data_file_obj:
            results = json.load(data_file_obj)

        email_body += build_summary_report(results)
        email_body += '<br>'

        for setup_name in results:
            email_body += '<p style="font-size:14px"> <b>Setup name: {} </b></p>'.format(setup_name)
            email_body += build_setup_report(setup_name, results)
            email_body += '<br>'
    except Exception as err:
        email_body += '<p style="font-size:14px">Error happen during build report email. ' \
                      'Please check Jenkins job logs. <br> Python traceback: {} </p>'.format(err)

    with open(email_report_file_path, 'w') as report:
        report.write(email_body)


if __name__ == "__main__":

    args = parse_args()

    do_preparation = args.do_preparation
    session_id = args.session_id
    setup_name = args.setup_name
    generate_report_email = args.generate_report_email

    if len(f_reboot_setups_list + w_reboot_setups_list) != len(set(f_reboot_setups_list + w_reboot_setups_list)):
        raise Exception('Single setup can run only one test type: fast or warm but not both. '
                        'Please choose correct setups for specific reboot type in Jenkins')

    if do_preparation:  # generate db and cases files
        do_preparation_steps()
    elif session_id:  # collect results for session
        get_results_for_session(session_id, setup_name)
    elif generate_report_email:  # generate email report
        generate_email_report_html()
    else:
        raise Exception('Please provide correct script run arguments')
