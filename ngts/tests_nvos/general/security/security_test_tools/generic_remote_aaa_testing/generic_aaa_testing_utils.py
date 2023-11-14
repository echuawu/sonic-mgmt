import logging

from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.cli_wrappers.openapi.openapi_command_builder import OpenApiRequest
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit


def detach_config():
    if TestToolkit.tested_api == ApiType.NVUE:
        logging.info('detach config using NVUE')
        NvueGeneralCli.detach_config(TestToolkit.engines.dut)
    else:
        logging.info('Clear global OpenApi changeset and payload')
        OpenApiRequest.clear_changeset_and_payload()
