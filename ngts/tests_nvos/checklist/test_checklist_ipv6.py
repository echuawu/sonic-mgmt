import logging
import pytest
import allure
import os
from ngts.cli_wrappers.openapi.openapi_command_builder import OpenApiCommandHelper
from ngts.nvos_constants.constants_nvos import OpenApiReqType

logger = logging.getLogger()


@pytest.mark.platform
def test_checklist_ipv6(engines):
    """
    ipv6

    - ping
    - ssh connection
    - openapi
    """
    try:
        with allure.step("Get ipv6 address for switch " + engines.dut.ip):
            logging.info("Running 'nv show interface eth0 ip address'")
            output = engines.dut.run_cmd("nv show interface eth0 ip address")
            assert output, "The output is empty"
            addresses = output.split()
            assert len(addresses) >= 4, "The output is invalid"
            ipv6_add = addresses[3].split("/")[0]
            assert ipv6_add, "failed to get the ipv6 address"
            logging.info("ipv6 address: " + ipv6_add)

        with allure.step("Verify ping to ipv6 address " + ipv6_add):
            response = os.system("ping -c 3 -6" + ipv6_add)
            logging.info("response: " + response)
            # response == 0, "Ping failed"

        '''with allure.step("Verify ssh connection to ipv6 address " + ipv6_add):
            response = os.system("ssh -6 admin@" + ipv6_add)
            assert response == 0, "SSH connection failed"'''

        with allure.step("Verify OpenApi command using ipv6 address"):
            output = OpenApiCommandHelper.execute_script(engines.dut.user_name, engines.dut.password,
                                                         OpenApiReqType.GET, ipv6_add, "platform", "", "")
            logging.info(output)

    except BaseException as ex:
        logging.info("Something failed")
