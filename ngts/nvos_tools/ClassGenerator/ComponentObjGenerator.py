import sys


PATH_TO_PARTIAL_YAML_FILE = "partial.yaml"
GET_KEY = "get"
PATCH_KEY = "patch"
DELETE_KEY = "delete"
SUMMARY_KEY = 'summary'
PARAMS_KEY = "parameters"
GET_PARAM_KEY = 'requestBody'
LIST_OF_PARAMS_TO_IGNORE = ['include', 'omit', 'revGet', 'revUpdate']


class Component:
    name = ''
    param_list = []
    show_method = False
    set_method = False
    unset_method = False
    list_of_next_components = []
    resource_path = ''

    def __init__(self, name, resource_path):
        self.name = name
        self.param_list = []
        self.show_method = False
        self.set_method = False
        self.unset_method = False
        self.set_param = ''
        self.list_of_next_components = []
        self.resource_path = resource_path


classes_list = Component("root", "root")


def get_component_obj(label, list_of_component_objects):
    for component_obj in list_of_component_objects:
        if component_obj.name == label:
            return component_obj
    return None


def get_last_split_label(str_to_split):
    split_param_path = str_to_split.split('/')
    return split_param_path[len(split_param_path) - 1]


def get_param(partial_dictionary):
    if GET_PARAM_KEY in partial_dictionary.keys():
        param = partial_dictionary[GET_PARAM_KEY]
        param_name = get_last_split_label(list(param.values())[0])
        if param_name not in LIST_OF_PARAMS_TO_IGNORE:
            return param_name
    return ''


def update_component_data(component_obj, component_data):
    list_of_component_data_keys = component_data.keys()

    if GET_KEY in list_of_component_data_keys:
        component_obj.show_method = True

    if PATCH_KEY in list_of_component_data_keys:
        component_obj.set_method = True
        component_obj.set_param = get_param(component_data[GET_KEY])

    if DELETE_KEY in list_of_component_data_keys:
        component_obj.unset_method = True


def add_classes_to_dictionary(component_data, split_label, resource_path):
    temp_ptr = classes_list

    for label in split_label:
        if label.startswith('{') and label.endswith('}'):
            temp_label = label.strip('{}')
            if temp_label not in temp_ptr.param_list:
                temp_ptr.param_list.append(temp_label)
            continue

        component_ptr = get_component_obj(label, temp_ptr.list_of_next_components)

        if not component_ptr:
            new_component = Component(label, resource_path)
            if split_label.index(label) == len(split_label) - 1:
                update_component_data(new_component, component_data)
            temp_ptr.list_of_next_components.append(new_component)
            temp_ptr = temp_ptr.list_of_next_components[0]
        else:
            temp_ptr = component_ptr
