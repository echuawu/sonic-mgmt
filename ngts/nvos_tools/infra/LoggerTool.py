import logging


def generate_log_format(asctime: str = '%(asctime)s', level: str = '%(levelname)s', filename: str = '%(filename)s',
                        lineno: str = '%(lineno)d'):
    return f'[{asctime}] [ {level}\t] [ {filename}:{lineno} ] $ %(message)s'


def get_logger(level=logging.INFO):
    log_format = generate_log_format()
    logging.basicConfig(level=level, format=log_format)
    return logging.getLogger(__name__)
