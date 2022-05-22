import os.path
import yaml
import sys
from ngts.nvos_tools.ClassGenerator.FilesGenerator import create_base_directory, define_classes, create_init_py_file, create_cli_wrappers
from ngts.nvos_tools.ClassGenerator.ComponentObjGenerator import add_classes_to_dictionary, classes_list


PATH_TO_PARTIAL_YAML_FILE = "partial.yaml"


def create_files():
    try:
        for root_class in classes_list.list_of_next_components:
            print("> Creating files for {}".format(root_class.name))

            base_directory = create_base_directory(root_class.name)
            print("-infrastructure files will be created in '{}' directory".format(base_directory))

            print('-create __init__.py file')
            create_init_py_file(base_directory)

            print('-create classes')
            define_classes(root_class, root_class.name, base_directory)

            print('-add cli wrappers (nvue and openApi)')
            create_cli_wrappers(root_class.name)

    except Exception as ex:
        print('ERROR: Failed to create python classes')
        raise ex


def generate_required_files(data_dictionary):
    print("\n> Parsing provided yaml file:")
    for component_key in data_dictionary.keys():
        print('-parsing data - {}'.format(component_key))
        split_label = list(filter(None, component_key.replace('-', '_').split('/')))
        print("-generating classes")
        add_classes_to_dictionary(data_dictionary[component_key], split_label, component_key)

    print('\n> Creating python classes and cli wrappers in relevant directories')
    create_files()
    print('-created successfully')


def main():
    print('> Script started - yaml to class generator\n')

    print('> Searching for an input file - partial.yaml')
    if not os.path.isfile(PATH_TO_PARTIAL_YAML_FILE):
        print('{} file not found'.format(PATH_TO_PARTIAL_YAML_FILE))
    print('-input file found')

    with open(PATH_TO_PARTIAL_YAML_FILE, 'r') as stream:
        try:
            print('> Reading provided yaml file')
            data_dictionary = yaml.safe_load(stream)

            if not data_dictionary or len(data_dictionary.keys()) == 0:
                print('-failed to read partial.yaml file')
            else:
                generate_required_files(data_dictionary)

        except Exception as ex:
            print("ERROR - Failed to read yaml file")
            print(str(ex))
            exit(1)

    print('> Script completed successfully')


if __name__ == '__main__':
    sys.exit(main())
