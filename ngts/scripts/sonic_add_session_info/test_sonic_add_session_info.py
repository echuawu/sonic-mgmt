import pytest
import logging

logger = logging.getLogger()


@pytest.mark.disable_loganalyzer
def test_add_session_info(topology_obj, sonic_topo, chip_type, sonic_version, sonic_branch, platform_params,
                          sonic_session_facts_prefix):
    """
        The function collects the data required for the get_dynamic_info function of mars script sonic_add_session_info.
        Currently, it will get the following:
            1. version
            2. platform
            3. hwsku
            4. asic
            5. topology
            6. chip_type
            7. branch

        The data will be printed to stdout which will be read from sonic-tool/mars/scripts/sonic_add_session_info
        :param topology_obj: topology object fixture.
        :param sonic_topo: sonic_topo fixture
        :param sonic_version: sonic_version fixture
        :param chip_type: chip_type fixture
        :param sonic_branch: sonic_branch fixture
        :param platform_params: platform_params fixture
        :param sonic_session_facts_prefix: sonic_session_facts_prefix fixture
        :raise AssertionError: in case of script failure.
    """
    res = {
        "version": "SONiC." + sonic_version,  # sonic_version fixture doesn't contain the prefix SONiC.
        "platform": platform_params['platform'],
        "hwsku": platform_params['hwsku'],
        "asic": platform_params['asic_type'],
        "topology": sonic_topo,
        "chip_type": chip_type,
        "sonic_branch": sonic_branch
    }
    logger.info(f"{sonic_session_facts_prefix}{res}")
