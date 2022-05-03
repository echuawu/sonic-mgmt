import logging
import pytest

EXPECTED_VERSION = "3.10.1974"

logger = logging.getLogger()


@pytest.mark.disable_loganalyzer
def test_verify_fanout_version(topology_obj):
    """
    Checks if the fanout version is correct
    """
    logger.info("Show version concise on the fanout")
    fanout_engine = topology_obj.players['fanout']['engine']
    current_version = fanout_engine.run_cmd('show version concise')
    assert EXPECTED_VERSION in current_version
