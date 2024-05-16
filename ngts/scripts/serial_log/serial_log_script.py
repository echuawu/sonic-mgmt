"""
Based on:
    sx_fit_regression/libs/scripts/logs_extractor/serial_log_script.py
    sx_fit_regression/libs/tools/serial_connection_tools.py
"""

import argparse
import json
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime
from enum import Enum
from typing import List, Dict

import psutil

from infra.tools.general_constants.constants import NogaConstants

path = os.path.abspath(__file__)
sonic_mgmt_path = path.split('/ngts/')[0]
sys.path.append(sonic_mgmt_path)
sys.path.append(os.path.join(sonic_mgmt_path, "sonic-tool", "mars", "scripts"))

from infra.tools.topology_tools import nogaq  # noqa: E402
from ngts.constants.constants import SerialLoggerConst  # noqa: E402
from ngts.scripts.serial_log import serial_log_formatter  # noqa: E402
from lib.utils import get_logger  # noqa: E402


logger = get_logger("SerialLogHandler")


# SERIAL_LOGS_ERROR_LIST = [r'\[Failed\]',
#                           r'\[FAILED\]',
#                           'Root filesystem is busy; re-trying',
#                           'No such file or directory',
#                           'target is busy',
#                           'An error occurred',
#                           'oops']
ACTIONS = Enum("ACTIONS", ["OFF", "STORE", "ANALYZE", "ANALYZE_AND_OPEN_BUGS"])


def find_descendant_process_by_name(root_pid, name):
    """
    @summary:
        run a DFS of the child processes of the root process and return the pid
        of the first descendant that have the target name.
        this is useful when running a pipe command, e.g.
            'exec | ssh <> | awk ... > file'
        and want to get the pid of the ssh process
    @param root_pid:
        the pid of the root process
    @param name:
        the name of the target process (e.g. 'ssh')
    @return:
        the pid of the first descendant that have the target name, None if none
        exists
    """
    for child in psutil.Process(root_pid).children():
        pid = child.pid if child.name() == name else find_descendant_process_by_name(child.pid, name)
        if pid is not None:
            return pid


def ip_to_ip_path(ip: str) -> str:
    return str(ip).strip().replace('.', '_')


def get_all_ips_in_setup(setup_name: str) -> List[str]:
    setup_dict = nogaq.get_noga_resource_data(resource_name=setup_name)
    switch_names = [item[NogaConstants.NAME] for item in setup_dict[NogaConstants.RELATIONS][NogaConstants.HAS_A]
                    if item[NogaConstants.TYPE_TITLE] == "Switch"]
    switches = [nogaq.get_noga_resource_data(resource_name=switch) for switch in switch_names]
    return [switch[NogaConstants.ATTRIBUTES][NogaConstants.SPECIFIC][NogaConstants.IP] for switch in switches]


def get_serial_connection_command(target_ip: str) -> str:
    return (nogaq.get_noga_resource_data(ip_address=target_ip)[NogaConstants.ATTRIBUTES][NogaConstants.SPECIFIC]
            [NogaConstants.SERIAL_CMD])


def create_file_and_dir_if_not_exists(path: str):
    if os.path.exists(path):
        return

    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, 'w+'):
        pass
    os.chmod(path, SerialLoggerConst.ALL_PERM)


def get_session_serial_log_path(log_dir: str, target_ip: str) -> str:
    """@summary: Return the path to the session serial log file for the target ip"""
    return os.path.join(log_dir, ip_to_ip_path(target_ip) + '.log')


def get_session_serial_logs_dir_path(setup_name: str, session_id: str) -> str:
    """@summary: Return the path to the session serial log dir (create it if not exists)"""
    return SerialLoggerConst.LOG_DIR.format(setup_name=setup_name, session_id=session_id)


def get_session_serial_metadata_path(log_dir: str, target_ip: str) -> str:
    """@summary: Return the path to the session serial log json data file for the ip"""
    return os.path.join(log_dir, ip_to_ip_path(target_ip) + '.json')


def create_metadata_dict(log_path, pid, event_to_analyze_ts='', event_to_analyze_name='', event_list=None,
                         last_reboot_ts='', hostname=None) -> Dict:
    """
    @summary: this creates a serial logs session metadata dictionary with
    empty values. The metadata dictionary will be saved in JSON format for each
    switch in the setup
    @param  log_path: the path to the switch serial log file for this session
    @param  pid: the process id of the switches serial logging process
    @param event_to_analyze_name: the name of the last event we want to analyze
    the serial logs from
    @param event_to_analyze_ts: the timestamp of the last event we
     want to analyze the serial logs from
    @param last_reboot_ts: the timestamp of the last reboot that occurred
    @param event_list: the list of session events, represented as a dictionary with
     'name' and 'timestamp' keys. This are used to slice the session serial logs
     for analysis (e.g. from the last test case end until now)
    @return: the new serial logs session metadata dictionary with empty values
    """
    event_list = event_list if event_list is not None else []
    return {
        'log_file_path': log_path,
        'hostname': hostname,
        'log_process_pid': pid,
        'last_event_to_analyze_timestamp': event_to_analyze_ts,
        'last_event_to_analyze_name': event_to_analyze_name,
        'last_reboot_timestamp': last_reboot_ts,
        'event_list': event_list or []
    }


def get_serial_metadata(log_dir: str, target_ip: str) -> Dict:
    """
    @summary: this function fetches the relevant serial logs metadata
    @return: a dictionary with the data from the metadata file
    """
    json_path = get_session_serial_metadata_path(log_dir, target_ip)
    with open(json_path) as json_file:
        data = json.load(json_file)
    return data


def get_serial_logger_command(target_ip: str, hostname: str) -> str:
    """Builds the shell command that establishes serial connection and formats its output."""
    serial_command = get_serial_connection_command(target_ip)
    # remove authentication to serial console
    ssh_opt = ' -tt -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'
    serial_command = serial_command.replace('ssh', 'ssh' + ssh_opt).strip()

    formatter_command = ' '.join(['sudo', sys.executable, serial_log_formatter.__file__, "-b", hostname])
    # example: sudo /venv/bin/python serial_log_formatter.py -b 10.7.144.154
    return " | ".join(["exec", serial_command, formatter_command])


def start_serial_log(target_ip, log_file_path, append=False, hostname=''):
    """
    @summary: this function creates a new serial connection (in a sub-process)
              with added times to each line and directs its output into a file
    @param target_ip: the ip of the switch we want to log its output
    @param log_file_path: the path to the log file
    @param append: if False - will overwrite the contents of the logs file
    @param hostname: if not None - will add the hostname in the beginning of each line in the serial logs
    @note: if the target file does not exist - it will be created. If some
           directory in the path does not exists - an exception will be raised
    @return: the pid of the log process if succeeded, None if failed
    """
    try:
        logger.info(f"will record serial connection with times to {log_file_path}")
        # if the file not exists - create the file (with open) and set the permissions to be 777
        create_file_and_dir_if_not_exists(log_file_path)
        cmd = get_serial_logger_command(target_ip, hostname)
        logger.info("Running: " + cmd)
        sh_process = subprocess.Popen(cmd, shell=True, stdout=open(log_file_path, 'a' if append else 'w'))
        time.sleep(0.1)
        pid = find_descendant_process_by_name(sh_process.pid, 'ssh')
    except Exception as err:
        pid = None
        logger.error(f'Exception of type {type(err)} received during start_serial_logs: {err}')
        traceback.print_exc()

    return pid


def stop_serial_log(pid):
    """
    @summary: this function stops the serial log process
    @param pid: the pid of the log process we wish to stop
    """
    try:
        os.kill(int(pid), 9)
    except Exception as err:
        # if the process was already terminated - just report
        if isinstance(err, OSError) and err.errno == 3:
            logger.info(f"No Process Exists with PID {pid}")
        else:
            logger.error(f'Error: {type(err)} received during stop_serial_log: {err}')
            traceback.print_exc()


def init_serial_logging_on_all_switches(setup_name, session_id, add_hostname=True):
    """
    @summary: this function starts the serial logging for all the switches
    in the setup for a specific MARS session. It will fetch all the necessary
    ips from NOGA, build the log files paths and start the logging process.
    It will also create the relevant json files for the use of the session tests
    """
    setup_ips = get_all_ips_in_setup(setup_name)
    serial_logs_dir = get_session_serial_logs_dir_path(setup_name, session_id)
    logger.info(f"Will start serial logging for {setup_ips} at directory {serial_logs_dir}")
    for switch_ip in setup_ips:
        log_path = get_session_serial_log_path(serial_logs_dir, switch_ip)
        hostname = switch_ip if add_hostname else ''
        pid = start_serial_log(switch_ip, log_file_path=log_path, hostname=hostname)
        json_path = get_session_serial_metadata_path(serial_logs_dir, switch_ip)
        time_s = datetime.now().strftime(SerialLoggerConst.DATETIME_FORMAT)
        session_start_event = {'name': SerialLoggerConst.START_SERIAL_LOGGING,
                               'timestamp': time_s,
                               'hostname': hostname}
        with open(json_path, 'w') as json_file:
            data = create_metadata_dict(log_path, pid,
                                        session_start_event['timestamp'],
                                        session_start_event['name'],
                                        event_list=[session_start_event],
                                        hostname=hostname)
            json.dump(data, json_file)
        os.chmod(json_path, SerialLoggerConst.ALL_PERM)


def stop_serial_logging_on_all_switches(setup_name, session_id):
    """Stops the serial logging for all the switches in the setup and prints the serial log contents."""
    setup_ips = get_all_ips_in_setup(setup_name)
    log_dir = get_session_serial_logs_dir_path(setup_name, session_id)
    for switch_ip in setup_ips:
        logger.info(f"Stop serial logging for {switch_ip}")
        json_data = get_serial_metadata(log_dir, switch_ip)
        pid = json_data['log_process_pid']
        logger.info(f"{switch_ip} serial log pid is {pid} - will try to kill if exists")
        if pid:
            stop_serial_log(pid)

        log_path = get_session_serial_log_path(log_dir, switch_ip)
        logger.info(f"Printing contents of {log_path}")
        try:
            with open(log_path, encoding="ISO-8859-1") as log_file:
                contents = log_file.read()
                contents = contents.encode('ascii', 'replace').decode('utf-8')  # workaround for logger exception
                logger.info(f"\n\n===================== SERIAL LOG FOR {switch_ip} =====================\n{contents}" +
                            f"\n===================== END SERIAL LOG FOR {switch_ip} =====================\n\n")
        except Exception as e:
            logger.error(f"Failed to print serial log of {switch_ip} that was stored at {log_path}. {type(e)}: {e}")


def parse_args():
    """Handle parsing the command line arguments using argparse. Documented in the code."""
    usage_str = """Script to be used as a regression step in order to start/stop
    serial logging on all the switches on a given setup"""
    action_help_str = f"""One of the following:
    {ACTIONS.OFF.name.lower()}: Don't keep serial logs
    {ACTIONS.STORE.name.lower()}: Store serial logs but don't analyze them
    {ACTIONS.ANALYZE.name.lower()}: Store serial logs and run log analyzer
    {ACTIONS.ANALYZE_AND_OPEN_BUGS.name.lower()}: Store serial logs and run log analyzer and bug handler"""

    epilog_str = f'How to run the script:\n{usage_str}'
    cmd_line_parser = argparse.ArgumentParser(usage=usage_str, epilog=epilog_str,
                                              formatter_class=argparse.RawDescriptionHelpFormatter)
    cmd_line_parser.add_argument('function',
                                 choices=FUNCTION_MAP.keys())
    cmd_line_parser.add_argument('--setup_name',
                                 help='Setup name in NOGA')
    cmd_line_parser.add_argument('--session_id',
                                 help='MARS session number')
    # todo: action is currently ignored until log-analyzer is enabled for serial
    cmd_line_parser.add_argument('--action',
                                 choices=[action.name.lower() for action in ACTIONS],
                                 help=action_help_str)
    return cmd_line_parser.parse_args()


if __name__ == '__main__':
    FUNCTION_MAP = {'START': init_serial_logging_on_all_switches,
                    'STOP': stop_serial_logging_on_all_switches,
                    }  # todo: 'ANALYZE_INSTALL_PHASE': analyze_install_phase_serial_logs_on_all_switches}
    try:
        logger.info(f"Start running script ({__file__})")
        args = parse_args()
        if args.action == ACTIONS.OFF:
            # not really necessary because if action=off then the script is skipped by mars anyway
            logger.info("Serial logger is off")
        else:
            FUNCTION_MAP[args.function](setup_name=args.setup_name, session_id=args.session_id)
        logger.info(f"Finished running script ({__file__})")
    except Exception as err:
        logger.error(f"\nException {type(err)} occurred with message: {err}\nTraceback:\n{traceback.format_exc()}")
        traceback.print_exc()
        raise  # raise an exception, keeping the stack trace
