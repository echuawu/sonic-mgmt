import logging
from .openapi_command_builder import OpenApiCommandHelper

logger = logging.getLogger()


class OpenApiGeneralCli:

    """
    Open API cli wrapper
    """

    def __init__(self):
        pass

    @staticmethod
    def apply_config(engine):
        """
        Apply configuration
        :param engine: ssh engine object
        """
        return OpenApiCommandHelper.execute_script(engine.engine.username, engine.engine.password, 'PATCH', engine.ip,
                                                   'system/config/apply')
