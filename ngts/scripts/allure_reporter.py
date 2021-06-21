import os
import sys
import requests
import json
import base64
import argparse
import logging

path = os.path.abspath(__file__)
sonic_mgmt_path = path.split('/ngts/')[0]
sys.path.append(sonic_mgmt_path)

from ngts.constants.constants import InfraConst
from infra.tools.topology_tools.topology_setup_utils import get_topology_by_setup_name


ALLURE_DOCKER_SERVICE = 'allure-docker-service'


def get_logger():
    log = logging.getLogger('AllureReporter')
    log.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    return log


logger = get_logger()


def parse_args():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument("--action", required=True, dest="action", default="upload",
                        choices=["upload", "generate", "cleanup"], help="Action to do")
    parser.add_argument('--setup_name', dest='setup_name', help='Setup name')

    return parser.parse_args()


def upload_results(results_directory, allure_server, project_id):
    if os.path.exists(results_directory):
        create_project(allure_server, project_id)
        allure_report_items_list = collect_allure_results(results_directory)
        upload_data_to_server(allure_report_items_list, allure_server, project_id)


def create_project(allure_server_url, allure_project):
    data = {'id': allure_project}
    http_headers = {'Content-type': 'application/json'}
    url = allure_server_url + '/projects'

    if requests.get(url + '/' + allure_project).status_code != 200:
        logger.info('Creating project {} on allure server'.format(allure_project))
        response = requests.post(url, json=data, headers=http_headers)
        if response.raise_for_status():
            logger.error('Failed to create project on allure server, error: {}'.format(response.content))
    else:
        logger.info('Allure project {} already exist on server. No need to create project'.format(allure_project))


def collect_allure_results(allure_report_dir):
    allure_report_file_list = os.listdir(allure_report_dir)

    allure_report_items_list = []
    for allure_report_file_item in allure_report_file_list:
        report_item_dict = {}

        file_path = allure_report_dir + "/" + allure_report_file_item
        logger.info(file_path)

        if os.path.isfile(file_path):
            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                    if content.strip():
                        b64_content = base64.b64encode(content)
                        report_item_dict['file_name'] = allure_report_file_item
                        report_item_dict['content_base64'] = b64_content.decode('UTF-8')
                        allure_report_items_list.append(report_item_dict)
                    else:
                        logger.info('Empty File skipped: ' + file_path)
            finally:
                f.close()
        else:
            logger.info('Directory skipped: ' + file_path)

    return allure_report_items_list


def upload_data_to_server(allure_report_items_list, allure_server, project_id):
    headers = {'Content-type': 'application/json'}
    request_body = {
        "results": allure_report_items_list
    }
    json_request_body = json.dumps(request_body)

    ssl_verification = True

    logger.info("------------------SEND-RESULTS------------------")
    send_result_url = '{}/send-results?project_id={}'.format(allure_server, project_id)
    response = requests.post(send_result_url, headers=headers, data=json_request_body, verify=ssl_verification)
    logger.info("STATUS CODE:")
    logger.info(response.status_code)


def generate_report(allure_server_url, allure_project):
    response = requests.get('{}/generate-report?project_id={}'.format(allure_server_url, allure_project)).json()
    report_url = response['data']['report_url']
    logger.info('Allure report URL: {}'.format(report_url))

    cleanup_report(allure_server_url, allure_project)


def cleanup_report(allure_server_url, allure_project):
    requests.get('{}/clean-results?project_id={}'.format(allure_server_url, allure_project))


if __name__ == "__main__":
    args = parse_args()

    allure_report_dir = InfraConst.ALLURE_REPORT_DIR
    allure_server_addr = InfraConst.ALLURE_SERVER_URL
    setup_name = args.setup_name

    allure_project_id = setup_name.replace('_', '-')

    try:
        topology = get_topology_by_setup_name(setup_name, slow_cli=False)
        dut_name = topology.players['dut']['attributes'].noga_query_data['attributes']['Common']['Name']
        allure_project_id = dut_name
    except Exception as err:
        allure_project_id = setup_name

    allure_server_base_url = '{}/{}'.format(allure_server_addr, ALLURE_DOCKER_SERVICE)
    if args.action == 'upload':
        upload_results(allure_report_dir, allure_server_base_url, allure_project_id)
    if args.action == 'generate':
        generate_report(allure_server_base_url, allure_project_id)
    if args.action == 'cleanup':
        cleanup_report(allure_server_base_url, allure_project_id)
