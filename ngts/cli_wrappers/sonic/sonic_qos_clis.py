class SonicQosCli:
    """
    This class hosts SONiC Qos cli methods
    """

    def __init__(self, engine):
        self.engine = engine

    def reload_qos(self):
        """
        This method is to reload qos
        :param engine: ssh engine object
        :return: command output
        """
        return self.engine.run_cmd('sudo config qos reload ', validate=True)

    def clear_qos(self):
        """
        This method is to clear qos
        :param engine: ssh engine object
        :return: command output
        """
        return self.engine.run_cmd('sudo config qos clear ', validate=True)

    def stop_buffermgrd(self):
        """
        This method is to stop buffermgrd
        :param engine: ssh engine object
        :return: command output
        """
        return self.engine.run_cmd('docker exec swss supervisorctl stop buffermgrd', validate=True)

    def start_buffermgrd(self):
        """
        This method is to start buffermgrd
        :param engine: ssh engine object
        :return: command output
        """
        return self.engine.run_cmd('docker exec swss supervisorctl start buffermgrd', validate=True)
