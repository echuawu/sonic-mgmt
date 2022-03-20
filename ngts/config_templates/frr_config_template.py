import allure

from ngts.cli_util.stub_engine import StubEngine
from ngts.config_templates.parallel_config_runner import parallel_config_runner


class FrrConfigTemplate:
    """
    This class contain 2 methods for configuration and cleanup of FRR related settings.
    """
    @staticmethod
    def configuration(topology_obj, frr_config_dict):
        """
        Method which are doing FRR configuration
        :param topology_obj: topology object fixture
        :param frr_config_dict: configuration dictionary with all FRR related info
        Example: {
        'dut': {'configuration': {'config_name': 'dut_frr_conf.conf', 'path_to_config_file': FRR_CONFIG_FOLDER},
                'cleanup': ['configure terminal', 'no router bgp 65000', 'exit', 'exit']},
        }
        """
        with allure.step('Applying FRR configuration'):
            for player_alias, configuration in frr_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                engine = topology_obj.players[player_alias]['engine']
                config_name = configuration['configuration']['config_name']
                path_to_config_file = configuration['configuration']['path_to_config_file']
                cli_object.frr.apply_frr_config(engine, config_name, path_to_config_file)
                cli_object.frr.save_frr_configuration(engine)

    @staticmethod
    def cleanup(topology_obj, frr_config_dict):
        """
        Method which are doing FRR cleanup
        :param topology_obj: topology object fixture
        :param frr_config_dict: configuration dictionary with all FRR related info
        Example: {
        'dut': {'configuration': {'config_name': 'dut_frr_conf.conf', 'path_to_config_file': FRR_CONFIG_FOLDER},
                'cleanup': ['configure terminal', 'no router bgp 65000', 'exit', 'exit']},
        }
        """
        with allure.step('Performing FRR configuration cleanup'):
            conf = {}
            for player_alias, configuration in frr_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                stub_engine = StubEngine()
                cli_object.frr.run_config_frr_cmd(stub_engine, configuration['cleanup'])
                cli_object.frr.save_frr_configuration(stub_engine)
                conf[player_alias] = stub_engine.commands_list

            parallel_config_runner(topology_obj, conf)
