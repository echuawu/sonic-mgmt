class SonicAdaptiveRoutingCli:
    """
    This class implements SONiC Adaptive Routing cli methods
    """

    def __init__(self, engine):
        self.engine = engine

    def restart_dockers(self, condition=False):
        return "yes" if condition else "yes n"

    def enable_ar_function(self, restart_swss=False, validate=True):
        return self.engine.run_cmd(f'{self.restart_dockers(restart_swss)} | sudo config ar enabled', validate=validate)

    def disable_ar_function(self, restart_swss=False, validate=True):
        return self.engine.run_cmd(f'{self.restart_dockers(restart_swss)} | sudo config ar disabled', validate=validate)

    def enable_ar_port(self, port, restart_swss=False, validate=True):
        return self.engine.run_cmd(f'{self.restart_dockers(restart_swss)} | sudo config ar port enabled {port}', validate=validate)

    def disable_ar_port(self, port, restart_swss=False, validate=True):
        return self.engine.run_cmd(f'{self.restart_dockers(restart_swss)} | sudo config ar port disabled {port}', validate=validate)

    def config_ar_profile(self, profile, restart_swss=False, validate=True):
        return self.engine.run_cmd(f'{self.restart_dockers(restart_swss)} | sudo config ar profile {profile}', validate=validate)

    def enable_ar_link_utilization(self, threshold=None, restart_swss=False, validate=True):
        enable_cmd = "sudo config ar link-utilization-threshold enabled"
        if threshold:
            enable_cmd += f" {threshold}"
        return self.engine.run_cmd(f'{self.restart_dockers(restart_swss)} | {enable_cmd}', validate=validate)

    def disable_ar_link_utilization(self, restart_swss=False, validate=True):
        return self.engine.run_cmd(f'{self.restart_dockers(restart_swss)} | sudo config ar link-utilization-threshold disabled', validate=validate)

    def show_ar_config(self):
        return self.engine.run_cmd(f'show ar config')
