import logging
from ngts.constants.constants_nvos import OpenApiReqType
from ngts.nvos_tools.infra.ResultObj import ResultObj
import json
import allure
import requests
from requests.auth import HTTPBasicAuth
from retry import retry

logger = logging.getLogger()

ENDPOINT_URL_TEMPLATE = 'https://{ip}/nvue_v1'
REQ_HEADER = {"Content-Type": "application/json"}


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
            changeset = response.popitem()[0]
            return changeset

    @staticmethod
    def apply_nvue_changeset(request_data, changeset, add_approve=True):
        with allure.step("Apply NVUE changeset"):
            logging.info("Apply NVUE changeset")
            apply_payload = {"state": "apply", "auto-prompt": {"ays": "ays_yes"}} if add_approve else {"state": "apply"}
            url = '{url_endoint}/revision/{req_quote}'.format(url_endoint=OpenApiRequest._get_endpoint_url(request_data),
                                                              req_quote=requests.utils.quote(changeset, safe=""))
            r = requests.patch(url=url, auth=OpenApiRequest._get_http_auth(request_data), verify=False,
                               data=json.dumps(apply_payload), headers=REQ_HEADER)
            OpenApiRequest.print_request(r.request)
            OpenApiRequest.print_response(r, OpenApiReqType.PATCH)
            OpenApiRequest._validate_response(r, OpenApiReqType.PATCH)

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
                if obj["state"] == "ays_fail":
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
        split_path.reverse()

        if len(split_path) < 1:
            assert "Invalid resource path: " + request_data.resource_path

        payload = {}
        for comp in split_path:
            if comp not in payload.keys():
                payload = {}
                payload[comp] = temp_comp
                temp_comp = payload

        return payload

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
    def send_patch_request(request_data, op_params=''):
        with allure.step('Send PATCH request'):
            changeset = OpenApiRequest.create_nvue_changest(request_data)
            logging.info("Using NVUE Changeset: '{}'".format(changeset))

            payload = OpenApiRequest._create_json_payload(request_data)

            query_string = {"rev": changeset}
            logging.info("Send patch request")
            r = requests.patch(url=OpenApiRequest._get_endpoint_url(request_data) + "/",
                               auth=OpenApiRequest._get_http_auth(request_data),
                               verify=False,
                               data=json.dumps(payload),
                               params=query_string,
                               headers=REQ_HEADER)
            OpenApiRequest.print_request(r.request)
            OpenApiRequest.print_response(r, OpenApiReqType.PATCH)

            res = OpenApiRequest._validate_response(r, OpenApiReqType.PATCH)
            if not res.result:
                return res.info

            OpenApiRequest.apply_nvue_changeset(request_data, changeset)
            try:
                result = OpenApiRequest._check_apply_status(request_data, changeset)
                if not result.result:
                    return result.info
            except Exception:
                return "Error: Failed to apply configuration"
            return "Configuration applied successfully"

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
            return OpenApiRequest.send_patch_request(request_data, op_params)


class OpenApiCommandHelper:

    req_method = {OpenApiReqType.GET: OpenApiRequest.send_get_request,
                  OpenApiReqType.PATCH: OpenApiRequest.send_patch_request,
                  OpenApiReqType.DELETE: OpenApiRequest.send_delete_request}

    @staticmethod
    def execute_script(user_name, password, req_type, dut_ip, resource_path, op_param_name='', op_param_value=''):
        request_data = RequestData(user_name, password, dut_ip, resource_path, op_param_name, op_param_value)
        return OpenApiCommandHelper.req_method[req_type](request_data, op_param_name)
