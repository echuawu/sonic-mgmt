import os
from contextlib import contextmanager
import inspect
import allure
import logging

logger = logging.getLogger()


@contextmanager
def step(step_msg):
    """
    @summary:
        Context manager that wraps allure step context and a log with the same message
    @param step_msg: The desired step message
    """
    orig_logger_formatter = logger.handlers[0].formatter
    orig_logger_format: str = orig_logger_formatter._fmt

    caller_frame = inspect.currentframe().f_back.f_back
    caller_file = inspect.getframeinfo(caller_frame).filename
    lineno = caller_frame.f_lineno
    filename = os.path.basename(caller_file)

    new_logger_format = orig_logger_format.replace('%(filename)s', filename).replace('%(lineno)s', str(lineno))
    new_logger_formatter = logging.Formatter(new_logger_format)
    new_logger_formatter.datefmt = '%Y-%m-%d %H:%M:%S'

    def print_step_log_info(log_info_msg: str):
        logger.handlers[0].setFormatter(new_logger_formatter)
        logging.info(log_info_msg)
        logger.handlers[0].setFormatter(orig_logger_formatter)

    with allure.step(step_msg) as allure_step_context:
        print_step_log_info(f'Step start: {step_msg}')
        step_success = True
        try:
            yield allure_step_context
        except Exception as e:
            step_success = False
            raise e
        finally:
            print_step_log_info(f'Step end [{"SUCCESS" if step_success else "FAIL"}]: {step_msg}')
