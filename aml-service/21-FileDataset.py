# import all libraries required
import os, json, sys
from azureml.core import Workspace, Datastore, Dataset
from azureml.core.authentication import AzureCliAuthentication

def read_config(config_file):
    # read config file
    with open(config_file, encoding='utf-8-sig') as f:
        return json.load(f)['file_dataset']['configuration']


def register_file_dataset(dset_config):
    # Authenticate using CLI
    cli_auth = AzureCliAuthentication()
    # 1. Get workspace & datastore
    ws = Workspace.from_config(auth=cli_auth)
    dstore = Datastore.get(ws, dset_config['datastore_name'])

    # 2. Upload file
    path = dset_config['path']
    target_path = dset_config["target_path"]
    regist_name = dset_config["name"]
    dstore.upload_files(files = [path],
                        target_path = target_path,
                        overwrite = True,
                        show_progress = True)

    # 3. Register dataset
    # 3.1. Set the dataset path
    dset_config['path'] = (dstore, path)
    dset_file_args = ['path', 'validate', 'partition_format', 'is_file']
    dset_file_config = {}
    for a in dset_file_args:
        if a in dset_config:
            dset_file_config[a] = dset_config[a]
    # 3.2. Register dataset
    dset = Dataset.File.from_files(**dset_file_config)
    # Prepare register dataset arguments
    register_args = ['name', 'description', 'tags', 'create_new_version']
    register_config = {}
    for a in register_args:
        if a in dset_config:
            register_config[a] = dset_config[a]
    # Register the dataset
    dset.register(ws, **register_config, create_new_version=True)
    print('File dataset {} registered.'.format(dset_config['name']))
    # return the dataset information
    return {"dataset_name": dset_config['name'],
            "dataset_path": path,
            "datastore_name": dset_config['datastore_name']}

def save_dataset_config(datasets, folder):
    # save json file
    os.makedirs(folder, exist_ok=True)
    with open(folder + '/file_dataset.json', "w+") as outfile:
        json.dump(datasets, outfile)

def main():
    args = sys.argv[1:]

    if len(args) >= 2 and args[0] == '-config':
        # execute load config file and dataset registration
        dset_configs = read_config(args[1])
        # register each dataset
        dsets = []
        for dset_config in dset_configs:
            dset = register_file_dataset(dset_config)
            # collect all registered datasets
            dsets.append(dset)
        # save datasets to aml_config (default)
        out_folder = 'aml_config'
        if len(args) >= 4 and args[2] == '-outfolder':
            out_folder = args[3]
        save_dataset_config(dsets, out_folder)
    else:
        print('Usage: -config <config file name> [-outfolder <Azure ML config folder>]')
    
if __name__ == '__main__':
    main()