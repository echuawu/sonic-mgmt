import logging
import pytest
from ngts.constants.constants import CliType

EXPECTED_MLNX_VERSION = "3.10.4206"
EXPECTED_SONIC_VERSION = "202311_RC.36-b4a12122b_Internal"

logger = logging.getLogger()


@pytest.mark.disable_loganalyzer
def test_verify_fanout_version(topology_obj):
    """
    Checks if the fanout version is correct
    """
    logger.info("Show version concise on the fanout")
    fanout_engine = topology_obj.players['fanout']['engine']
    fanout_engine_type = topology_obj.players['fanout']['attributes'].noga_query_data['attributes']['Topology Conn.'][
        'CLI_TYPE']

    if fanout_engine_type == CliType.SONIC:
        logger.info("This is a SONiC fanout switch")
        current_version = fanout_engine.run_cmd('show version')
        assert EXPECTED_SONIC_VERSION in current_version
    else:
        logger.info("This is an ONYX fanout switch")
        current_version = fanout_engine.run_cmd('show version concise')
        assert EXPECTED_MLNX_VERSION in current_version
