# import all libraries required
import json, os, sys
from azureml.core import Workspace, Model, Environment
from azureml.core.model import InferenceConfig
from azureml.core.webservice import AciWebservice
from azureml.core.authentication import AzureCliAuthentication

def read_config(config_file):
    # read config file
    with open(config_file, encoding='utf-8-sig') as f:
        return json.load(f)['aci']['configuration']

def read_model_config(config_file):
    # read model config file
    with open(config_file, encoding='utf-8-sig') as f:
        return json.load(f)['model']['configuration']

def deploy_model_to_aci(aci_config, model_config):
    # Authenticate using CLI
    cli_auth = AzureCliAuthentication()
    # Get workspace
    ws = Workspace.from_config(auth=cli_auth)

    # Get the model, model must exist otherwise can't continue
    model_name = model_config['name']
    model_version = model_config['version']
    model = Model(ws, name=model_name, version=model_version)

    # Get inference config
    inference_config = aci_config['inference_config']
    # Get environment (if specified)
    env_name = {}
    if 'environment' in inference_config:
        env_name = inference_config['environment']
    if env_name:
        env = Environment.get(ws, name=env_name)
        # replace inference_config['environment'] with environment object
        inference_config['environment'] = env
    # set inference config
    inference_configuration = InferenceConfig(**inference_config)

    # Get deployment config
    deploy_config = aci_config['deploy_configuration']
    aci_configuration = AciWebservice.deploy_configuration(**deploy_config)

    # Get service configuration
    service_name = aci_config['name']
    service_overwrite = aci_config['overwrite']

    # Deploy the webservice
    service = Model.deploy(
        workspace=ws,
        name=service_name,
        models=[model],
        inference_config=inference_configuration,
        deployment_config=aci_configuration,
        overwrite=service_overwrite
    )
    service.wait_for_deployment(show_output=True)

    # Print ACI details
    print(service.__dict__)

    # return service information
    return {
        'aci_name': service.name,
        'aci_scoring_uri': service.scoring_uri
    }

def save_aci_config(aci, folder):
    # save json file
    os.makedirs(folder, exist_ok=True)
    with open(folder + '/aci.json', "w+") as outfile:
        json.dump(aci, outfile)

def main():
    args = sys.argv[1:]

    if len(args) >= 2 and args[0] == '-config':
        # execute load config file and model registration
        aci_config = read_config(args[1])
        model_config = read_model_config(args[1])
        # deploy model to ACI
        aci = deploy_model_to_aci(aci_config, model_config)
        # save datasets to aml_config (default)
        out_folder = 'aml_config'
        if len(args) >= 4 and args[2] == '-outfolder':
            out_folder = args[3]
        save_aci_config(aci, out_folder)
    else:
        print('Usage: -config <config file name> [-outfolder <Azure ML config folder>]')
    
if __name__ == '__main__':
    main()