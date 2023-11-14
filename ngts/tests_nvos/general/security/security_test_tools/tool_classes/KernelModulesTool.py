
import re
from typing import List
from ngts.nvos_tools.infra.ResultObj import ResultObj
from ngts.tests_nvos.conftest import ProxySshEngine
import logging


class KernelModulesTool:
    def __init__(self, engine: ProxySshEngine) -> None:
        self.engine = engine

    def get_loaded_kernel_modules(self) -> List[str]:
        """
        @summary: run lsmod and return the loaded kernel module names (list)
        @return: list of loaded kernel module names
        """
        output_raw = self.engine.run_cmd('lsmod')
        loaded_kernel_modules = list(map(
            lambda line: re.sub(r'\s+', ' ', line).split(' ')[0],
            output_raw.split('\n')[1:]
        ))
        return loaded_kernel_modules

    def remove_kernel_module(self, kernel_module_name: str) -> str:
        """
        @summary: remove the given kernel module
        @return: raw command output
        """
        return self.engine.run_cmd(f'sudo rmmod {kernel_module_name}')

    def load_kernel_module(self, kernel_module_ko_file_path: str) -> ResultObj:
        """
        @summary: load/install the given kernel module
        @return: result object containing the output and whether the command was successful or not
        """
        output = self.engine.run_cmd(f'sudo insmod {kernel_module_ko_file_path}')
        return ResultObj(
            result=output == '',
            info=f'Expected output: {""}\nActual output: "{output}"',
            returned_value=output
        )

    def get_kernel_module_ko_file_path(self, kernel_module_name: str) -> ResultObj:
        """
        @summary: return path of the .ko file of the given module
        @return: .ko file path , or None if not exists or if any error occurred
        """
        output_raw = self.engine.run_cmd(f'sudo modinfo {kernel_module_name}')
        output = self.engine.run_cmd(f'sudo modinfo {kernel_module_name} | grep filename')
        if output == '':
            return ResultObj(
                result=False,
                info=f'Bad given kernel module {kernel_module_name}. Output: "{output_raw}"',
                returned_value=output_raw
            )
        return ResultObj(
            result=True,
            info='',
            returned_value=output.split(':')[1].strip()
        )

    def is_kernel_module_loaded(self, kernel_module_name: str) -> bool:
        """
        @summary: return whether a given kernel module is loaded or not
        @return: [True/False]
        """
        return kernel_module_name in self.get_loaded_kernel_modules()
