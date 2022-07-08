import os
import tarfile
import yaml


def get_cred(credential_name):
    """
    Get GitHub/Redmine API credentials
    :return: dictionary with GitHub credentials {'user': aaa, 'api_token': 'bbb'}
             Or dictionary with Redmine credentials {'api_token': 'ccc'}
    """
    if not os.path.exists('/tmp/token/credentials.yaml'):
        cred_tarfile_name = 'credentials.tar.gz'
        cred_folder_path = os.path.dirname(__file__)
        gh_token_path = os.path.join(cred_folder_path, cred_tarfile_name)
        try:
            os.mkdir("/tmp/token")
        except OSError as e:
            raise AssertionError("Problem in creating temporary directory: /tmp/token. \n{}".format(e))
        with tarfile.open(gh_token_path, "r:gz") as f:
            f.extractall("/tmp/token")
    with open('/tmp/token/credentials.yaml', 'r') as gb_token:
        cred = yaml.load(gb_token, Loader=yaml.FullLoader).get(credential_name)
        return cred
