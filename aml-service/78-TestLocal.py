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

def inference_local_webservice(local_service):
    sample_input = json.dumps({'data': [[0,1,8,1,0,0,1,0,0,0,0,0,0,0,12,1,0,0,0.5,0.3,0.610327781,7,1,-1,0,-1,1,1,1,2,1,65,1,0.316227766,0.669556409,0.352136337,3.464101615,0.1,0.8,0.6,1,1,6,3,6,2,9,1,1,1,12,0,1,1,0,0,1],[4,2,5,1,0,0,0,0,1,0,0,0,0,0,5,1,0,0,0.9,0.5,0.771362431,4,1,-1,0,0,11,1,1,0,1,103,1,0.316227766,0.60632002,0.358329457,2.828427125,0.4,0.5,0.4,3,3,8,4,10,2,7,2,0,3,10,0,0,1,1,0,1]]})
    print('----------------local scoring uri: \n', local_service.scoring_uri)
    print('----------------local service name: \n', local_service.name)
    print('----------------request sample: \n', sample_input)
    output = local_service.run(sample_input)
    print('----------------output: \n', output)
    return output

def test_local(local_config, model_config):
    # Authenticate using CLI
    cli_auth = AzureCliAuthentication()
    # Get workspace
    ws = Workspace.from_config(auth=cli_auth)

    # Get the model, model must exist otherwise can't continue
    model_name = model_config['name']
    model_version = model_config['version']
    model = Model(ws, name=model_name, version=model_version)

    # Get Local service name
    local_name = local_config['name']
    local_service = LocalWebservice(ws, local_name)    
    output = inference_local_webservice(local_service)

    # return test successful
    return output

def main():
    args = sys.argv[1:]

    if len(args) >= 2 and args[0] == '-config':
        # execute load config file and model registration
        local_config = read_config(args[1])
        model_config = read_model_config(args[1])
        # test model on local
        pass_test = test_local(local_config, model_config)
        if pass_test:
            print('Local pass testing')
        else:
            sys.exit('Local failed testing')
    else:
        print('Usage: -config <config file name> [-outfolder <Azure ML config folder>]')
    
if __name__ == '__main__':
    main()