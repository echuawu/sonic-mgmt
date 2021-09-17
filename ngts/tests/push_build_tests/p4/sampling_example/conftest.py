"""

conftest.py

Defines the methods and fixtures which will be used by pytest

"""

import pytest
import logging
from ngts.constants.constants import P4SamplingConsts
import ngts.helpers.p4_sampling_fixture_helper as fixture_helper
logger = logging.getLogger()
APP_NAME = P4SamplingConsts.APP_NAME


@pytest.fixture(scope="package", autouse=True)
def skipping_p4_sampling_test_case_for_spc1(platform_params):
    """
    If platform is SPC1, skip all test cases except test_p4_sampling_not_support_on_spc1
    :param platform_params: platform_params fixture
    """
    fixture_helper.skipping_p4_sampling_test_case_for_spc1(platform_params)


@pytest.fixture(scope="package", autouse=True)
def skipping_p4_sampling_test_case(engines):
    """
    If p4-sampling is not ready, skipping all p4-sampling test cases execution
    :param engines: engines fixture
    """
    fixture_helper.skipping_p4_sampling_test_case(engines.dut)


@pytest.fixture(scope='package', autouse=False)
def clean_p4_sampling_entries(engines):
    """
    Fixture used to add entries and remove entries after test case finish
    :param engines: engines fixture object
    """
    port_entries, flow_entries = fixture_helper.clean_p4_sampling_entries(engines)
    yield
    fixture_helper.recover_p4_sampling_entries(engines, port_entries, flow_entries)


@pytest.fixture(scope='class', autouse=False)
def p4_sampling_entries(skipping_p4_sampling_test_case_for_spc1, topology_obj, interfaces, engines, table_params):
    """
    Fixture used to add entries and remove entries after test case finish
    :param skipping_p4_sampling_test_case_for_spc1: skipping_p4_sampling_test_case_for_spc1 fixture object
    :param topology_obj: topology_obj fixture object
    :param engines: engines fixture object
    :param interfaces: interfaces fixture object
    :param table_params: table_params fixture object
    """
    fixture_helper.add_p4_sampling_entries(engines, table_params)
    yield
    fixture_helper.remove_p4_sampling_entries(topology_obj, interfaces, engines, table_params)


@pytest.fixture(scope='class')
def table_params(interfaces, engines, topology_obj, ha_dut_2_mac, hb_dut_1_mac):
    """
    Fixture used to create the TableParams object which contains some params used in the testcases
    :param interfaces: interfaces fixture
    :param engines : engines fixture object
    :param topology_obj: topology_obj fixture object
    :param ha_dut_2_mac: ha_dut_2_mac fixture object
    :param hb_dut_1_mac: hb_dut_1_mac fixture object
    """
    return fixture_helper.get_table_params(interfaces, engines, topology_obj, ha_dut_2_mac, hb_dut_1_mac)
