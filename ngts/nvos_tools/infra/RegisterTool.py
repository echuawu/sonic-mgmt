import logging

logger = logging.getLogger()


class RegisterTool:

    @staticmethod
    def get_mst_status(engine):
        logging.info('Get MST PCI loaded module and configuration module')
        return engine.run_cmd('sudo mst status')

    @staticmethod
    def get_mst_register_value(engine, mst_dev_name, reg_name):
        logging.info(f'Get MST register value')
        return engine.run_cmd(f'sudo mlxreg -d {mst_dev_name} -g --reg_name {reg_name}')
