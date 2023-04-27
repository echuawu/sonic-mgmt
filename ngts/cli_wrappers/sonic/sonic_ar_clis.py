class SonicAdaptiveRoutingCli:
    """
    This class implements SONiC Adaptive Routing cli methods
    """

    def __init__(self, engine):
        self.engine = engine

    def restart_dockers(self, condition=False):
        return "yes" if condition else "yes n"

    def enable_ar_function(self, restart_swss=False):
        return self.engine.run_cmd(f'{self.restart_dockers(restart_swss)} | sudo config ar enabled')

    def disable_ar_function(self, restart_swss=False):
        return self.engine.run_cmd(f'{self.restart_dockers(restart_swss)} | sudo config ar disabled')

    def enable_ar_port(self, port, link_util_threshold=70, restart_swss=False):
        return self.engine.run_cmd(f'{self.restart_dockers(restart_swss)} | sudo config ar port enabled {port} '
                                   f'{link_util_threshold}')

    def disable_ar_port(self, port, restart_swss=False):
        return self.engine.run_cmd(f'{self.restart_dockers(restart_swss)} | sudo config ar port disabled {port}')

    def config_ar_profile(self, profile, restart_swss=False):
        return self.engine.run_cmd(f'{self.restart_dockers(restart_swss)} | sudo config ar profile {profile}')

    def show_ar_config(self):
        return self.engine.run_cmd(f'show ar config')

    def config_ar_profile_parameter(self, profile, parameter, value):
        return self.engine.run_cmd(f'redis-cli -n 4 hset "AR_PROFILE|{profile}" {parameter} {value}')
