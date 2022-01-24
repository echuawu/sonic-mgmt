#!/usr/bin/env python
import allure
import logging
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.cli_wrappers.sonic.sonic_qos_clis import SonicQosCli


logger = logging.getLogger()


@allure.title('Configure qos for dynamic buffer tests')
def test_configure_qos(topology_obj, qos_config_action):
    """
    This script will reload qos config or clear qos config
    :param topology_obj: topology object fixture
    :param qos_config_action: qos config action(reload/clear)
    :return: raise assertion error in case of script failure
    """
    try:
        dut_engine = topology_obj.players['dut']['engine']
        # Now all branches above 201911 except for 202106 support the feature
        if "202106" != SonicGeneralCli.get_image_sonic_version(dut_engine):
            if qos_config_action == "reload":
                SonicQosCli.reload_qos(dut_engine)
            else:
                SonicQosCli.clear_qos(dut_engine)
            SonicGeneralCli.save_configuration(dut_engine)
            dut_engine.reload(['sudo reboot'])

    except Exception as err:
        raise AssertionError(err)