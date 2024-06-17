import logging
import re

logger = logging.getLogger()


class FilesTool:

    @staticmethod
    def get_subfiles_list(engine, folder_path, subfiles_pattern=""):
        """
        :param subfiles_pattern:
        :param engine:
        :param folder_path: a full path for a specific folder
        :return: list of all subfiles in the folder
        """
        output = engine.run_cmd('ls {}/*'.format(folder_path))
        reg = r'\b(?:{})-\d+\+[^\s]+\b|\b(?:{})+\d*+[^\s]+\b'.format(subfiles_pattern, subfiles_pattern)
        return re.findall(reg, output)
