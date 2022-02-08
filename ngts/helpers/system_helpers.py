import logging
import re
import os

from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon
from retry.api import retry_call

logger = logging.getLogger()

JOBS_MAX_ATTEMPTS = 30
JOBS_POLLING_INTERVAL_SEC = 10


class PrefixEngine():

    def __init__(self, engine, prefix):
        self.engine = engine
        self.prefix = prefix

    def run_cmd(self, cmd, validate=False):
        return self.engine.run_cmd(f'{self.prefix} {cmd}', validate=validate)


def list_files(engine, path, pattern=''):
    files = GeneralCliCommon.ls(engine, path, flags='-1').splitlines()
    return [os.path.join(path, file) for file in files if re.search(pattern, file)]


def verify_empty_job_queue(engine):
    """
    Verifies that systemd job queue is empty.
    :param engine: the engine to use.
    :raise Exception: if the job queue is not empty.
    """
    if engine.run_cmd("sudo systemctl list-jobs | grep -v 'No jobs running.'"):
        raise Exception('Job queue is not empty')


def wait_for_all_jobs_done(engine, max_attempts=JOBS_MAX_ATTEMPTS, polling_interval_sec=JOBS_POLLING_INTERVAL_SEC):
    """
    Polls systemd job queue until it is empty.
    :param engine: the engine to use.
    :param max_attempts: the maximum number of attempts before failing with Exception
    :param polling_interval_sec: the polling interval in seconds
    :raise Exception: if the job queue was not empty after max_attempts have been made.
    """
    retry_call(verify_empty_job_queue,
               fargs=[engine],
               tries=max_attempts,
               delay=polling_interval_sec,
               logger=logger)
