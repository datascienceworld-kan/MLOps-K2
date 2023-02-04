# import all libraries required
import json, sys, math
import pandas as pd
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from azureml.core import Workspace, Model, Dataset
from azureml.core.webservice import LocalWebservice
from azureml.core.authentication import AzureCliAuthentication

def read_config(config_file):
    # read config file
    with open(config_file, encoding='utf-8-sig') as f:
        return json.load(f)['local_webservice']['configuration']

def read_model_config(config_file):
    # read model config file
    with open(config_file, encoding='utf-8-sig') as f:
        return json.load(f)['model']['configuration']

def read_model_test_config(config_file):
    # read model test config file
    with open(config_file, encoding='utf-8-sig') as f:
        return json.load(f)['model']

def delete_local(local_config):
    # Authenticate using CLI
    cli_auth = AzureCliAuthentication()
    # Get workspace
    ws = Workspace.from_config(auth=cli_auth)

    # Get Local service name
    local_name = local_config['name']
    try:
        local_service = LocalWebservice(ws, local_name)    
        local_service.delete()
    except:
        print('Cannot delete!')

def main():
    args = sys.argv[1:]

    if len(args) >= 2 and args[0] == '-config':
        # execute load config file and model registration
        local_config = read_config(args[1])
        # delete model on local
        delete_local(local_config)
    else:
        print('Usage: -config <config file name> [-outfolder <Azure ML config folder>]')
    
if __name__ == '__main__':
    main()