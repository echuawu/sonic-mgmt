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

    @staticmethod
    def clear_qos(engine):
        """
        This method is to clear qos
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd('sudo config qos clear ', validate=True)

    @staticmethod
    def stop_buffermgrd(engine):
        """
        This method is to stop buffermgrd
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd('docker exec swss supervisorctl stop buffermgrd', validate=True)

    @staticmethod
    def start_buffermgrd(engine):
        """
        This method is to start buffermgrd
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd('docker exec swss supervisorctl start buffermgrd', validate=True)
