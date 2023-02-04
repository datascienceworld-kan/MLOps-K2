# import all libraries required
import os, json, sys
from azureml.core import Workspace, LinkedService, SynapseWorkspaceLinkedServiceConfiguration
from azureml.core.compute import AmlCompute, ComputeTarget, ComputeInstance, DatabricksCompute, SynapseCompute
from azureml.core.compute_target import ComputeTargetException
from azureml.core.authentication import AzureCliAuthentication
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

# Authenticate using CLI
cli_auth = AzureCliAuthentication()

# Get workspace
ws = Workspace.from_config(auth=cli_auth)

def get_keyvault_secret_value(keyvault_name, keyvault_secret_name):
    credential = DefaultAzureCredential()
    kv_url = f'https://{keyvault_name}.vault.azure.net'
    kv_client = SecretClient(vault_url=kv_url, credential=credential)
    return kv_client.get_secret(keyvault_secret_name).value

def get_config_value(config_value):
    value = None
    if config_value != None:
        if type(config_value) is dict:
            value = get_keyvault_secret_value(config_value['keyvault_name'], config_value['secret_name'])
        else:
            value = config_value
    return value

def read_config(config_file):
    # read config file
    with open(config_file, encoding='utf-8-sig') as f:
        return json.load(f)['compute']['configuration']

def create_compute(compute_config):
    # get compute type
    compute_type = compute_config['type']
    # create/register compute type accordingly
    if compute_type.lower() == "amlcompute":
        compute = create_amlcompute(compute_config['name'], compute_config['provisioning_configuration'])
    elif compute_type.lower() == "computeinstance":
        compute = create_computeinstance(compute_config['name'], compute_config['provisioning_configuration'], compute_config['start'])
    elif compute_type.lower() == "databricks":
        compute = register_databricks(compute_config['name'], compute_config['attach_configuration'])
    elif compute_type.lower() == "synapse":
        compute = register_synapse(compute_config['name'], compute_config['attach_configuration'])
    else:
        print("No compatible compute type found, compute target NOT created")
    return compute
    
def create_amlcompute(name, config):
    # Check compute exist, if yes, use it, if not, create
    try:
        compute_cluster = ComputeTarget(workspace=ws, name=name)
        print(f'Found existing AMLCompute cluster {name}, use it.')
    except ComputeTargetException:
        # get secret values from keyvault if applicable
        admin_key = ['admin_username', 'admin_user_password', 'admin_user_ssh_key']
        for ak in admin_key:
            if ak in config:
                av = get_config_value(config[ak])
                if av:
                    config[ak] = av
                else:
                    config[ak] = None
        # set compute config
        prov_config = AmlCompute.provisioning_configuration(**config)
        # create new compute cluster
        compute_cluster = ComputeTarget.create(ws, name, prov_config)
        # wait for completion
        compute_cluster.wait_for_completion(show_output = True)
    # print compute details
    print(compute_cluster.get_status().serialize())
    # return compute details
    return {"compute_name": compute_cluster.name,
            "compute_type": 'amlcompute',
            "vm_size": compute_cluster.vm_size,
            "min_node": compute_cluster.scale_settings.minimum_node_count,
            "max_node": compute_cluster.scale_settings.maximum_node_count,
            "location": compute_cluster.location}
    
def create_computeinstance(name, config, start_instance):
    # Check compute exist, if yes, use it, if not, create
    try:
        compute_instance = ComputeInstance(workspace=ws, name=name)
        print(f'Found existing compute instance {name}')
        compute_instance_detail = compute_instance.get_status().serialize()
        print('State:', compute_instance_detail['state'].lower())
        if compute_instance_detail['state'].lower() == 'createfailed':
            print(f'Try to delete {name}')
            compute_instance.delete(wait_for_completion=True)
            raise ComputeTargetException(f'compute instance {name} was created unseccessfully')
    except ComputeTargetException:
        # set compute instance config
        print(f'Attemp to create {name}')
        prov_config = ComputeInstance.provisioning_configuration(**config)
        # create new compute instance
        compute_instance = ComputeTarget.create(ws, name, prov_config)
        # wait for completion
        compute_instance.wait_for_completion(show_output = True)
    compute_instance_detail = compute_instance.get_status().serialize()
    # print compute details
    
    print(compute_instance_detail)
    return {"compute_name": compute_instance.name,
            "compute_type": 'computeinstance',
            "vm_size": compute_instance.vm_size,
            "location": compute_instance.location}

def register_databricks(name, config):
    # Check compute exists, if yes, use it, if not, create
    try:
        compute_cluster = ComputeTarget(workspace=ws, name=name)
        print(f'Found existing Databricks compute {name}, use it.')
    except ComputeTargetException:
        # get secret values from keyvault if applicable
        if 'access_token' in config:
            access_token = get_config_value(config['access_token'])
            if access_token:
                config['access_token'] = access_token
            else:
                config['access_token'] = None
        # set compute config
        attach_config = DatabricksCompute.attach_configuration(**config)
        # register databricks compute
        compute_cluster = ComputeTarget.attach(ws, name, attach_config)
        # wait for completion
        compute_cluster.wait_for_completion(show_output = True)
    # print compute details
    print(compute_cluster.get_status())
    # return compute details
    return {
        "compute_name": compute_cluster.name,
        "compute_type": 'databricks',
        "databricks_workspace_name": config['workspace_name'],
        "databricks_resource_group": config['resource_group'],
    }

def register_synapse(name, config):
    # Check compute exists, if yes, use it, if not, create
    try:
        compute_cluster = ComputeTarget(workspace=ws, name=name)
        print(f'Found existing Synapse cluster {name}, use it.')
    except ComputeTargetException:
        # get linked service
        try:
            linked_service = LinkedService.get(ws, config['linked_service_name'])
            print(f'Found existing Synapse linked service {linked_service.name}, use it.')
        except:
            # create linked service configuration
            synapse_ws_linked_service_config = SynapseWorkspaceLinkedServiceConfiguration(
                subscription_id = config['subscription_id'],
                resource_group = config['resource_group'],
                name = config['synapse_name'],
            )
            # register linked service
            linked_service = LinkedService.register(ws, config['linked_service_name'], synapse_ws_linked_service_config)
        # set compute config
        attach_config = SynapseCompute.attach_configuration(
            linked_service = linked_service,
            type = config['type'],
            pool_name = config['pool_name'],
        )
        # register databricks compute
        compute_cluster = ComputeTarget.attach(ws, name, attach_config)
        # wait for completion
        compute_cluster.wait_for_completion(show_output = True)
    # print compute details
    print(compute_cluster.get_status())
    # return compute details
    return {
        "compute_name": compute_cluster.name,
        "compute_type": 'synapse',
        "synapse_name": config['synapse_name'],
        "synapse_spark_pool_name": config['pool_name'],
    }

def save_compute_config(computes, folder):
    # save as json file
    os.makedirs(folder, exist_ok=True)
    with open(folder + '/compute.json', "w+") as outfile:
        json.dump(computes, outfile)

def main():
    args = sys.argv[1:]

    if len(args) >= 2 and args[0] == '-config':
        # execute load config file and compute creation
        compute_configs = read_config(args[1])
        # create/register each compute
        computes = []
        for compute_config in compute_configs:
            compute = create_compute(compute_config)
            # collect all computes
            computes.append(compute)
        # save compute to aml_config (default)
        out_folder = 'aml_config'
        if len(args) >= 4 and args[2] == '-outfolder':
            out_folder = args[3]
        save_compute_config(computes, out_folder)
    else:
        print('Usage: -config <config file name> [-outfolder <Azure ML config folder>]')
    
if __name__ == '__main__':
    main()