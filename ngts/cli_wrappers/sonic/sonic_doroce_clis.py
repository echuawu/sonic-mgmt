from retry.api import retry_call

DEFAULT_POOLS_LIST = ['egress_lossless_pool',
                      'egress_lossy_pool',
                      'ingress_lossless_pool',
                      'ingress_lossy_pool']


class SonicDoroceCli:
    """
    This class is for DoRoCE cli commands
    """

    def __init__(self, engine):
        self.engine = engine

    def config_doroce(self, compression, pool):
        """
        Configure the DoRoCE
        :param compression: the buffer compression. lossless or lossy
        :param pool: the pool. double-ipool or single-ipool
        :return: the output of cli command
        """
        return self.engine.run_cmd(f'sudo config doroce enabled {compression} {pool}')

    def config_doroce_lossless_double_ipool(self):
        """
        Apply 2 ingress pools - lossless RoCE ingress pool and lossy ingress pool
        :return: the output of cli command
        """
        return self.config_doroce('lossless', 'double-ipool')

    def config_doroce_lossless_single_ipool(self):
        """
        Apply 1 ingress pools - lossless RoCE pool and lossy ingress pool
        :return: the output of cli command
        """
        return self.config_doroce('lossless', 'single-ipool')

    def config_doroce_lossy_double_ipool(self):
        """
        Apply 2 ingress pools - lossy RoCE ingress pool and lossy ingress pool
        :return: the output of cli command
        """
        return self.config_doroce('lossy', 'double-ipool')

    def config_doroce_lossy_single_ipool(self):
        """
        Apply 1 ingress pool - lossy RoCE and lossy ingress pool
        :return: the output of cli command
        """
        return self.config_doroce('lossy', 'single-ipool')

    def disable_doroce(self):
        """
        Delete RoCE configuration.
        :return: the output of cli command
        """
        return self.engine.run_cmd('sudo config doroce disabled')

    def show_doroce_status(self):
        """
        Displaying RoCE configuration
        :return: the output of cli command
        """
        return self.engine.run_cmd('show doroce status')

    def show_buffer_configuration(self):
        """
        Displaying buffer configuration
        :return: the output of cli command
        """
        return self.engine.run_cmd('show buffer configuration')

    def check_buffer_configurations(self, expected_pools_list=DEFAULT_POOLS_LIST):
        retry_call(self._check_buffer_configurations, fargs=[expected_pools_list], tries=3, delay=3, logger=None)

    def _check_buffer_configurations(self, expected_pools_list):
        buffer_conf_output = self.show_buffer_configuration()
        assert "No buffer pool information available" not in buffer_conf_output, "The required qos reload"
        for expected_pool in expected_pools_list:
            assert f'Pool: {expected_pool}' in buffer_conf_output, f'The expected pool:{expected_pool} not' \
                                                                   f' found in the buffer configuration output'
