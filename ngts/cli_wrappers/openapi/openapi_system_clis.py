import logging
from ngts.cli_wrappers.openapi.openapi_base_clis import OpenApiBaseCli
logger = logging.getLogger()


class OpenApiSystemCli(OpenApiBaseCli):

    def __init__(self):
        self.cli_name = "System"
