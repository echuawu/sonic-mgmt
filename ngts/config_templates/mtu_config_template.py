import allure

from ngts.config_templates.parallel_config_runner import parallel_config_runner
from functools import partial


class MTUConfigTemplate:
    """
    This class contain 2 methods for configuration and cleanup of interface mtu related settings.
    """
    @staticmethod
    def config_mtu(topology_obj, mtu_config_dict, action='config'):
        conf = {}
        if action == 'config':
            mtu_key = 'mtu'
        elif action == 'clean':
            mtu_key = 'origin_mtu'

        for player_alias, configuration in mtu_config_dict.items():
            cli_object = topology_obj.players[player_alias]['stub_cli']
            for interface_info in configuration:
                iface = interface_info['iface']
                mtu = interface_info.get(mtu_key)
                if mtu:
                    cli_object.interface.set_interface_mtu(iface, mtu)
            conf[player_alias] = cli_object.interface.engine.commands_list
            cli_object.interface.engine.commands_list = []

        parallel_config_runner(topology_obj, conf)

    @staticmethod
    def configuration(topology_obj, mtu_config_dict, request=None):
        """
        Method which are doing interface mtu configuration
        :param topology_obj: topology object fixture
        :param request: request object fixture
        :param mtu_config_dict: configuration dictionary with all MTU related info
        Example: {
            'dut': [
                {'iface': interfaces.dut_ha_1, 'mtu': 1500, 'origin_mtu': 9100},
                {'iface': interfaces.dut_ha_2, 'mtu': 1500, 'origin_mtu': 9100},
                {'iface': interfaces.dut_hb_1, 'mtu': 1500, 'origin_mtu': 9100}
            ],
            'ha': [
                {'iface': interfaces.ha_dut_1, 'mtu': 9100, 'origin_mtu': 1500},
                {'iface': interfaces.ha_dut_2, 'mtu': 9100, 'origin_mtu': 1500}
            ],
            'hb': [
                {'iface': interfaces.hb_dut_1, 'mtu': 9100, 'origin_mtu': 1500},
                {'iface': DUMMY_0, 'mtu': 9100, 'origin_mtu': 1500},
                {'iface': DUMMY_1, 'mtu': 9100, 'origin_mtu': 1500}
            ]
        }
        """
        if request:
            with allure.step('Add MTU configuration cleanup into finalizer'):
                cleanup = partial(MTUConfigTemplate.cleanup, topology_obj, mtu_config_dict)
                request.addfinalizer(cleanup)

        with allure.step('Applying MTU configuration'):
            MTUConfigTemplate.config_mtu(topology_obj, mtu_config_dict)

    @staticmethod
    def cleanup(topology_obj, mtu_config_dict):
        """
        Method which are doing MTU cleanup
        :param topology_obj: topology object fixture
        :param mtu_config_dict: configuration dictionary with all MTU related info
        Example: {
            'dut': [
                {'iface': interfaces.dut_ha_1, 'mtu': 1500, 'origin_mtu': 9100},
                {'iface': interfaces.dut_ha_2, 'mtu': 1500, 'origin_mtu': 9100},
                {'iface': interfaces.dut_hb_1, 'mtu': 1500, 'origin_mtu': 9100}
            ],
            'ha': [
                {'iface': interfaces.ha_dut_1, 'mtu': 9100, 'origin_mtu': 1500},
                {'iface': interfaces.ha_dut_2, 'mtu': 9100, 'origin_mtu': 1500}
            ],
            'hb': [
                {'iface': interfaces.hb_dut_1, 'mtu': 9100, 'origin_mtu': 1500}
            ]
        }
        """
        with allure.step('Performing MTU configuration cleanup'):
            MTUConfigTemplate.config_mtu(topology_obj, mtu_config_dict, action='clean')
