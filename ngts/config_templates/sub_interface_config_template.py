import allure

from ngts.config_templates.parallel_config_runner import parallel_config_runner


class SubIntConfigTemplate:
    """
    This class contain 2 methods: configuration and deletion of sub interfaces related setting.
    """

    @staticmethod
    def configuration(topology_obj, sub_int_config_dict):
        """
        This method applies sub interfaces configuration
        :param topology_obj: topology object fixture
        :param sub_int_config_dict: configuration dictionary with all sub interfaces related info
        Example: {'dut': [{'iface': eth0.100, ', vlan_id': ''},{'iface': 'Po1.200', vlan_id': '200'}]
                  'ha':[{'iface': "bond1", vlan_id': '200'}]}
        """
        with allure.step('Applying sub interfaces configuration'):
            conf = {}
            for player_alias, configuration in sub_int_config_dict.items():
                cli_object = topology_obj.players[player_alias]['stub_cli']
                for sub_int_config in configuration:
                    cli_object.interface.add_sub_interface(sub_int_config.get("iface"),
                                                           sub_int_config.get("vlan_id"))
                    if player_alias != "dut":
                        cli_object.interface.enable_interface(
                            f'{sub_int_config.get("iface")}.{sub_int_config.get("vlan_id")}')

                conf[player_alias] = cli_object.interface.engine.commands_list
                cli_object.interface.engine.commands_list = []

            parallel_config_runner(topology_obj, conf)

    @staticmethod
    def cleanup(topology_obj, sub_int_config_dict):
        """
        This method performs sub interfaces configuration clean-up
        :param topology_obj: topology object fixture
        :param sub_int_config_dict: configuration dictionary with all sub interfaces related info
        Example: Example: {'dut': [{'iface': eth0.100, ', vlan_id': ''},{'iface': 'Po1.200', vlan_id': '200'}]
                  'ha':[{'iface': "bond1", vlan_id': '200'}]}
        """
        with allure.step('Performing sub interfaces configuration cleanup'):
            conf = {}
            for player_alias, configuration in sub_int_config_dict.items():
                cli_object = topology_obj.players[player_alias]['stub_cli']
                if player_alias == "dut":
                    for sub_int_config in configuration:
                        cli_object.interface.del_sub_interface(sub_int_config.get("iface"))
                else:
                    for sub_int_config in configuration:
                        cli_object.interface.del_interface(
                            f'{sub_int_config.get("iface")}.{sub_int_config.get("vlan_id")}')
                conf[player_alias] = cli_object.interface.engine.commands_list
                cli_object.interface.engine.commands_list = []

            parallel_config_runner(topology_obj, conf)
