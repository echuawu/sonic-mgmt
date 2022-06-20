import allure
import logging

logger = logging.getLogger()


def test_check_errors_in_log_during_deploy_sonic_image(engines, request, loganalyzer):
    """
    Test checks errors in logs which happen during deploy SONiC image
    This test must be executed as first test case after deploy SONiC image, because test logic will analyze syslog
    files since first entry in log till current test case execution entries.
    Test logic is next:
    - Get current LogAnalyzer start_string as variable and remove existing start_string from syslog file
    - Get oldest syslog file id
    - Create LogAnalyzer start_string and put it into oldest syslog file(create it)
    - Then on teardown step LogAnalyzer will analyze all logs since start_string till end_string(which will be
    added after current test case automatically by LogAnalyzer logic)
    :param engines: engines fixture
    :param request: pytest build-in
    """
    log_analyzer_start_string_line = get_la_start_string(engines.dut, request)
    oldest_syslog_id = get_oldest_syslog_id(engines.dut)
    new_log_analyzer_start_string = get_new_start_string(engines.dut, oldest_syslog_id, log_analyzer_start_string_line)
    insert_new_start_string(engines.dut, oldest_syslog_id, new_log_analyzer_start_string)

    # Logic below required for prevent issue when end_marker not available in syslog, we do force add end_marker
    logger.info('Adding end_marker in syslog')
    for dut in loganalyzer:
        run_id = loganalyzer[dut].ansible_loganalyzer.run_id
        # Command below may fail, but we do not care about it - LA will do the same after test executed(it will pass)
        engines.dut.run_cmd(f'sudo python /tmp/loganalyzer.py --action add_end_marker --run_id {run_id}')


def get_la_start_string(engine, request):
    """
    Get LogAnalyzer start string line and remove line which was added by LogAnalyzer at the beginning of current test
    :param engine: dut engine object
    :param request: pytest build-in
    :return: LogAnalyzer start_string line, example: r-lionfish-07 INFO start-LogAnalyzer-test_a.2022-05-16-13:49:02
    """
    test_name = request.node.name
    start = 'start-LogAnalyzer'
    start_prefix = start + '-' + test_name

    msg = 'Getting original LogAnalyzer start_string'
    with allure.step(msg):
        logger.info(msg)
        start_string_full_line = engine.run_cmd(f'sudo cat /var/log/syslog -n | grep {start_prefix}')
        # line example:  "   9	May 16 13:48:23.535689 r-lionfish-07 INFO start-LogAnalyzer-test_a.2022-05-16-13:49:02"
        start_string_line = ' '.join(start_string_full_line.split()[4:])
        start_string_line_number = start_string_full_line.split()[0]

    msg = 'Remove original LogAnalyzer start_string'
    with allure.step(msg):
        logger.info(msg)
        engine.run_cmd(f'sudo sed -i \'{start_string_line_number}d\' /var/log/syslog')

    return start_string_line


def get_oldest_syslog_id(engine):
    """
    Get oldest syslog file ID
    :param engine: dut engine
    :return: oldest syslog file ID
    """
    with allure.step('Getting oldest syslog file ID'):
        syslogs_list = engine.run_cmd('sudo ls /var/log/syslog*').split()
        list_of_file_ids = []
        for syslog_name in syslogs_list:
            for s in syslog_name.split('.'):
                if s.isdigit():
                    list_of_file_ids.append(int(s))
        # Get first element - which is bigger(oldest syslog file index) that other
        oldest_syslog_id = sorted(list_of_file_ids, reverse=True)[0]
        logger.info(f'Oldest syslog file id is: {oldest_syslog_id}')

    return oldest_syslog_id


def get_new_start_string(engine, oldest_syslog_id, start_string_line):
    """
    Get new LogAnalyzer start string with oldest timestamp inside
    :param engine: dut engine
    :param oldest_syslog_id: oldest syslog ID
    :param start_string_line: original LogAnalyzer start string line without timestamp
    :return: new LogAnalyzer start string with oldest timestamp inside,
    example: May 16 09:30:19 r-lionfish-07 INFO start-LogAnalyzer-test_a.2022-05-16-13:49:02
    """
    with allure.step('Get oldest syslog timestamp'):
        oldest_syslog_file = f'/var/log/syslog.{oldest_syslog_id}'
        file_reader = 'cat'
        if oldest_syslog_id > 1:
            oldest_syslog_file = oldest_syslog_file + '.gz'
            file_reader = 'zcat'

        oldest_syslog_line = engine.run_cmd(f'sudo {file_reader} {oldest_syslog_file} | head -1')
        # Add first 3 elements(oldest timestamp) at the beginning of new LogAnalyzer start string
        oldest_syslog_timestamp_string = ' '.join(oldest_syslog_line.split()[:3])

    with allure.step('Creating new start_string'):
        new_start_string = ' '.join([oldest_syslog_timestamp_string, start_string_line])
        logger.info(f'New start_string line is: {new_start_string}')

    return new_start_string


def insert_new_start_string(engine, oldest_syslog_id, new_start_string):
    """
    Insert new LogAnalyzer start string at the beginning of syslog entries(by creating new syslog.x.gz file
    with one line inside)
    :param engine: due engine
    :param oldest_syslog_id: oldest syslog id
    :param new_start_string: new LogAnalyzer start string
    """
    new_oldest_syslog_id = oldest_syslog_id + 1
    with allure.step(f'Inserting start_sting line into syslog file with ID: {new_oldest_syslog_id}'):
        engine.run_cmd(f'sudo echo \'{new_start_string}\' > syslog.{new_oldest_syslog_id}')
        engine.run_cmd(f'sudo gzip syslog.{new_oldest_syslog_id}')
        engine.run_cmd(f'sudo mv syslog.{new_oldest_syslog_id}.gz /var/log/')
