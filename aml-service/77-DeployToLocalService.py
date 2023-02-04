# import all libraries required
import json, os, sys
from azureml.core import Workspace, Model, Environment
from azureml.core.model import InferenceConfig
from azureml.core.webservice import LocalWebservice
from azureml.core.authentication import AzureCliAuthentication
import json

def read_config(config_file):
    # read config file
    with open(config_file, encoding='utf-8-sig') as f:
        return json.load(f)['local_webservice']['configuration']

def read_model_config(config_file):
    # read model config file
    with open(config_file, encoding='utf-8-sig') as f:
        return json.load(f)['model']['configuration']

def deploy_model_to_local(local_config, model_config):
    # Authenticate using CLI
    cli_auth = AzureCliAuthentication()
    # Get workspace
    ws = Workspace.from_config(auth=cli_auth)

    # Get the model, model must exist otherwise can't continue
    model_name = model_config['name']
    model_version = model_config['version']
    model = Model(ws, name=model_name, version=model_version)

    # Get inference config
    inference_config = local_config['inference_config']
    print('inference_config: ', inference_config)
    # Get environment (if specified)
    env_name = {}
    if 'environment' in inference_config:
        env_name = inference_config['environment']
    if env_name:
        env = Environment.get(ws, name=env_name)
        # replace inference_config['environment'] with environment object
        inference_config['environment'] = env
    # set inference config
    # inference_configuration = InferenceConfig(**inference_config)
    inference_configuration = InferenceConfig(source_directory=inference_config["source_directory"],
                                   entry_script=inference_config["entry_script"],
                                   environment=env)

    # Get deployment config
    deploy_config = local_config['deploy_configuration']
    local_configuration = LocalWebservice.deploy_configuration(**deploy_config)
    print('local_config: ', local_configuration)
    # Get service configuration
    service_name = local_config['name']
    service_overwrite = local_config['overwrite']

    # Deploy the webservice
    service = Model.deploy(
        workspace=ws,
        name=service_name,
        models=[model],
        inference_config=inference_configuration,
        deployment_config=local_configuration,
        overwrite=service_overwrite
    )
    service.wait_for_deployment(show_output=True)

    # Print ACI details
    print(service.__dict__)
    
    print("Local service successful created!")
    return {
        'local_name': service.name,
        'local_scoring_uri': service.scoring_uri
    }

def test_local_webservice(local_service):
    sample_input = json.dumps({'data': [[0,1,8,1,0,0,1,0,0,0,0,0,0,0,12,1,0,0,0.5,0.3,0.610327781,7,1,-1,0,-1,1,1,1,2,1,65,1,0.316227766,0.669556409,0.352136337,3.464101615,0.1,0.8,0.6,1,1,6,3,6,2,9,1,1,1,12,0,1,1,0,0,1],[4,2,5,1,0,0,0,0,1,0,0,0,0,0,5,1,0,0,0.9,0.5,0.771362431,4,1,-1,0,0,11,1,1,0,1,103,1,0.316227766,0.60632002,0.358329457,2.828427125,0.4,0.5,0.4,3,3,8,4,10,2,7,2,0,3,10,0,0,1,1,0,1]]})
    output = local_service.run(sample_input)
    return output

def save_aci_config(aci, folder):
    # save json file
    os.makedirs(folder, exist_ok=True)
    with open(folder + '/aci.json', "w+") as outfile:
        json.dump(aci, outfile)

def main():
    args = sys.argv[1:]

    if len(args) >= 2 and args[0] == '-config':
        # execute load config file and model registration
        local_config = read_config(args[1])
        model_config = read_model_config(args[1])
        # deploy model to local
        local = deploy_model_to_local(local_config, model_config)
        # save datasets to aml_config (default)
        out_folder = 'aml_config'
        if len(args) >= 4 and args[2] == '-outfolder':
            out_folder = args[3]
        save_aci_config(local, out_folder)
    else:
        print('Usage: -config <config file name> [-outfolder <Azure ML config folder>]')
    
if __name__ == '__main__':
    main()