# import all libraries required
import os, json, sys
from azureml.core import Workspace, PrivateEndPointConfig
from azureml.core.authentication import AzureCliAuthentication

def read_config(config_file):
    # read config file
    with open(config_file, encoding='utf-8-sig') as f:
        return json.load(f)['workspace']['configuration']

def create_workspace(ws_config):
    # authenticate using CLI
    cli_auth = AzureCliAuthentication()
    # create private end point config
    if 'private_endpoint_config' in ws_config:
        ws_private_endpoint_config = ws_config['private_endpoint_config']
        if ws_private_endpoint_config:
            private_endpoint_config = PrivateEndPointConfig(
                name = ws_private_endpoint_config['name'],
                vnet_name = ws_private_endpoint_config['vnet_name'],
                vnet_subnet_name = ws_private_endpoint_config['vnet_subnet_name'],
                vnet_subscription_id = ws_private_endpoint_config['vnet_subscription_id'],
                vnet_resource_group = ws_private_endpoint_config['vnet_resource_group'],
            )
            ws_config['private_endpoint_config'] = private_endpoint_config
        else:
            ws_config['private_endpoint_config'] = None
    # create/register workspace
    ws = Workspace.create(
        auth = cli_auth,
        **ws_config
    )
    return ws

def get_workspace(ws_config):
    # authenticate using CLI
    cli_auth = AzureCliAuthentication()
    # get config settings
    ws_name = ws_config['name']
    ws_subscription_id = ws_config['subscription_id']
    ws_rg = ws_config['resource_group']
    ws_location = ws_config['location']
    # get existing workspace, throw error if not exist
    print(f'Getting existing ML workspace {ws_name}')
    ws = Workspace.get(
        name=ws_name, 
        auth=cli_auth, 
        subscription_id=ws_subscription_id, 
        resource_group=ws_rg, 
        location=ws_location
    )
    print(f'Existing ML workspace {ws_name} found')
    return ws

def save_workspace_config(workspace, folder):
    # create json format
    ws_json = {}
    ws_json['subscription_id'] = workspace.subscription_id
    ws_json['resource_group'] = workspace.resource_group
    ws_json['workspace_name'] = workspace.name
    ws_json['location'] = workspace.location
    # save json file
    os.makedirs(folder, exist_ok=True)
    with open(folder + '/config.json', "w+") as outfile:
        json.dump(ws_json, outfile)

def main():
    args = sys.argv[1:]
    print('args: ', args)
    if len(args) >= 2 and args[0] == '-config':
        # execute load config file and workspace creation
        ws_config = read_config(args[1])
        
        # if creation allowed, use create_workspace
        # otherwise, use get_workspace
        #ws = create_workspace(ws_config)
        ws = get_workspace(ws_config)

        # print Workspace details
        print(ws.subscription_id, ws.resource_group, ws.name, ws.location, sep="\n")
        # save workspace to aml_config (default)
        out_folder = 'aml_config'
        if len(args) >= 4 and args[2] == '-outfolder':
            out_folder = args[3]
        save_workspace_config(ws, out_folder)
    else:
        print('Usage: -config <config file name> [-outfolder <Azure ML config folder>]')

if __name__ == '__main__':
    main()