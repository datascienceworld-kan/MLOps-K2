# import all libraries required
import os, json, sys
from azureml.core import Workspace
from azureml.core.datastore import Datastore
from azureml.exceptions import UserErrorException
from azureml.core.authentication import AzureCliAuthentication
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

# Authenticate using CLI
cli_auth = AzureCliAuthentication()

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
        return json.load(f)['datastore']['configuration']

def register_datastore(datastore_type, datastore_config):
    # Remove the 'type' key as it's not part of the function
    datastore_config.pop('type', None)
    
    # Execute the relevant datastore registration function
    if datastore_type.lower() == 'azure_blob_container':
        datastore = register_azure_blob_container(datastore_type, datastore_config)
    elif datastore_type.lower() == 'azure_data_lake_gen2':
        datastore = register_azure_data_lake_gen2(datastore_type, datastore_config)
    elif datastore_type.lower() == 'azure_sql_database':
        datastore = register_azure_sql_database(datastore_type, datastore_config)
    else:
        print("No compatible datastore type found, datastore NOT registered")
    return datastore
    
def register_azure_blob_container(datastore_type, datastore_config):
    # Get workspace
    ws = Workspace.from_config(auth=cli_auth)
    # Check datastore exist, if yes, use it, if not, register
    dstore_name = datastore_config['datastore_name']
    try:
        blob_datastore = Datastore.get(ws, dstore_name)
        print(f"Found Azure Blob Container Datastore with name: {dstore_name}")
    except UserErrorException:
        # get secret values from keyvault if applicable
        secret_key = ['account_name', 'sas_token', 'account_key', 'subscription_id']
        for sk in secret_key:
            if sk in datastore_config:
                sv = get_config_value(datastore_config[sk])
                if sv:
                    datastore_config[sk] = sv
                else:
                    datastore_config[sk] = None
        # Register blob container as datastore
        blob_datastore = Datastore.register_azure_blob_container(workspace = ws, **datastore_config)
        print(f"Registered Azure Blob Container Datastore with name: {dstore_name}")
    # Show datastore details
    print(blob_datastore)
    # Return the registered datastore
    return {
        'datastore_name': dstore_name,
        'datastore_type': datastore_type,
    }
    
def register_azure_data_lake_gen2(datastore_type, datastore_config):
    # Get workspace
    ws = Workspace.from_config(auth=cli_auth)
    # Check datastore exist, if yes, use it, if not, register
    dstore_name = datastore_config['datastore_name']
    try:
        adls2_datastore = Datastore.get(ws, dstore_name)
        print(f"Found Azure Data Lake Gen2 Datastore with name: {dstore_name}")
    except UserErrorException:
        # get secret values from keyvault if applicable
        secret_key = ['account_name', 'tenant_id', 'client_id', 'client_secret', 'subscription_id']
        for sk in secret_key:
            if sk in datastore_config:
                sv = get_config_value(datastore_config[sk])
                if sv:
                    datastore_config[sk] = sv
                else:
                    datastore_config[sk] = None
        # register azure data lake gen2 as datastore
        adls2_datastore = Datastore.register_azure_data_lake_gen2(workspace = ws, **datastore_config)
        print(f"Registered Azure Data Lake Gen2 Datastore with name: {dstore_name}")
    # Show datastore details
    print({"name": adls2_datastore.name, "datastore_type": adls2_datastore.datastore_type})
    # Return the registered datastore
    return {
        'datastore_name': dstore_name,
        'datastore_type': datastore_type,
    }
    
def register_azure_sql_database(datastore_type, datastore_config):
    # Get workspace
    ws = Workspace.from_config(auth=cli_auth)
    # Check datastore exist, if yes, use it, if not, register
    dstore_name = datastore_config['datastore_name']
    try:
        sql_datastore = Datastore.get(ws, dstore_name)
        print(f"Found Azure SQL Database Datastore with name: {dstore_name}")
    except UserErrorException:
        # get secret values from keyvault if applicable
        secret_key = ['server_name', 'database_name', 'tenant_id', 'client_id', 'client_secret', 
                      'username', 'password', 'subscription_id']
        for sk in secret_key:
            if sk in datastore_config:
                sv = get_config_value(datastore_config[sk])
                if sv:
                    datastore_config[sk] = sv
                else:
                    datastore_config[sk] = None
        # register azure data lake gen2 as datastore
        sql_datastore = Datastore.register_azure_sql_database(workspace = ws, **datastore_config)
        print(f"Registered Azure SQL Database Datastore with name: {dstore_name}")
    # Show datastore details
    print({"name": sql_datastore.name, "datastore_type": sql_datastore.datastore_type})
    # Return the registered datastore
    return {
        'datastore_name': dstore_name,
        'datastore_type': datastore_type,
    }
    
def save_datastore_config(datastores, folder):
    # save json file
    os.makedirs(folder, exist_ok=True)
    with open(folder + '/datastore.json', "w+") as outfile:
        json.dump(datastores, outfile)

def main():
    args = sys.argv[1:]
    print('args: ', args)
    if len(args) >= 2 and args[0] == '-config':
        # execute load config file and datastore creation
        dstore_configs = read_config(args[1])
        # register each datastore
        dstores = []
        for dstore_config in dstore_configs:
            dstore = register_datastore(dstore_config['type'], dstore_config)
            # append datastore to the list
            dstores.append(dstore)
        # save datastore to aml_config (default)
        out_folder = 'aml_config'
        if len(args) >= 4 and args[2] == '-outfolder':
            out_folder = args[3]
        save_datastore_config(dstores, out_folder)
    else:
        print('Usage: -config <config file name> [-outfolder <Azure ML config folder>]')
    
if __name__ == '__main__':
    main()