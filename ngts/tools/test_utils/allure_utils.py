from contextlib import contextmanager

import allure
import logging


@contextmanager
def allure_step(step_msg):
    """
    @summary:
        Context manager that wraps allure step context and a log with the same message
    @param step_msg: The desired step message
    """
    with allure.step(step_msg) as allure_step_context:
        logging.info(f'Step start: {step_msg}')
        try:
            yield allure_step_context
        finally:
            logging.info(f'Step end: {step_msg}')
