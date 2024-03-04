import logging

from ngts.nvos_constants.constants_nvos import UfmMadConsts

logger = logging.getLogger()


class RegisterTool:

    @staticmethod
    def get_mst_status(engine):
        logging.info('Get MST PCI loaded module and configuration module')
        return engine.run_cmd('sudo mst status')

    @staticmethod
    def get_mst_register_value(engine, mst_dev_name, reg_name, additional_params=""):
        logging.info(f'Get {reg_name} value {additional_params}')
        return engine.run_cmd(f'sudo mlxreg -d {mst_dev_name} -g --reg_name {reg_name} {additional_params}')

    @staticmethod
    def set_mst_register_value(engine, mst_dev_name, reg_name, set_params, additional_params=""):
        logging.info(f'Set {reg_name} value {additional_params} with {set_params}')
        return engine.run_cmd(
            f'sudo mlxreg -d {mst_dev_name} --reg_name {reg_name} {additional_params} -s {set_params} -y')

    @staticmethod
    def update_pmaos_register(engine, admin_status, slot_index=0, module_index=0):
        indexes = f"-i slot_index={slot_index},module={module_index}"
        set_params = f"ase=1,e=1,ee=1,admin_status={admin_status}"
        return RegisterTool.set_mst_register_value(engine, UfmMadConsts.MST_DEV_NAME, UfmMadConsts.PMAOS_REGISTER,
                                                   set_params, additional_params=indexes)
