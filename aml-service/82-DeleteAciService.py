# import all libraries required
import json, sys, math
import pandas as pd
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from azureml.core import Workspace, Model, Dataset
from azureml.core.webservice import Webservice
from azureml.core.authentication import AzureCliAuthentication

def read_config(config_file):
    # read config file
    with open(config_file, encoding='utf-8-sig') as f:
        return json.load(f)['aci']['configuration']

def read_model_config(config_file):
    # read model config file
    with open(config_file, encoding='utf-8-sig') as f:
        return json.load(f)['model']['configuration']

def read_model_test_config(config_file):
    # read model test config file
    with open(config_file, encoding='utf-8-sig') as f:
        return json.load(f)['model']

def delete_aci(aci_config):
    # Authenticate using CLI
    cli_auth = AzureCliAuthentication()
    # Get workspace
    ws = Workspace.from_config(auth=cli_auth)

    # Get ACI service name
    aci_name = aci_config['name']
    try:
        aci_service = Webservice(ws, aci_name)    
        aci_service.delete()
        print('Complete delete aci_service')
    except:
        print('Cannot delete because aci_service is not exist!')

def main():
    args = sys.argv[1:]

    if len(args) >= 2 and args[0] == '-config':
        # execute load config file and model registration
        local_config = read_config(args[1])
        # delete model on aci
        delete_aci(local_config)
    else:
        print('Usage: -config <config file name> [-outfolder <Azure ML config folder>]')
    
if __name__ == '__main__':
    main()