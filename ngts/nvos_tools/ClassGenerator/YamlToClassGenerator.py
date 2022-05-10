import yaml
import sys
import os.path

PATH_TO_PARTIAL_YAML_FILE = "partial.yaml"
PATH_TO_CLASSES_FILE = "python_classes.py"
GET_KEY = "get"
PATCH_KEY = "patch"
DELETE_KEY = "delete"
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
            temp_lable = label.strip('{}')
            if temp_lable not in temp_ptr.param_list:
                temp_ptr.param_list.append(temp_lable)
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


def add_imports(component, py_class_file, root_class_name):
    py_class_file.write('from ngts.nvos_tools.infra.ResultObj import ResultObj\n')
    if len(component.list_of_next_components) != 0:
        for component in component.list_of_next_components:
            py_class_file.write('from ngts.nvos_tools.{root_component}.{name} import {name}\n'.format(
                root_component=root_class_name, name=component.name.capitalize()))
    py_class_file.write('\n\n')


def add_inner_class_params(component, py_class_file):
    if len(component.list_of_next_components) != 0:
        for component in component.list_of_next_components:
            py_class_file.write('    {} = None\n'.format(component.name))


def add_method(method_name, params, py_class_file):
    param_str = ''
    for param in params:
        param_str += ', ' + param
    py_class_file.write('    def {method_name}(self{param_str}): \n'.format(method_name=method_name,
                                                                            param_str=param_str))
    py_class_file.write('        return ResultObj(True)\n\n')


def add_params(params, py_class_file):
    for param in params:
        py_class_file.write('    {param_name} = \'\'\n'.format(param_name=param))
    py_class_file.write('\n')


def add_init(component, py_class_file):
    param_list = []
    if len(component.list_of_next_components) != 0:
        for component in component.list_of_next_components:
            param_list.append(component.name)

    py_class_file.write('    def __init__(self):\n')
    for param in param_list:
        py_class_file.write('        self.{param} = {param_class}()\n'.format(param=param,
                                                                              param_class=param.capitalize()))
    if len(param_list) == 0:
        py_class_file.write('        pass\n')

    py_class_file.write('\n')


def define_classes(component, py_class_file, root_class_name):
    py_class_file.write('# ------------- {class_name} -------------- \n'.format(class_name=component.name.capitalize()))

    add_imports(component, py_class_file, root_class_name)
    py_class_file.write('class {class_name}:\n'.format(class_name=component.name.capitalize()))

    add_inner_class_params(component, py_class_file)

    add_params(component.param_list, py_class_file)

    add_init(component, py_class_file)

    if component.show_method:
        add_method('show', component.show_param_list, py_class_file)

    if component.set_method:
        add_method('set', component.set_param_list, py_class_file)

    if component.unset_method:
        add_method('unset', component.unset_param_list, py_class_file)

    for next_component in component.list_of_next_components:
        define_classes(next_component, py_class_file, root_class_name)


def create_classes_file():
    try:
        py_class_file = open(PATH_TO_CLASSES_FILE, 'w')
        for root_class in classes_list.list_of_next_components:
            define_classes(root_class, py_class_file, root_class.name)
        py_class_file.close()
    except Exception as ex:
        print('--------------------------------------')
        print('ERROR: Failed to create python classes')
        print('--------------------------------------')
        raise ex


def create_classes(data_dictionary):
    print("Parsing provided yaml file")
    for component_key in data_dictionary.keys():
        split_label = list(filter(None, component_key.replace('-', '_').split('/')))
        add_classes_to_dictionary(data_dictionary[component_key], split_label)

    print('Creating python classes in python_classes.py file')
    create_classes_file()

    print('Relevant classes were created in python_classes.py file')


def main():
    if not os.path.isfile(PATH_TO_PARTIAL_YAML_FILE):
        print('{} file not found'.format(PATH_TO_PARTIAL_YAML_FILE))

    with open(PATH_TO_PARTIAL_YAML_FILE, 'r') as stream:
        data_dictionary = yaml.safe_load(stream)
        if not data_dictionary or len(data_dictionary.keys()) == 0:
            print('Failed to read partial.yaml file')
        else:
            create_classes(data_dictionary)


if __name__ == '__main__':
    sys.exit(main())
