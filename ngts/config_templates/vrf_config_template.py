import allure
from functools import partial


class VrfConfigTemplate:
    """
    This class contain 2 methods for configuration and vrf_config_dict deletion of VRF related settings.
    """
    @staticmethod
    def configuration(topology_obj, vrf_config_dict, request=None):
        """
        This method applies VRF configuration
        :param topology_obj: topology object fixture
        :param request: request object fixture
        :param vrf_config_dict: configuration dictionary with all VRF related info
        Example: {'dut': [{'vrf': 'Vrf_custom', 'table': '10', 'vrf_interfaces':
        [dutlb1_2, dutlb2_2, dutlb3_2, dutlb4_2, dutlb5_2,
        dutlb6_2, duthb1]}]}
        """
        if request:
            cleanup = partial(VrfConfigTemplate.cleanup, topology_obj, vrf_config_dict)
            with allure.step('Add VRF configuration cleanup into finalizer'):
                request.addfinalizer(cleanup)
        with allure.step('Applying VRF configuration'):
            for player_alias, configuration in vrf_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                for vrf_info in configuration:
                    vrf = vrf_info['vrf']
                    if vrf_info.get('table'):
                        table = vrf_info['table']
                        cli_object.vrf.add_vrf(vrf, table)
                    else:
                        cli_object.vrf.add_vrf(vrf)
                    if vrf_info.get('vrf_interfaces'):
                        for interface in vrf_info['vrf_interfaces']:
                            cli_object.vrf.add_interface_to_vrf(interface, vrf)

    @staticmethod
    def cleanup(topology_obj, vrf_config_dict):
        """
        Method which are doing VRF configuration cleanup
        :param topology_obj: topology object fixture
        :param vrf_config_dict: configuration dictionary with all VRF related info
        Example: {'dut': [{'vrf': 'Vrf_custom', 'vrf_interfaces': [dutlb1_2, dutlb2_2, dutlb3_2, dutlb4_2, dutlb5_2,
        dutlb6_2, duthb1]}]}
        """
        with allure.step('Performing VRF configuration cleanup'):
            for player_alias, configuration in vrf_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                for vrf_info in configuration:
                    vrf = vrf_info['vrf']
                    if vrf_info.get('vrf_interfaces'):
                        for interface in vrf_info['vrf_interfaces']:
                            cli_object.vrf.del_interface_from_vrf(interface, vrf)
                    cli_object.vrf.del_vrf(vrf)