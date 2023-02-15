import allure
from functools import partial

command_dict = {"pg": "buffer-threshold-pg",
                "queue": "buffer-threshold-queue",
                "latency": "latency-threshold-queue"}


class WjhBufferConfigTemplate:
    """
    This class contain 2 methods: configuration and deletion of WJH buffer congestion and latency thresholds.
    """
    @staticmethod
    def configuration(topology_obj, thresholds_config_dict, request=None):
        """
        This method applies WJH buffer congestion and latency thresholds configuration
        :param topology_obj: topology object fixture
        :param request: request object fixture
        :param thresholds_config_dict: configuration dictionary with all WJH buffer congestion and latency thresholds related info
        Example: {'dut': [{'iface': eth0, 'queue_type': 'pg', 'index': 0, 'threshold': 10}]}
        """
        if request:
            with allure.step('Add Vxlan configuration cleanup into finalizer'):
                cleanup = partial(WjhBufferConfigTemplate.cleanup, topology_obj, thresholds_config_dict)
                request.addfinalizer(cleanup)

        with allure.step('Applying WJH buffer congestion and latency thresholds configuration'):
            conf = {}
            for player_alias, configuration in thresholds_config_dict.items():
                engine = topology_obj.players[player_alias]['engine']
                for threshold_info in configuration:
                    iface = threshold_info['iface']
                    queue_type = threshold_info.get('queue_type')
                    threshold = threshold_info.get('threshold')

                    engine.run_cmd("sudo config what-just-happened {} {} {}".format(command_dict[queue_type], iface, threshold))

    @staticmethod
    def cleanup(topology_obj, thresholds_config_dict):
        """
        This method clear WJH buffer congestion and latency thresholds configuration
        :param topology_obj: topology object fixture
        :param thresholds_config_dict: configuration dictionary with all WJH buffer congestion and latency thresholds related info
        Example: {'dut': [{'iface': eth0, 'queue_type': 'pg', 'index': 0}]}
        """
        with allure.step('Clear WJH buffer congestion and latency thresholds configuration'):
            conf = {}
            for player_alias, configuration in thresholds_config_dict.items():
                engine = topology_obj.players[player_alias]['engine']
                for threshold_info in configuration:
                    iface = threshold_info['iface']
                    queue_type = threshold_info.get('queue_type')

                    engine.run_cmd("sudo config what-just-happened {} {} 0".format(command_dict[queue_type], iface))
