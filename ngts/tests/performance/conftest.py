import os
import pytest
import logging

from ngts.helpers.adaptive_routing_helper import ArHelper, ArPerfHelper
from ngts.helpers.system_helpers import copy_files_to_syncd
from ngts.tests.nightly.adaptive_routing.constants import ArConsts
from ngts.constants.constants import PerfConsts
from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure

logger = logging.getLogger()
ar_helper = ArHelper()


@pytest.fixture(scope='module', autouse=True)
def skip_if_not_performance_setup(is_performance):
    """
    This method validates that the performance tests run only on performance setup
    :param is_performance: is_performance fixture
    """
    if not is_performance:
        pytest.skip('Performance tests are supported only on performance setup. Test is skipped')


@pytest.fixture(scope='module')
def config_node(cli_objects, engines, topology_obj):
    ar_perf_helper = ArPerfHelper(engines)
    tg_engines = ar_perf_helper.tg_engines
    for engine in tg_engines:
        copy_files_to_syncd(engines[engine], PerfConsts.CONFIG_FILES_DICT[engine], PerfConsts.CONFIG_FILES_DIR)
        ar_perf_helper.run_cmd_on_syncd(engines[engine], PerfConsts.DISABLE_MAC_SCRIPT, python=True)
        cli_objects[engine].mac.clear_fdb()
        ar_perf_helper.run_cmd_on_syncd(engines[engine], PerfConsts.LB_SCRIPT_TG,
                                        additional_args=PerfConsts.LOG_PORTS_DICT[engine])
        ar_perf_helper.copy_traffic_cmds_to_node(engines[engine], engine)


@pytest.fixture(scope='module')
def config_dut(cli_objects, engines, topology_obj):
    ar_perf_helper = ArPerfHelper(engines)
    dut_engine = engines.dut
    ar_perf_helper.config_ip_neighbors_on_dut(dut_engine, topology_obj)
    ar_perf_helper.ensure_ar_perf_config_set(cli_objects, topology_obj)


@pytest.fixture(scope='module')
def load_ibm_profile(engines, cli_objects, topology_obj):
    logger.info('Load ingress buffer mode custom AR profile')
    ar_perf_helper = ArPerfHelper(engines)
    ar_ibm_profile_config_folder_path = os.path.dirname(os.path.abspath(__file__)) + '/' + PerfConsts.AR_PERF_CONFIG_FOLDER
    ar_perf_helper.copy_and_load_profile_config(engines, cli_objects, ar_ibm_profile_config_folder_path, PerfConsts.CUSTOM_IBM_PROFILE_JSON)

    # Enable AR custom profile
    with allure.step(f'Enable {PerfConsts.IBM_CUSTOM_PROFILE_NAME} profile'):
        ar_perf_helper.enable_ar_profile(cli_objects, PerfConsts.IBM_CUSTOM_PROFILE_NAME, restart_swss=True)
        dut_ports = ar_perf_helper.get_dut_ports(topology_obj)
        cli_objects.dut.interface.check_link_state(dut_ports)
        ar_perf_helper.config_ip_neighbors_on_dut(engines.dut, topology_obj)

    yield

    with allure.step(f'Return to default profile {ArConsts.GOLDEN_PROFILE0} at the end of the test'):
        ar_helper.enable_ar_profile(cli_objects, ArConsts.GOLDEN_PROFILE0, restart_swss=True)
        cli_objects.dut.interface.check_link_state(dut_ports)
        ar_perf_helper.config_ip_neighbors_on_dut(engines.dut, topology_obj)
