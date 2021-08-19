import commands
import os


def get_all_different_file_name_list(expected_diff_file_name_list):
    git_diff_command = 'git --no-pager diff  --name-status develop..upstream/master | egrep "^M"'
    git_diff_output = commands.getstatusoutput(git_diff_command)
    rc = git_diff_output[0]
    git_diff_output_file_list = git_diff_output[1].split('\n')

    if rc != 0:
        raise Exception(git_diff_output)

    return [format_file_name(file_name) for file_name in git_diff_output_file_list if
            format_file_name(file_name) not in expected_diff_file_name_list]


def format_file_name(file_name):
    return file_name.lstrip('M').lstrip('\t')


def get_expected_diff_file_name_list():
    expected_diff_file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), "merge_overwrite_conflicts")
    with open(expected_diff_file_name) as f:
        return [file_name.strip('\n') for file_name in f.readlines()]
    return []


if __name__ == "__main__":
    expected_diff_file_name_list = get_expected_diff_file_name_list()
    different_file_name_list = get_all_different_file_name_list(expected_diff_file_name_list)
    print("----------------------------File number is {0} ---------------------------".format(len(different_file_name_list)))
    for file_name in different_file_name_list:
        print(file_name)
