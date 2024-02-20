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

ENDPOINT_URL_TEMPLATE = 'https://{ip}:{port_num}/nvue_v1'
REQ_HEADER = {"Content-Type": "application/json"}
INVALID_RESPONSE = ["ays_fail", "invalid", "Bad Request", "Not Found", "Forbidden", "Internal Server Error"]


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
    port_num = "443"

    @staticmethod
    def print_request(r: requests.Request):
        output = "\n=======Request=======\nURL: {url}{body}\n=====================".format(
            url=r.url, body="\nBody:\n" + json.dumps(r.body, indent=2) if r.body else "")
        logger.info(output)

    @staticmethod
    def print_response(r: requests.Response, req_type):
        response = json.dumps(r.json(), indent=2) if req_type == OpenApiReqType.PATCH else r.content
        output = "\n=======Response=======\n{}\n=====================".format(response)
        logger.info(output)

    @staticmethod
    def _get_endpoint_url(request_data):
        return ENDPOINT_URL_TEMPLATE.format(ip=request_data.endpoint_ip, port_num=OpenApiRequest.port_num)

    @staticmethod
    def _get_http_auth(request_data):
        return HTTPBasicAuth(username=request_data.user_name, password=request_data.password)

    @staticmethod
    def create_nvue_changest(request_data):
        req_type = 'POST'
        with allure.step(f"Send {req_type} request to create NVUE change-set"):
            logging.info(f"Send {req_type} request to create NVUE change-set")
            r = requests.post(url=OpenApiRequest._get_endpoint_url(request_data) + "/revision",
                              auth=OpenApiRequest._get_http_auth(request_data), verify=False)
            OpenApiRequest.print_request(r.request)
            OpenApiRequest.print_response(r, req_type)
            response = r.json()
            OpenApiRequest.changeset = response.popitem()[0]

            logging.info("Using NVUE change-set: '{}'".format(OpenApiRequest.changeset))

            return OpenApiRequest._validate_response(r, req_type)

    @staticmethod
    def clear_changeset_and_payload():
        OpenApiRequest.changeset = None
        OpenApiRequest.payload = {}

    @staticmethod
    def apply_nvue_changeset(request_data, op_param_name, add_approve=True):
        res = OpenApiRequest._apply_config(request_data, add_approve)
        OpenApiRequest.clear_changeset_and_payload()
        return res.info

    @staticmethod
    def _apply_config(request_data, add_approve):
        with allure.step("Apply NVUE change-set"):
            logging.info("Apply NVUE change-set")
            apply_payload = {"state": "apply", "auto-prompt": {"ays": "ays_yes"}} if add_approve else {"state": "apply"}
            url = '{url_end_point}/revision/{req_quote}'.format(
                url_end_point=OpenApiRequest._get_endpoint_url(request_data),
                req_quote=requests.utils.quote(OpenApiRequest.changeset, safe=""))
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
                result = ResultObj(False, "Error: Failed to apply configuration")
            finally:
                OpenApiRequest.changeset = None
                OpenApiRequest.payload = {}
                return result

    @staticmethod
    @retry(Exception, tries=5, delay=10)
    def _check_apply_status(request_data, changeset):
        with allure.step("Check the status of the apply"):
            logging.info("Check the status of the apply")
            req_url = '{url_endpoint}/revision/{req_quote}'.format(
                url_endpoint=OpenApiRequest._get_endpoint_url(request_data),
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
                if str(obj["state"]) in INVALID_RESPONSE:
                    logging.info("Apply state: " + str(obj["state"]))
                    try:
                        msg = obj["transition"]['issue']['00000']["message"]
                    except BaseException:
                        msg = ""
                    return ResultObj(False, "Error: Failed to apply configuration. Reason: " + msg)
                else:
                    raise Exception("Waiting for configuration to be applied")

    @staticmethod
    def _create_json_payload(resource, param):
        if len(resource) > 0:
            key = resource.pop(0)
            dictionary = {key: OpenApiRequest._create_json_payload(resource, param)}
        else:
            dictionary = param
        return dictionary

    @staticmethod
    def _validate_response(r: requests.Response, req_type):
        if req_type == OpenApiReqType.PATCH:
            response = r.json()
        else:
            response = json.loads(r.content)
        if 'title' in response.keys() and response['title'] in INVALID_RESPONSE:
            return ResultObj(False, "Error: Request failed. Details: " + response['detail'])
        return ResultObj(True, "")

    @staticmethod
    def send_get_request(request_data, op_params=''):
        with allure.step('Send GET request'):
            logging.info("Send GET request")
            params = '' if not op_params else op_params if op_params.startswith('?') else "/" + op_params
            req_url = '{url}{resource_path}{params}'.format(url=OpenApiRequest._get_endpoint_url(request_data),
                                                            params=params,
                                                            resource_path=request_data.resource_path)
            r = requests.get(url=req_url, verify=False, auth=OpenApiRequest._get_http_auth(request_data))
            OpenApiRequest.print_request(r.request)
            OpenApiRequest.print_response(r, OpenApiReqType.GET)

            res = OpenApiRequest._validate_response(r, OpenApiReqType.GET)
            if not res.result:
                return res.info
            return r.content.decode('utf8')

    @staticmethod
    def send_patch_request(request_data, op_params=''):
        with allure.step("Send PATCH request"):
            logging.info("Send PATCH request")
            with allure.step("Add data to patch request"):
                split_path = list(filter(None, request_data.resource_path.split('/')))
                if op_params and (split_path[-1] != op_params):
                    split_path.append(op_params)
                OpenApiRequest.payload = OpenApiRequest._create_json_payload(split_path, request_data.param_value)

            if OpenApiRequest.changeset is None:
                res = OpenApiRequest.create_nvue_changest(request_data)
                if not res.result:
                    logging.info(f'Failed to create revision. Abort the current request\nInfo: {res.info}')
                    OpenApiRequest.changeset = None
                    OpenApiRequest.payload = {}
                    return res.info

            rev_string = {"rev": OpenApiRequest.changeset}
            req_type = OpenApiReqType.PATCH

            logging.info("Send PATCH request")
            r = requests.patch(url=OpenApiRequest._get_endpoint_url(request_data) + "/",
                               auth=OpenApiRequest._get_http_auth(request_data),
                               verify=False,
                               data=json.dumps(OpenApiRequest.payload).replace('"null"', "null"),
                               params=rev_string,
                               headers=REQ_HEADER)
            OpenApiRequest.print_request(r.request)
            OpenApiRequest.print_response(r, req_type)
            res = OpenApiRequest._validate_response(r, req_type)
            return res.info

    @staticmethod
    def send_delete_request(request_data, op_params=''):
        with allure.step('Send DELETE request'):
            logging.info("Send DELETE request")
            if op_params:
                request_data.param_value = 'null'
                return OpenApiRequest.send_patch_request(request_data, op_params)
            else:
                if OpenApiRequest.changeset is None:
                    res = OpenApiRequest.create_nvue_changest(request_data)
                    if not res.result:
                        logging.info(f'Failed to create revision. Abort the current request\nInfo: {res.info}')
                        OpenApiRequest.changeset = None
                        OpenApiRequest.payload = {}
                        return res.info

                rev_string = {"rev": OpenApiRequest.changeset}
                req_type = OpenApiReqType.DELETE

                if request_data.param_name == '':
                    url = OpenApiRequest._get_endpoint_url(request_data) + request_data.resource_path
                else:
                    url = OpenApiRequest._get_endpoint_url(request_data) + request_data.resource_path + "/" + \
                        request_data.param_name

                logging.info("Send DELETE request")
                r = requests.delete(url=url,
                                    auth=OpenApiRequest._get_http_auth(request_data),
                                    verify=False,
                                    params=rev_string,
                                    headers=REQ_HEADER)

                OpenApiRequest.print_request(r.request)
                OpenApiRequest.print_response(r, req_type)
                res = OpenApiRequest._validate_response(r, req_type)
                return res.info

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
            r = r.json()
            response = json.dumps(r, indent=2)
            if not response.isnumeric():
                assert isinstance(r, dict) and r.get('status') != 200 and 'title' in r and 'detail' in r, \
                    f"In case of bad request expect status!=200 and some error message, but response is: {r}"
                return f"{r['title']}: {r['detail']}"
            return OpenApiRequest._send_get_req_and_wait_till_completed(request_data, response)

    @staticmethod
    def _send_get_req_and_wait_till_completed(request_data, rev):
        with allure.step("Send GET request"):
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
                if "Performing reboot" in response['status']:
                    return json.loads(r.content.decode('utf-8'))['status']
                if response['state'] == "action_success":
                    return json.loads(r.content.decode('utf-8'))['status']
                elif response['state'] == 'action_error' and response['issue'] != '':
                    return json.loads(r.content.decode('utf-8'))['issue'][0]['message']
                elif response['state'] and response['state'] != "running" and response['state'] != "start":
                    info = response["status"] + " - issue: " + response["issue"]
                time.sleep(10)
            assert action_success, info


class OpenApiCommandHelper:
    req_method = {OpenApiReqType.GET: OpenApiRequest.send_get_request,
                  OpenApiReqType.PATCH: OpenApiRequest.send_patch_request,
                  OpenApiReqType.DELETE: OpenApiRequest.send_delete_request,
                  OpenApiReqType.ACTION: OpenApiRequest.send_action_request,
                  OpenApiReqType.APPLY: OpenApiRequest.apply_nvue_changeset}

    @staticmethod
    def update_open_api_port(port_num):
        OpenApiRequest.port_num = port_num
        logging.info(f"OpenApi port number updated to {port_num}")

    @staticmethod
    def execute_script(user_name, password, req_type, dut_ip, resource_path, op_param_name='', op_param_value=''):
        request_data = RequestData(user_name, password, dut_ip, resource_path, op_param_name, op_param_value)
        return OpenApiCommandHelper.req_method[req_type](request_data, op_param_name)

    @staticmethod
    def execute_action(action_type, user_name, password, dut_ip, resource_path, params):
        request_data = RequestData(user_name, password, dut_ip, resource_path.strip(), action_type, params)
        return OpenApiCommandHelper.req_method[OpenApiReqType.ACTION](request_data, resource_path)
