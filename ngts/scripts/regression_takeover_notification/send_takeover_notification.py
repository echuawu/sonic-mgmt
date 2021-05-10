import time
import logging

logger = logging.getLogger()


def test_send_takeover_notification(topology_obj):
    """
    This function will send a regression takeover notification to all the active terminals.
    :param topology_obj: topology object fixture
    """
    wait_between_notf_to_regression_start = 3
    takeover_message = "Mars regression is taking over in {} minutes. Please save your work and logout".\
        format(wait_between_notf_to_regression_start)
    dut_engine = topology_obj.players['dut']['engine']
    logger.info("Sending a regression takeover notification to the user")
    dut_engine.run_cmd('wall {}'.format(takeover_message))
    logger.info("Sleeping for {} minutes".format(wait_between_notf_to_regression_start))
    time.sleep(wait_between_notf_to_regression_start * 60)
