class SonicQosCli:
    """
    This class hosts SONiC Qos cli methods
    """

    @staticmethod
    def reload_qos(engine):
        """
        This method is to reload qos
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd('sudo config qos reload ', validate=True)