import pytest
import logging

from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.cli_wrappers.sonic.sonic_mac_clis import SonicMacCli
from retry.api import retry_call
from ngts.tests.nightly.fdb.fdb_helper import FDB_AGING_TIME


logger = logging.getLogger()


@pytest.fixture(scope='module', autouse=False)
def pre_configure_for_fdb_basic(engines, topology_obj, interfaces, cli_objects):
    """
    Pytest fixture which are doing configuration for fdb basic tests
    :param engines: engines object fixture
    :param topology_obj: topology object fixture
    :param interfaces: interfaces object fixture
    :param cli_objects: cli_objects object fixture
    """
    # VLAN config which will be used in test
    vlan_config_dict = {
        'dut': [{'vlan_id': 40, 'vlan_members': [{interfaces.dut_ha_1: 'access'},
                                                 {interfaces.dut_ha_2: 'access'},
                                                 {interfaces.dut_hb_1: 'access'},
                                                 {interfaces.dut_hb_2: 'access'}]},
                ],
        'ha': [{'vlan_id': 40, 'vlan_members': [{interfaces.ha_dut_1: None}, {interfaces.ha_dut_2: None}]},
               ],
        'hb': [{'vlan_id': 40, 'vlan_members': [{interfaces.hb_dut_1: None}, {interfaces.hb_dut_2: None}]},
               ]
    }

    # IP config which will be used in test
    ip_config_dict = {
        'dut': [{'iface': 'Vlan40', 'ips': [('40.0.0.1', '24')]},
                {'iface': interfaces.dut_ha_1, 'ips': [('40.0.0.2', '24')]},
                ],
        'hb': [{'iface': interfaces.hb_dut_1, 'ips': [('40.0.0.3', '24')]}]
    }
    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    cli_objects.hb.general.stop_service(engines.hb, 'lldpad')

    yield

    cli_objects.hb.general.start_service(engines.hb, 'lldpad')
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)


@pytest.fixture(scope='module', autouse=False)
def pre_configure_for_fdb_advance(engines, topology_obj, interfaces, cli_objects):
    """
    Pytest fixture which are doing configuration for fdb advanced test
    :param engines: engines object fixture
    :param topology_obj: topology object fixture
    :param interfaces: interfaces object fixture
    :param cli_objects: cli_objects object fixture
    """
    # VLAN config which will be used in test
    vlan_config_dict = {
        'dut': [{'vlan_id': 40, 'vlan_members': [{interfaces.dut_ha_1: 'access'},
                                                 {interfaces.dut_hb_1: 'access'}]},
                {'vlan_id': 50, 'vlan_members': [{interfaces.dut_ha_2: 'access'},
                                                 {interfaces.dut_hb_2: 'access'}]}
                ],
        'ha': [{'vlan_id': 40, 'vlan_members': [{interfaces.ha_dut_1: None}]},
               {'vlan_id': 50, 'vlan_members': [{interfaces.ha_dut_2: None}]},
               ],
        'hb': [{'vlan_id': 40, 'vlan_members': [{interfaces.hb_dut_1: None}]},
               {'vlan_id': 50, 'vlan_members': [{interfaces.hb_dut_2: None}]},
               ]
    }

    # IP config which will be used in test
    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    cli_objects.hb.general.stop_service(engines.hb, 'lldpad')

    yield

    cli_objects.hb.general.start_service(engines.hb, 'lldpad')
    VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)


@pytest.fixture(scope='function', autouse=True)
def pre_clear_fdb_table(engines, topology_obj, interfaces):
    SonicMacCli(engine=engines.dut).clear_fdb()


@pytest.fixture(scope='function', autouse=False)
def set_fdb_aging_time(engines, topology_obj):
    """
    Pytest fixture which is to set the fdb_aging_time
    :param engines: engines object fixture
    :param topology_obj: topology object fixture
    """
    old_fdb_aging_time = SonicMacCli(engine=engines.dut).get_fdb_aging_time()
    new_fdb_aging_time = FDB_AGING_TIME
    SonicMacCli(engine=engines.dut).set_fdb_aging_time(new_fdb_aging_time)

    def verify_fdb_aging_time(dut_engine, fdb_aging_time):
        actual_fdb_aging_time = SonicMacCli(engine=dut_engine).get_fdb_aging_time()
        assert actual_fdb_aging_time == fdb_aging_time, f"Actual fdb_aging_time:{actual_fdb_aging_time} doesn't equal to expected fdb_aging_time:{fdb_aging_time}"

    retry_call(verify_fdb_aging_time,
               fargs=[engines.dut, new_fdb_aging_time],
               tries=20,
               delay=15,
               logger=logger)

    yield
    SonicMacCli(engine=engines.dut).set_fdb_aging_time(old_fdb_aging_time)
    retry_call(verify_fdb_aging_time,
               fargs=[engines.dut, old_fdb_aging_time],
               tries=20,
               delay=15,
               logger=logger)
