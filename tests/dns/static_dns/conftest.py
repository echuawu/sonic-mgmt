import pytest
import logging

from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure
from .static_dns_util import RESOLV_CONF_FILE, get_nameserver_from_config_db, get_nameserver_from_resolvconf, \
    config_mgmt_ip

logger = logging.getLogger(__name__)
allure.logger = logger


@pytest.fixture(scope="module", autouse=True)
def is_static_dns_supported(duthost):
    cmd_err = duthost.shell("show dns nameserver", module_ignore_errors=True)['stderr']
    if 'Error: No such command "dns"' in cmd_err:
        pytest.skip("The static DNS is not supported by this image.")


@pytest.fixture(scope="module", autouse=True)
def static_dns_setup(duthost):
    with allure.step("Get all existing DNS nameserver from config db"):
        nameservers_db = get_nameserver_from_config_db(duthost)

        duthost.shell(f"cp {RESOLV_CONF_FILE} {RESOLV_CONF_FILE}.bk")
        if not nameservers_db:
            nameservers = get_nameserver_from_resolvconf(duthost)
        else:
            nameservers = nameservers_db

    with allure.step("Clear all existing DNS nameserver from config db"):
        for nameserver in nameservers_db:
            duthost.shell(f"config dns nameserver del {nameserver}")

    with allure.step(f"Clear all existing DNS nameserver from {RESOLV_CONF_FILE}"):
        duthost.shell(f"echo > {RESOLV_CONF_FILE}")

    yield

    with allure.step("Recover DNS nameserver in config db"):
        for nameserver in nameservers:
            duthost.shell(f"config dns nameserver add {nameserver}")


@pytest.fixture(autouse=True)
def static_dns_clean(duthost):

    yield

    with allure.step("Clean up the nameserver in config db"):
        nameservers = get_nameserver_from_config_db(duthost)
        for nameserver in nameservers:
            duthost.shell(f"config dns nameserver del {nameserver}")


@pytest.fixture()
def static_mgmt_ip_guarantee(duthost, mgmt_interfaces):
    with allure.step("Check the static ip address configured on the mgmt interface"):
        if not mgmt_interfaces:
            pytest.skip("No static ip address is configured, skip the test")

    with allure.step("Delete the ip address from the mgmt port"):
        config_mgmt_ip(duthost, mgmt_interfaces, "remove")

    yield

    with allure.step("Config the static ip on the mgmt port"):
        config_mgmt_ip(duthost, mgmt_interfaces, "add")


@pytest.fixture(scope="module")
def mgmt_interfaces(duthost, tbinfo):
    ansible_facts = duthost.config_facts(host=duthost.hostname, source="running")['ansible_facts']
    mgmt_interface_info = ansible_facts["MGMT_INTERFACE"] if "MGMT_INTERFACE" in ansible_facts else {}
    return mgmt_interface_info
