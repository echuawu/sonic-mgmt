import logging

logger = logging.getLogger()


class RedisTool:

    @staticmethod
    def redis_cli_hset(engine, db_num, db_config, param, value):
        logging.info(f'Running redis-cli -n {db_num} hset "{db_config}" "{param}" {value}')
        return engine.run_cmd(f'redis-cli -n {db_num} hset "{db_config}" "{param}" {value}')

    def redis_cli_hget(engine, db_num, db_config, param):
        logging.info(f'Running redis-cli -n {db_num} hget "{db_config}" "{param}"')
        return engine.run_cmd(f'redis-cli -n {db_num} hget "{db_config}" "{param}"')
