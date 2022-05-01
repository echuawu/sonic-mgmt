import os
import pytest
import logging

from pytest_ansible.errors import AnsibleConnectionFailure
from ngts.tools.infra import update_sys_path_by_community_plugins_path
from ngts.constants.constants import NvosCliTypes
from devices.sonic import SonicHost
from plugins.loganalyzer import pytest_addoption, loganalyzer


update_sys_path_by_community_plugins_path()
logger = logging.getLogger()


def pytest_cmdline_main(config):
    """
    Pytest hook which adds default parameters, required for pytest-ansible module
    We define ansible_host_pattern with stub string, which will be updated later by dut hostname. In other case will
    need to provide additional pytest argument with dut hostname
    :param config: pytest build-in
    """
    path = os.path.abspath(__file__)
    sonic_mgmt_path = path.split('/ngts/')[0]
    config.option.ansible_inventory = sonic_mgmt_path + '/ansible/inventory'
    config.option.ansible_host_pattern = 'stub_string'


@pytest.fixture(scope='session')
def ansible_adhoc(request, topology_obj):
    """
    Return an inventory initialization method.
    :param request: pytest build-in
    :param topology_obj:  topology_obj fixture
    :return: ansible host initialization object
    """

    dut_hostname = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Common']['Name']
    request.config.option.ansible_host_pattern = dut_hostname

    plugin = request.config.pluginmanager.getplugin("ansible")

    def init_host_mgr(**kwargs):
        return plugin.initialize(request.config, request, **kwargs)
    return init_host_mgr


@pytest.fixture(scope="session")
def duthosts(ansible_adhoc, topology_obj):
    """
    Emulate duhosts fixure from community
    :param ansible_adhoc: ansible_adhoc fixture
    :param topology_obj: topology_obj fixture
    :return: list of ansible engines
    """
    dut_ansible_engine = None
    dut_hostname = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Common']['Name']
    if topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Topology Conn.']['CLI_TYPE'] not in \
            NvosCliTypes.NvueCliTypes:
        try:
            dut_ansible_engine = SonicHost(ansible_adhoc, dut_hostname)
        except AnsibleConnectionFailure as err:
            logger.error(f'DUT not reachable. Can not create DUT ansible engine. Error: {err}')

    return [dut_ansible_engine]
