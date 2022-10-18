import logging
from ngts.nvos_constants.constants_nvos import OpenApiReqType
from ngts.nvos_tools.infra.ResultObj import ResultObj
import json
import time
import allure
import requests
from requests.auth import HTTPBasicAuth
from retry import retry

logger = logging.getLogger()

ENDPOINT_URL_TEMPLATE = 'https://{ip}/nvue_v1'
REQ_HEADER = {"Content-Type": "application/json"}
INVALID_RESPONSE = ["ays_fail", "invalid"]


class RequestData:
    user_name = ''
    password = ''
    endpoint_ip = ''
    resource_path = ''
    param_name = None
    param_value = None

    def __init__(self, user_name, password, endpoint_ip, resource_path, param_name, param_value):
        self.user_name = user_name
        self.password = password
        self.endpoint_ip = endpoint_ip
        self.resource_path = resource_path
        self.param_name = param_name
        self.param_value = param_value


class OpenApiRequest:
    payload = {}
    changeset = None

    @staticmethod
    def print_request(r: requests.Request):
        output = "\n=======Request=======\nURL: {url}{body}\n=====================".format(url=r.url,
                                                                                           body="\nBody:\n" + json.dumps(r.body, indent=2) if r.body else "")
        logger.info(output)

    @staticmethod
    def print_response(r: requests.Response, req_type):
        response = json.dumps(r.json(), indent=2) if req_type == OpenApiReqType.PATCH else r.content
        output = "\n=======Response=======\n{}\n=====================".format(response)
        logger.info(output)

    @staticmethod
    def _get_endpoint_url(request_data):
        return ENDPOINT_URL_TEMPLATE.format(ip=request_data.endpoint_ip)

    @staticmethod
    def _get_http_auth(request_data):
        return HTTPBasicAuth(username=request_data.user_name, password=request_data.password)

    @staticmethod
    def create_nvue_changest(request_data):
        with allure.step("Create NVUE changeset"):
            r = requests.post(url=OpenApiRequest._get_endpoint_url(request_data) + "/revision",
                              auth=OpenApiRequest._get_http_auth(request_data), verify=False)
            OpenApiRequest.print_request(r.request)
            OpenApiRequest.print_response(r, OpenApiReqType.PATCH)
            response = r.json()
            OpenApiRequest.changeset = response.popitem()[0]

    @staticmethod
    def apply_nvue_changeset(request_data, add_approve=True):
        res = OpenApiRequest._send_patch_request(request_data)
        if res.result:
            res = OpenApiRequest._apply_config(request_data, add_approve)
        else:
            OpenApiRequest.changeset = None
            OpenApiRequest.payload = {}
        return res.info

    @staticmethod
    def _apply_config(request_data, add_approve):
        with allure.step("Apply NVUE changeset"):
            logging.info("Apply NVUE changeset")
            apply_payload = {"state": "apply", "auto-prompt": {"ays": "ays_yes"}} if add_approve else {"state": "apply"}
            url = '{url_endoint}/revision/{req_quote}'.format(url_endoint=OpenApiRequest._get_endpoint_url(request_data),
                                                              req_quote=requests.utils.quote(OpenApiRequest.changeset,
                                                                                             safe=""))
            r = requests.patch(url=url, auth=OpenApiRequest._get_http_auth(request_data), verify=False,
                               data=json.dumps(apply_payload), headers=REQ_HEADER)
            OpenApiRequest.print_request(r.request)
            OpenApiRequest.print_response(r, OpenApiReqType.PATCH)
            OpenApiRequest._validate_response(r, OpenApiReqType.PATCH)

            try:
                result = OpenApiRequest._check_apply_status(request_data, OpenApiRequest.changeset)
                if result.result:
                    result.info = "Configuration applied successfully"
            except Exception:
                result.info = "Error: Failed to apply configuration"
            finally:
                OpenApiRequest.changeset = None
                OpenApiRequest.payload = {}
                return result

    @staticmethod
    @retry(Exception, tries=5, delay=10)
    def _check_apply_status(request_data, changeset):
        with allure.step("Check the status of the apply"):
            logging.info("Check the status of the apply")
            req_url = '{url_endoint}/revision/{req_quote}'.format(
                url_endoint=OpenApiRequest._get_endpoint_url(request_data),
                req_quote=requests.utils.quote(changeset, safe=""))
            r = requests.get(url=req_url, verify=False, auth=OpenApiRequest._get_http_auth(request_data))
            OpenApiRequest.print_response(r, OpenApiReqType.GET)

            res = OpenApiRequest._validate_response(r, OpenApiReqType.GET)
            if not res.result:
                return res.info

            obj = json.loads(r.content)

            if "state" in obj.keys():
                if obj["state"] == "applied":
                    return ResultObj(True, "Configuration applied successfully")
                '''if obj["state"] == "ays" and obj["transition"]["progress"] == "Are you sure?":
                    OpenApiRequest.apply_nvue_changeset(request_data, changeset, True)
                    raise Exception("Waiting for configuration to be applied")'''
                if obj["state"] in INVALID_RESPONSE:
                    msg = obj["transition"]["issue"]["0"]["message"]
                    return ResultObj(False, "Error: Failed to apply configuration. Reason: " + msg)
                else:
                    raise Exception("Waiting for configuration to be applied")

    @staticmethod
    def _create_json_payload(request_data):
        temp_comp = {}
        if request_data.param_name:
            temp_comp[request_data.param_name] = request_data.param_value
        else:
            temp_comp = None

        split_path = list(filter(None, request_data.resource_path.split('/')))
        if request_data.param_name in split_path:
            split_path.remove(request_data.param_name)

        if len(split_path) < 1:
            assert "Invalid resource path: " + request_data.resource_path

        OpenApiRequest.payload = OpenApiRequest._update_payload(temp_comp, split_path, OpenApiRequest.payload)

    @staticmethod
    def _update_payload(last_component, path, payload):
        if path and (path[0] in payload.keys()):
            temp_comp_name = path.pop(0).strip()
            payload[temp_comp_name] = OpenApiRequest._update_payload(last_component, path, payload[temp_comp_name])
        elif path:
            payload.update(OpenApiRequest._create_partial_payload(last_component, path))
        return payload

    @staticmethod
    def _create_partial_payload(last_component, path):
        temp_comp = {}
        if len(path) > 1:
            temp_comp_name = path.pop(0).strip()
            temp_comp[temp_comp_name] = OpenApiRequest._create_partial_payload(last_component, path)
        else:
            temp_comp[path[0]] = last_component
        return temp_comp

    @staticmethod
    def _validate_response(r: requests.Response, req_type):
        if req_type == OpenApiReqType.PATCH:
            response = r.json()
        else:
            response = json.loads(r.content)
        if 'title' in response.keys() and response['title'] == "Bad Request":
            return ResultObj(False, "Error: Request failed. Details: " + response['detail'])
        return ResultObj(True, "")

    @staticmethod
    def add_to_path_request(request_data, op_params=''):
        with allure.step("Add data to patch request"):
            OpenApiRequest._create_json_payload(request_data)

    @staticmethod
    def _send_patch_request(request_data):
        with allure.step('Send PATCH request'):

            logging.info("Create NVUE changeset")
            OpenApiRequest.create_nvue_changest(request_data)
            logging.info("Using NVUE Changeset: '{}'".format(OpenApiRequest.changeset))

            query_string = {"rev": OpenApiRequest.changeset}
            logging.info("Send patch request")
            r = requests.patch(url=OpenApiRequest._get_endpoint_url(request_data) + "/",
                               auth=OpenApiRequest._get_http_auth(request_data),
                               verify=False,
                               data=json.dumps(OpenApiRequest.payload),
                               params=query_string,
                               headers=REQ_HEADER)
            OpenApiRequest.print_request(r.request)
            OpenApiRequest.print_response(r, OpenApiReqType.PATCH)

            res = OpenApiRequest._validate_response(r, OpenApiReqType.PATCH)
            return res

    @staticmethod
    def send_get_request(request_data, op_params=''):
        with allure.step('Send GET request'):
            logging.info("Send GET request")
            req_url = '{url}{resource_path}{params}'.format(url=OpenApiRequest._get_endpoint_url(request_data),
                                                            params="/" + op_params if op_params else '',
                                                            resource_path=request_data.resource_path)
            r = requests.get(url=req_url, verify=False, auth=OpenApiRequest._get_http_auth(request_data))
            OpenApiRequest.print_request(r.request)
            OpenApiRequest.print_response(r, OpenApiReqType.GET)

            res = OpenApiRequest._validate_response(r, OpenApiReqType.GET)
            if not res.result:
                return res.info
            return r.content.decode('utf8')

    @staticmethod
    def send_delete_request(request_data, op_params=''):
        with allure.step('Send DELETE request'):
            logging.info("Send DELETE request")
            return OpenApiRequest.add_to_path_request(request_data, op_params)

    @staticmethod
    def send_action_request(request_data, resource_path):
        with allure.step("Send POST request"):
            logging.info("Send POST request")
            req_url = '{url}{resource_path}'.format(url=OpenApiRequest._get_endpoint_url(request_data),
                                                    resource_path=request_data.resource_path)

            OpenApiRequest.payload = {request_data.param_name: request_data.param_value}

            r = requests.post(url=req_url,
                              auth=OpenApiRequest._get_http_auth(request_data), verify=False,
                              data=json.dumps(OpenApiRequest.payload),
                              headers=REQ_HEADER)
            OpenApiRequest.print_request(r.request)
            response = json.dumps(r.json(), indent=2)
            if response.isnumeric():
                rev = response
            else:
                response = r.json()
                assert "title" not in response, response['detail']

        with allure.step("Send GET request"):
            logging.info("Send GET request")
            OpenApiRequest._send_get_req_and_wait_till_completed(request_data, rev)

    @staticmethod
    def _send_get_req_and_wait_till_completed(request_data, rev):

        logging.info("Send GET request")
        action_success = False
        info = ""
        timeout = 360
        req_url = OpenApiRequest._get_endpoint_url(request_data) + "/action/" + rev
        auth = OpenApiRequest._get_http_auth(request_data)

        while timeout > 0:
            r = requests.get(url=req_url, verify=False, auth=auth)
            OpenApiRequest.print_request(r.request)
            OpenApiRequest.print_response(r, OpenApiReqType.GET)
            response = json.loads(r.content)
            if response['state'] == "action_success":
                action_success = True
                break
            elif response['state'] and response['state'] != "running" and response['state'] != "start":
                info = response["status"] + " - issue: " + response["issue"]
            time.sleep(10)
        assert action_success, info


class OpenApiCommandHelper:

    req_method = {OpenApiReqType.GET: OpenApiRequest.send_get_request,
                  OpenApiReqType.PATCH: OpenApiRequest.add_to_path_request,
                  OpenApiReqType.DELETE: OpenApiRequest.send_delete_request,
                  OpenApiReqType.ACTION: OpenApiRequest.send_action_request}

    @staticmethod
    def execute_script(user_name, password, req_type, dut_ip, resource_path, op_param_name='', op_param_value=''):
        request_data = RequestData(user_name, password, dut_ip, resource_path, op_param_name, op_param_value)

        if req_type == OpenApiReqType.APPLY:
            return OpenApiRequest.apply_nvue_changeset(request_data)

        return OpenApiCommandHelper.req_method[req_type](request_data, op_param_name)

    @staticmethod
    def execute_action(action_type, user_name, password, dut_ip, resource_path, params):
        request_data = RequestData(user_name, password, dut_ip, resource_path.strip(), action_type, params)
        return OpenApiCommandHelper.req_method[OpenApiReqType.ACTION](request_data, resource_path)
