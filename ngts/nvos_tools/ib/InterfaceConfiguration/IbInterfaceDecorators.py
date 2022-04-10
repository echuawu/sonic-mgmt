import logging
import sys

from .nvos_consts import ApiObject
from ngts.nvos_tools.infra.ResultObj import ResultObj
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit

logger = logging.getLogger()


def operation_wrapper(func):
    def wrapper_func(*args, **kwargs):
        pre_collect()
        try:
            func(*args, **kwargs)
            post_collect(False)
        except Exception as err:
            post_collect(True, sys.exc_info()[0])
    return wrapper_func


def pre_collect():
    """
    Run show command on tested ports
    """
    logging.info("Collecting data before executing the command")
    logging.info("--------------------------------------------")
    output = ApiObject[TestToolkit.api_show].show_interface()
    logging.info(output)
    logging.info("--------------------------------------------")


def post_collect(was_exception, exception=None):
    """
    1. Run show command on tested ports
    2. Create ResultObj and return it
    """
    try:
        logging.log("Collecting data after command execution")
        logging.info("--------------------------------------------")
        output = ApiObject[TestToolkit.api_show].show_interface()
        logging.info(output)
        logging.info("--------------------------------------------")
    except BaseException:
        logging.info("Failed to collect data")

    return ResultObj(was_exception, exception if was_exception else "")
