# import all libraries required
import os, json, sys
from azureml.core import Workspace, Datastore, Dataset
from azureml.core.authentication import AzureCliAuthentication

def read_config(config_file):
    # read config file
    with open(config_file, encoding='utf-8-sig') as f:
        return json.load(f)['tabular_dataset']['configuration']

def register_tabular_dataset(dset_from, dset_config):
    print(dset_config)
    # Authenticate using CLI
    cli_auth = AzureCliAuthentication()
    # Get workspace
    ws = Workspace.from_config(auth=cli_auth)
    print('workspace: \n', ws)
    # remove the 'from' key
    dset_config.pop('from', None)
    # call the register dataset based on the source type
    if dset_from.lower() == 'delimited_files':
        input = dset_config['path']
        dataset = register_delimited_files_dataset(dset_config, ws)
    elif dset_from.lower() == 'parquet_files':
        input = dset_config['path']
        dataset = register_parquet_files_dataset(dset_config, ws)
    elif dset_from.lower() == 'sql_query':
        input = dset_config['query']
        dataset = register_sql_query_dataset(dset_config, ws)
    else:
        print("No compatible dataset type found, dataset NOT registered")
    if 'dataset' in locals():
        # Register the dataset
        dataset.register(ws, dset_config['name'], 
                         description=dset_config['description'], 
                         tags=dset_config['tags'],
                         create_new_version=True)
        print('Tabular dataset {} registered.'.format(dset_config['name']))
        print(dset_config)
        # return the dataset information
        return {"dataset_name": dset_config['name'],
                "dataset_from": dset_from,
                "dataset_input": input,
                "datastore_name": dset_config['datastore_name']}
    else:
        return {}

def set_param_dict(param_keys, param_dict):
    """Create the correct parameter dictionary for passing to functions"""
    output = {}
    for k in param_keys:
        if k in param_dict:
            output[k] = param_dict[k]
    return output

def register_delimited_files_dataset(dset_config, workspace):
    """Register a Tabular dataset using delimited files"""
    # Get datastore (must exist first otherwise will throw error
    dstore = Datastore.get(workspace, dset_config['datastore_name'])
    path = dset_config['path']
    # assign the right path object
    dset_config['path'] = (dstore, path)
    # Upload file
    dstore.upload_files(files=['./data/insurance.csv'],
                       target_path='data/',
                       overwrite=True)
    print('completed upload file ./data/insurance.csv')
    # Get the keys for this function
    param_keys = ['path', 'validate', 'include_path', 'infer_column_types', 'set_column_types',
                  'separator', 'header', 'partition_format', 'support_multi_line', 'empty_as_string', 'encoding']
    param_dict = set_param_dict(param_keys, dset_config)
    # Set dataset
    dset = Dataset.Tabular.from_delimited_files(**param_dict)
    return dset

def register_parquet_files_dataset(dset_config, workspace):
    """Register a Tabular dataset using Parquet files"""
    # Get datastore (must exist first otherwise will throw error
    dstore = Datastore.get(workspace, dset_config['datastore_name'])
    path = dset_config['path']
    # assign the right path object
    dset_config['path'] = (dstore, path)
    # Get the keys for this function
    param_keys = ['path', 'validate', 'include_path', 'set_column_types', 'partition_format']
    param_dict = set_param_dict(param_keys, dset_config)
    # Set dataset
    dset = Dataset.Tabular.from_parquet_files(**param_dict)
    return dset

def register_sql_query_dataset(dset_config, workspace):
    """Register a Tabular dataset using SQL query"""
    # Get datastore (must exist first otherwise will throw error
    dstore = Datastore.get(workspace, dset_config['datastore_name'])
    query = dset_config['query']
    # assign the right query object
    dset_config['query'] = (dstore, query)
    # Get the keys for this function
    param_keys = ['query', 'validate', 'set_column_types', 'query_timeout']
    param_dict = set_param_dict(param_keys, dset_config)
    # Set dataset
    dset = Dataset.Tabular.from_sql_query(**param_dict)
    return dset

def save_dataset_config(datasets, folder):
    # save json file
    os.makedirs(folder, exist_ok=True)
    with open(folder + '/tabular_dataset.json', "w+") as outfile:
        json.dump(datasets, outfile)

def main():
    args = sys.argv[1:]

    if len(args) >= 2 and args[0] == '-config':
        # execute load config file and dataset registration
        dset_configs = read_config(args[1])
        # register each dataset
        dsets = []
        for dset_config in dset_configs:
            dset = register_tabular_dataset(dset_config['from'], dset_config)
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