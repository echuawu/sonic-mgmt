import logging
import os
from ngts.constants.constants_nvos import OpenApiReqType

logger = logging.getLogger()


class OpenApiCommandHelper:

    @staticmethod
    def _get_command_get_request(user_name, password, req_type, dut_ip, resource_path, op_params=''):
        cmd = 'curl -k --user {user_name}:{password} --request {req_type} https://{dut_ip}/nvue_v1{resource_path}' \
              '{params}'.format(user_name=user_name, password=password, req_type=req_type, resource_path=resource_path,
                                dut_ip=dut_ip, params="/" + op_params if op_params else '')
        return cmd

    @staticmethod
    def _get_command_patch_request(user_name, password, req_type, dut_ip, resource_path, op_params=''):
        assert "Not Implemented"

    @staticmethod
    def _get_command_delete_request(user_name, password, req_type, dut_ip, resource_path, op_params=''):
        assert "Not Implemented"

    @staticmethod
    def _get_command_str(user_name, password, req_type, dut_ip, resource_path, op_params=''):
        if req_type == OpenApiReqType.GET:
            return OpenApiCommandHelper._get_command_get_request(user_name, password, req_type, dut_ip,
                                                                 resource_path, op_params)
        elif req_type == OpenApiReqType.PATCH:
            return OpenApiCommandHelper._get_command_patch_request(user_name, password, req_type, dut_ip,
                                                                   resource_path, op_params)
        elif req_type == OpenApiReqType.DELETE:
            return OpenApiCommandHelper._get_command_delete_request(user_name, password, req_type,
                                                                    dut_ip, resource_path, op_params)
        else:
            assert "Open API type is invalid"

    @staticmethod
    def execute_script(user_name, password, req_type, dut_ip, resource_path, op_params=''):
        logger.info("Building command")

        cmd = OpenApiCommandHelper._get_command_str(user_name, password, req_type, dut_ip, resource_path, op_params)

        try:
            logging.info("Executing openApi command: {}".format(cmd))
            stream = os.popen(cmd)
            output = stream.read()
            logger.info("output: \n" + output)
            return output
        except Exception as ex:
            return 'Error: ' + str(ex)
