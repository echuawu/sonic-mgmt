import logging
import os

logger = logging.getLogger()


class FilesTool:

    @staticmethod
    def get_subfiles_list(folder_path):
        """

        :param folder_path: a full path for a specific folder
        :return: list of all subfiles in the folder
        """
        assert folder_path, "Invalid path"
        subfiles = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                subfiles.append(file_path)
        return subfiles
