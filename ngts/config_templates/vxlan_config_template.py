import allure

from ngts.cli_util.stub_engine import StubEngine
from ngts.config_templates.parallel_config_runner import parallel_config_runner
from functools import partial


class VxlanConfigTemplate:
    """
    This class contain 2 methods for configuration and cleanup of VXLAN related settings.
    """
    @staticmethod
    def configuration(topology_obj, vxlan_config_dict, request=None):
        """
        Method which are doing VXLAN configuration
        :param topology_obj: topology object fixture
        :param request: request object fixture
        :param vxlan_config_dict: configuration dictionary with all VXLANs related info
        Example: {
        'dut': [{'vtep_name': 'vtep_76543', 'vtep_src_ip': '10.1.0.32', 'vni': 76543, 'vlan': 2345}],
        'ha': [{'vtep_name': 'vtep_76543', 'vtep_src_ip': '10.1.1.32', 'vtep_dst_ip': '10.1.0.32', 'vni': 76543,
                'vtep_ips': [('23.45.0.1', '24')]}]
        }
        """
        if request:
            with allure.step('Add Vxlan configuration cleanup into finalizer'):
                cleanup = partial(VxlanConfigTemplate.cleanup, topology_obj, vxlan_config_dict)
                request.addfinalizer(cleanup)

        with allure.step('Applying VXLAN configuration'):
            conf = {}
            for player_alias, configuration in vxlan_config_dict.items():
                cli_object = topology_obj.players[player_alias]['stub_cli']
                for vxlan_info in configuration:
                    cli_object.vxlan.configure_vxlan(vxlan_info)

                conf[player_alias] = cli_object.vxlan.engine.commands_list
                cli_object.vxlan.engine.commands_list = []

            parallel_config_runner(topology_obj, conf)

    @staticmethod
    def cleanup(topology_obj, vxlan_config_dict):
        """
        Method which are doing VXLAN cleanup
        :param topology_obj: topology object fixture
        :param vxlan_config_dict: configuration dictionary with all VXLANs related info
        Example: {
        'dut': [{'vtep_name': 'vtep_76543', 'vtep_src_ip': '10.1.0.32', 'vni': 76543, 'vlan': 2345}],
        'ha': [{'vtep_name': 'vtep_76543', 'vtep_src_ip': '10.1.1.32', 'vtep_dst_ip': '10.1.0.32', 'vni': 76543,
                'vtep_ips': [('23.45.0.1', '24')]}]
        }
        """
        with allure.step('Performing VXLAN configuration cleanup'):
            conf = {}
            for player_alias, configuration in vxlan_config_dict.items():
                cli_object = topology_obj.players[player_alias]['stub_cli']
                for vxlan_info in configuration:
                    cli_object.vxlan.delete_vxlan(vxlan_info)
                conf[player_alias] = cli_object.vxlan.engine.commands_list
                cli_object.vxlan.engine.commands_list = []

            parallel_config_runner(topology_obj, conf)