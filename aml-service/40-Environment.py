# import all libraries required
import os, json, sys
from azureml.core import Workspace, Environment
from azureml.core.authentication import AzureCliAuthentication

# Authenticate using CLI
cli_auth = AzureCliAuthentication()

def read_config(config_file):
    # read config file
    with open(config_file, encoding='utf-8-sig') as f:
        return json.load(f)['environment']['configuration']

def register_environment(env_config):
    # Get workspace
    ws = Workspace.from_config(auth=cli_auth)
    # Get environment configuration from yml file
    env_name = env_config['name']
    env_file = env_config['file_path']
    env = Environment.from_conda_specification(env_name, env_file)
    # Register the enviromnment
    env.register(workspace=ws)
    print (f'Environment {env_name} registered.')
    # return the dataset information
    return {"environment_name": env_name,
            "environment_file": env_file}

def save_environment_config(envs, folder):
    # save json file
    os.makedirs(folder, exist_ok=True)
    with open(folder + '/environment.json', "w+") as outfile:
        json.dump(envs, outfile)

def main():
    args = sys.argv[1:]

    if len(args) >= 2 and args[0] == '-config':
        # execute load config file and environment registration
        env_configs = read_config(args[1])
        # register each environment
        envs = []
        for env_config in env_configs:
            env = register_environment(env_config)
            # collect all registered datasets
            envs.append(env)
        # save datasets to aml_config (default)
        out_folder = 'aml_config'
        if len(args) >= 4 and args[2] == '-outfolder':
            out_folder = args[3]
        save_environment_config(envs, out_folder)
    else:
        print('Usage: -config <config file name> [-outfolder <Azure ML config folder>]')
    
if __name__ == '__main__':
    main()