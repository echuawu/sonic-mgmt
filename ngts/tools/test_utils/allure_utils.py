import os
from contextlib import contextmanager
import inspect
import allure
import logging

logger = logging.getLogger(__name__)


@contextmanager
def step(step_msg):
    """
    @summary:
        Context manager that wraps allure step context and a log with the same message
    @param step_msg: The desired step message
    """
    caller_frame = inspect.currentframe().f_back.f_back
    caller_file = inspect.getframeinfo(caller_frame).filename
    lineno = caller_frame.f_lineno
    filename = os.path.basename(caller_file)

    with allure.step(step_msg) as allure_step_context:
        logging.info(f'({filename}:{lineno}) Step start: {step_msg}')
        try:
            yield allure_step_context
        finally:
            logging.info(f'({filename}:{lineno}) Step end: {step_msg}')
