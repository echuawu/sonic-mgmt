import os.path
import yaml
import sys
from FilesGenerator import *
from ComponentObjGenerator import *

PATH_TO_PARTIAL_YAML_FILE = "partial.yaml"


def create_init_py_file(base_directory):
    path_to_init_file = base_directory + '/__init__.py'
    if not os.path.isfile(path_to_init_file):
        init_file = open(path_to_init_file, 'w')
        init_file.close()


def create_classes_file():
    try:
        for root_class in classes_list.list_of_next_components:
            base_directory = create_base_directory(root_class.name)
            create_init_py_file(base_directory)
            define_classes(root_class, root_class.name, base_directory)
    except Exception as ex:
        print('ERROR: Failed to create python classes')
        raise ex


def create_classes(data_dictionary):
    print("Parsing provided yaml file:")
    for component_key in data_dictionary.keys():
        print('Parsing data - {}'.format(component_key))
        split_label = list(filter(None, component_key.replace('-', '_').split('/')))
        add_classes_to_dictionary(data_dictionary[component_key], split_label)

    print('\nCreating python classes in relevant directories')
    create_classes_file()

    print('Relevant classes were created in python_classes.py file')


def main():
    print('Script started - yaml to class generator\n')

    if not os.path.isfile(PATH_TO_PARTIAL_YAML_FILE):
        print('{} file not found'.format(PATH_TO_PARTIAL_YAML_FILE))

    with open(PATH_TO_PARTIAL_YAML_FILE, 'r') as stream:
        try:
            data_dictionary = yaml.safe_load(stream)
        except Exception as ex:
            print("ERROR - Failed to read yaml file")
            print(ex)

        if not data_dictionary or len(data_dictionary.keys()) == 0:
            print('Failed to read partial.yaml file')
        else:
            create_classes(data_dictionary)

    print('Script completed')


if __name__ == '__main__':
    sys.exit(main())
