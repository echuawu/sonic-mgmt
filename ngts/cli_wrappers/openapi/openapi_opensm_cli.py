import logging
from ngts.cli_wrappers.openapi.openapi_base_clis import OpenApiBaseCli
logger = logging.getLogger()


class OpenApiOpenSmCli(OpenApiBaseCli):

    def __init__(self):
        self.cli_name = "ib"
