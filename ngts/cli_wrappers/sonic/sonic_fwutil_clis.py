class SonicFwutilCli:
    """
    This class hosts SONiC fwutil cli methods
    """

    def __init__(self, engine):
        self.engine = engine

    def show_fwutil_status(self):
        """
        This method is used to show the fwutil status
        :return: the output of cli command
        """
        return self.engine.run_cmd('sudo fwutil show status')
