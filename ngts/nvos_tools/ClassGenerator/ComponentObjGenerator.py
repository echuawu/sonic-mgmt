PATH_TO_PARTIAL_YAML_FILE = "partial.yaml"
GET_KEY = "get"
PATCH_KEY = "patch"
DELETE_KEY = "delete"
SUMMARY_KEY = 'summary'
PARAMS_KEY = "parameters"
LIST_OF_PARAMS_TO_IGNORE = ['include', 'omit', 'revGet', 'revUpdate']


class Component:
    name = ''
    param_list = []
    show_method = False
    set_method = False
    unset_method = False
    show_param_list = []
    set_param_list = []
    unset_param_list = []
    list_of_next_components = []

    def __init__(self, name):
        self.name = name
        self.param_list = []
        self.show_method = False
        self.set_method = False
        self.unset_method = False
        self.show_param_list = []
        self.set_param_list = []
        self.unset_param_list = []
        self.list_of_next_components = []


classes_list = Component("root")


def get_component_obj(label, list_of_component_objects):
    for component_obj in list_of_component_objects:
        if component_obj.name == label:
            return component_obj
    return None


def get_last_split_label(str_to_split):
    split_param_path = str_to_split.split('/')
    return split_param_path[len(split_param_path) - 1]


def get_list_of_params(partial_dictionary):
    list_params = []
    if PARAMS_KEY in partial_dictionary.keys():
        param_list = partial_dictionary[PARAMS_KEY]
        for param in param_list:
            param_name = get_last_split_label(list(param.values())[0])
            if param_name not in LIST_OF_PARAMS_TO_IGNORE and param_name not in list_params:
                list_params.append(param_name)
    return list_params


def update_component_data(component_obj, component_data):
    list_of_component_data_keys = component_data.keys()

    if GET_KEY in list_of_component_data_keys:
        component_obj.show_method = True
        component_obj.show_param_list.extend(get_list_of_params(component_data[GET_KEY]))

    if PATCH_KEY in list_of_component_data_keys:
        component_obj.set_method = True
        component_obj.set_param_list.extend(get_list_of_params(component_data[PATCH_KEY]))

    if DELETE_KEY in list_of_component_data_keys:
        component_obj.unset_method = True
        component_obj.unset_param_list.extend(get_list_of_params(component_data[DELETE_KEY]))


def add_classes_to_dictionary(component_data, split_label):
    temp_ptr = classes_list

    for label in split_label:
        if label.startswith('{') and label.endswith('}'):
            temp_label = label.strip('{}')
            if temp_label not in temp_ptr.param_list:
                temp_ptr.param_list.append(temp_label)
            continue
        component_ptr = get_component_obj(label, temp_ptr.list_of_next_components)
        if not component_ptr:
            new_component = Component(label)
            if split_label.index(label) == len(split_label) - 1:
                update_component_data(new_component, component_data)
            temp_ptr.list_of_next_components.append(new_component)
            temp_ptr = temp_ptr.list_of_next_components[0]
        else:
            temp_ptr = component_ptr
