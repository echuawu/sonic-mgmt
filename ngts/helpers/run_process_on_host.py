import allure
import subprocess
import logging
import shlex
import concurrent.futures

logger = logging.getLogger()
SUCCESS = 0


def run_process_on_host(cmd, timeout=60, exec_path=None, validate=False):
    logger.info('Executing command on remote host: {}'.format(cmd))
    p = subprocess.Popen(shlex.split(cmd), cwd=exec_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        std_out, std_err = p.communicate(timeout=timeout)
        rc = p.returncode
    except subprocess.TimeoutExpired:
        logger.debug('Process is not responding. Sending SIGKILL.')
        p.kill()
        std_out, std_err = p.communicate()
        rc = p.returncode
        std_out = str(std_out.decode('utf-8') or '')
        std_err = str(std_err.decode('utf-8') or '')
    logger.debug('process:%s\n'
                 'rc:%s,\n'
                 'std_out:%s\n'
                 'std_err:%s', p.args, rc, std_out, std_err)

    logger.info('Command: {} finished execution'.format(cmd))

    if validate and rc != SUCCESS:
        logger.error('process:%s\n'
                     'rc:%s,\n'
                     'std_out:%s\n'
                     'std_err:%s', p.args, rc, std_out, std_err)
        raise Exception('Command: {} execution failed'.format(p.args))

    return std_out, std_err, rc


def run_background_process_on_host(processes_dict, process_name, cmd, **kwargs):
    """
    Start process(run cmd) in background
    :param processes_dict: dict which contains threads names and objects
    :param process_name: name of process(will be displayed in Allure report)
    :param cmd: cmd which should be executed
    :param kwargs: kwargs
    :return: process obj
    """
    with allure.step(f'Starting background process: "{process_name}"'):
        process_executor = concurrent.futures.ThreadPoolExecutor()
        process_obj = process_executor.submit(run_process_on_host, cmd, **kwargs)
        processes_dict[process_name] = process_obj

    return process_obj


def wait_until_background_procs_done(processes_dict):
    """
    Wait until background threads will finish and attach their output into Allure report
    :param processes_dict: list which contains threads objects
    """
    for proc_name, proc in processes_dict.items():
        with allure.step(f'Checking background process: "{proc_name}" results'):
            std_out, std_err, rc = proc.result()
            result = 'STDOUT:\n' + std_out.decode('utf-8') + '\n\nSTDERR:\n' + std_err.decode('utf-8')
            allure.attach(result, proc_name, allure.attachment_type.TEXT)
            if rc:
                raise AssertionError(f'Background thread process failed. '
                                     f'Check Allure report attached file: "{proc_name}" in step: "{proc_name}"')
