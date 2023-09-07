import logging

logger = logging.getLogger()


class DatabaseTool:

    @staticmethod
    def redis_cli_hset(engine, db_num, db_config, param, value):
        logging.info(f'Running redis-cli -n {db_num} hset "{db_config}" "{param}" "{value}"')
        return engine.run_cmd(f'redis-cli -n {db_num} hset "{db_config}" "{param}" "{value}"')

    @staticmethod
    def redis_cli_hget(engine, db_num, db_config, param):
        logging.info(f'Running redis-cli -n {db_num} hget "{db_config}" "{param}"')
        return engine.run_cmd(f'redis-cli -n {db_num} hget "{db_config}" "{param}"')

    @staticmethod
    def sonic_db_cli_hset(engine, asic, db_name, obj_num, param, value):
        logging.info(f'Running sonic-db-cli -n {asic} {db_name} hset {obj_num} {param} {value}')
        return engine.run_cmd(f'sonic-db-cli -n {asic} {db_name} hset {obj_num} {param} {value}')

    @staticmethod
    def sonic_db_cli_hget(engine, asic, db_name, obj_num, param):
        logging.info(f'Running sonic-db-cli -n {asic} {db_name} hget {obj_num} {param}')
        return engine.run_cmd(f'sonic-db-cli -n {asic} {db_name} hget {obj_num} {param}')
