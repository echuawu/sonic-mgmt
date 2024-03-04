import logging
import allure
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_constants.constants_nvos import CertificateFiles

logger = logging.getLogger()


class Certificate(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/certificate'
        self.certificate_path = CertificateFiles.CERTIFICATE_PATH
        self.parent_obj = parent_obj

    def set_certificate_type(self, cert_type="certificate"):
        """
        :param cert_type: the certificate type
        :return:
        """
        with allure.step('change the certificate type to {}'.format(cert_type)):
            self._resource_path = f'/{cert_type}'
            self.certificate_path += f"{cert_type}/"

    def import_certificate(self, import_type, cert_id, uri1, uri2="", passphrase="", data=""):
        """

        :param import_type:
        :param cert_id:
        :param uri1:
        :param uri2:
        :param passphrase:
        :return:
        """
        with allure.step("import certificate: {}".format(cert_id)):
            SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_import, TestToolkit.engines.dut,
                                            self.get_resource_path(), import_type, cert_id, uri1, uri2,
                                            passphrase, data).verify_result()

    def action_delete(self, cert_id, should_succeed=True):
        with allure.step("Delete certificate: {}".format(cert_id)):
            SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_delete, TestToolkit.engines.dut,
                                            self.get_resource_path(), cert_id).verify_result()

    def generate_uri_for_type(self, player, type):
        """
        we have use multiple ways to import new certificate, for two of them we need a full uri:
        Example: scp://root:12345@10.237.116.70/auto/sw_system_project/NVOS_INFRA/security/verification/cert_mgmt/test_bundle_uri_again.pem
        in this method we will generate the uri fot all different types
        :param player:
        :return:
        """
        uri = f'scp://{player.username}:{player.password}@{player.ip}{self.certificate_path}'

        if type == CertificateFiles.URI_BUNDLE:
            return f"{uri}certificate_bundle.p12"
        if type == CertificateFiles.PUBLIC_PRIVATE:
            return f"{uri}certificate_public.pem", f"{uri}certificate_private.pem"
        if type == CertificateFiles.DATA:
            return f"{uri}certificate_data.txt"
        else:  # CertificateFiles.URI:
            return f"{uri}ca-certificate.crt"
