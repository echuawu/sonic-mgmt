#!/auto/app/Python-3.6.2/bin/python
import argparse
import logging
import re
logger = logging.getLogger()


def init_parser():
    description = ('Functionality of the script: \n'
                   'Parse the Jenkins Parameters into the upload_regression_results_to_msft.py script parameters.\n'
                   'For Example: if the jenkins parameters are\n'
                   '\",user_sessions,8290561 8290558 8292116 8292122 8292121 8292132 8292551,false,'
                   ',false,false,false,false,true,false,false,true,false,false,true,true,false,\"\n'
                   'The parsed script parameters will be\n'
                   '\"--user_sessions 8290561 8290558 8292116 8292122 8292121 8292132 8292551\"')
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument("--params", required=True, help="jenkins active params")
    parser.add_argument("--command", required=True, help="jenkins command")

    arguments, unknown = parser.parse_known_args()
    if unknown:
        raise Exception("unknown argument(s): {}".format(unknown))
    return arguments


def get_platform_filter_param(params):
    platform_options = ["2010", "2100", "2410", "2700", "3420", "3700", "3800", "4410", "4600", "4600C", "4700", "5600"]
    start_idx = 1 if params[0] == "," else 0
    end_idx = -1 if params[-1] == "," else None
    updated_params = params[start_idx:end_idx] if end_idx is not None else params[start_idx:]
    platform_filter_param = updated_params.split(',')[-13:]
    if platform_filter_param[0] == "false":
        new_params = params.replace(",".join(platform_filter_param), "false,")
    else:
        platform_filter_list = []
        for index in range(1, 13):
            if platform_filter_param[index] == "true":
                platform_filter_list.append(platform_options[index - 1])
        platform_filter_string = " ".join(platform_filter_list)
        new_params = params.replace(",".join(platform_filter_param), "true,{}".format(platform_filter_string))
    return new_params


def split_modify_params(params):
    if ",true" in params:
        params_list = params.split(",true ")
        # params_list[0] = params_list[0][1:]
        params_list[1] = "true {}".format(params_list[1][:-2])
    else:
        params_list = params.split(",false ")[:-1]
    return params_list


def update_param_list(params, replace_dict, params_idx_dict, command):
    for old_str, new_str in replace_dict.items():
        params = params.replace(old_str, new_str)
    params_list = params.split(",") if command != 'modify' else split_modify_params(params)
    params_list = [param for param in params_list if param]
    params_to_remove = []
    for idx in params_idx_dict.keys():
        if idx < len(params_list):
            if params_list[idx].startswith('true '):
                params_list[idx] = params_list[idx].replace("true", params_idx_dict[idx])
                if params_idx_dict[idx] == "--redmine_issues_to_update":
                    param_name, json_str = params_list[idx].split("--redmine_issues_to_update ")
                    json_str = re.search(r"\s*(.*)", json_str).group(1)
                    json_str = json_str.replace("\\\"", "\\\\\"")
                    json_str = json_str.replace("\"", "\\\"")
                    params_list[idx] = "--redmine_issues_to_update  {json_str}\\\"".format(json_str=json_str)
            else:
                params_to_remove.append(params_list[idx])
    for param in params_to_remove:
        params_list.remove(param)
    return params_list


def parse_params(params, command):
    replace_dict = {"true,": "true ", "false,": "false "}
    params_idx_dict = {}
    if command == "collect":
        collect_replace_dict = {"last_days,": "--last_days ", ",user_sessions,": "--user_sessions "}
        replace_dict.update(collect_replace_dict)
        params_idx_dict = {1: "--filter_sessions_started_by", 2: "--filter_platforms"}
        params = get_platform_filter_param(params)
    elif command == "modify":
        params_idx_dict = {0: "--user_excel_table_path", 1: "--redmine_issues_to_update"}
    elif command == "compare":
        params_idx_dict = {0: "--compare_excel", 1: "--msft_results_path"}
    elif command == "save":
        params_idx_dict = {0: "--sessions_to_save"}
    elif command == "concat":
        params_idx_dict = {0: "--excel_tables"}
    elif command == "export":
        export_replace_dict = {"true,true,": "true "}
        replace_dict = export_replace_dict
        params_idx_dict = {0: "--export_excel"}
    params_list = update_param_list(params, replace_dict, params_idx_dict, command)
    print(" ".join(params_list))


if __name__ == '__main__':
    arg = init_parser()
    parse_params(arg.params, arg.command)
