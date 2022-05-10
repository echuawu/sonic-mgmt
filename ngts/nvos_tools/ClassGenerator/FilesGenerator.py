import os


def add_imports(component, py_class_file, root_class_name):
    py_class_file.write('import allure\n')
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
    py_class_file.write('        with allure.step(\'{method_name}\'):\n'.format(
        method_name=method_name))
    py_class_file.write('            return ResultObj(True)\n\n')


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


def create_base_directory(root_class_name):
    base_directory = os.getcwd().replace("/ClassGenerator", "")
    path_to_class_directory = r'{base_directory}/{root_component}'.format(root_component=root_class_name,
                                                                          base_directory=base_directory)
    if not os.path.isdir(path_to_class_directory):
        os.mkdir(path_to_class_directory)

    return path_to_class_directory


def create_class_file_in_relevant_directory(component, base_directory):
    py_class_file = open(base_directory + '/{class_name}.py'.format(class_name=component.name.capitalize()),
                         'a')
    return py_class_file


def define_classes(component, root_class_name, base_directory):
    py_class_file = create_class_file_in_relevant_directory(component, base_directory)
    print('Creating {class_name} - {path_to_class}'.format(class_name=component.name.capitalize(),
                                                           path_to_class=py_class_file.name))
    try:
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

        py_class_file.close()
        print('*** {class_name} class was successfully created ({path_to_class})'.format(
            class_name=component.name.capitalize(),
            path_to_class=py_class_file.name))

        for next_component in component.list_of_next_components:
            define_classes(next_component, root_class_name, base_directory)

    except BaseException:
        py_class_file.close()
