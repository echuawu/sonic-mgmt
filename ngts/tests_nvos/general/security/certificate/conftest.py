import pytest

from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.system.System import System
from ngts.tools.test_utils import allure_utils as allure


@pytest.fixture(scope='module', autouse=True)
def clear_certs():
    yield
    system = System()
    with allure.step('delete imported certificates'):
        certs = OutputParsingTool.parse_json_str_to_dictionary(system.security.certificate.show()).get_returned_value()
        for cert in certs:
            system.security.certificate.cert_id[cert].action_delete().verify_result()
    with allure.step('delete imported ca-certificates'):
        certs = OutputParsingTool.parse_json_str_to_dictionary(system.security.ca_certificate.show()).get_returned_value()
        for cert in certs:
            system.security.ca_certificate.cert_id[cert].action_delete().verify_result()
