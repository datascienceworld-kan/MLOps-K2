# import all libraries required
import os, json, sys
from azureml.core import Workspace, Environment, Experiment, Datastore, Dataset
from azureml.core.authentication import AzureCliAuthentication
from azureml.core.compute import ComputeTarget
from azureml.core.compute_target import ComputeTargetException
from azureml.core.runconfig import RunConfiguration
from azureml.pipeline.steps import PythonScriptStep
from azureml.pipeline.core import Pipeline, PipelineData, PipelineEndpoint, PublishedPipeline, Schedule, ScheduleRecurrence, TimeZone
# add additional libraries required for your pipeline

# Authenticate using CLI
cli_auth = AzureCliAuthentication()

# Get workspace
ws = Workspace.from_config(auth=cli_auth)

def read_config(config_file):
    # read config file
    with open(config_file, encoding='utf-8-sig') as f:
        return json.load(f)['pipeline']['configuration']

def create_pipeline(pipeline_config):
    """This pipeline is specific for insurance model training"""
    # Get some variables required for this pipeline
    pipeline_name = pipeline_config['name']
    compute_name = pipeline_config['compute_name']
    env_name = pipeline_config['environment_name']
    exp_name = pipeline_config['experiment_name']
    publish = pipeline_config['publish_pipeline']
    run = pipeline_config['run_pipeline']
    schedule_config = pipeline_config['schedule']
    # Get pipeline parameter
    input_dataset_name = pipeline_config['parameter']['dataset_name']
    output_model_name = pipeline_config['parameter']['output_model_name']
    feature_list_names = pipeline_config['parameter']['feature_list_names']
    target = pipeline_config['parameter']['target_column']
    model_hyps = str(pipeline_config['parameter']['model_hyperparameters'])

    # Get the target compute
    try:
        pipeline_cluster = ComputeTarget(ws, compute_name)
    except ComputeTargetException as e:
        print(e)
        sys.exit(f'Compute target {compute_name} not found!')

    # Create a new runconfig object for the pipeline
    pipeline_run_config = RunConfiguration()

    # Use the compute above
    pipeline_run_config.target = pipeline_cluster

    # Get existing environment, if not registered, exit
    if env_name:
        try:
            registered_env = Environment.get(ws, env_name)
        except Exception as e:
            print(e)
            sys.exit(f'Environment {env_name} not found!')

        # Assign the environment to the run configuration
        pipeline_run_config.environment = registered_env

    # python scripts folder
    train_folder = 'training'
    print("train_folder:", train_folder)

    # Get the pipeline dataset
    dataset = Dataset.get_by_name(ws, name=input_dataset_name)
    
    # train and test splits step
    default_store = ws.get_default_datastore() 
    output_split_train = PipelineData("output_split_train", datastore=default_store).as_dataset()
    output_split_test = PipelineData("output_split_test", datastore=default_store).as_dataset()
    test_train_splitting_step = PythonScriptStep(
        name="Split data to train and test data",
        script_name="train_test_split.py", 
        arguments=["--output_split_train", output_split_train,
                   "--output_split_test", output_split_test],
        inputs=[dataset.as_named_input('input_dataset')],
        outputs=[output_split_train, output_split_test],
        compute_target=pipeline_cluster,
        runconfig=pipeline_run_config,
        source_directory=train_folder,
        allow_reuse=False
    )

    print("test_train_splitting_step created.")

    # model train step
    print("Model hypeparameters: ", model_hyps)
    model_training_step = PythonScriptStep(
        name="Train and evaluate model",
        script_name="train.py",
        inputs=[output_split_train.parse_parquet_files(),
                output_split_test.parse_parquet_files()],
        arguments=['--output-model-name', output_model_name,
                   '--feature-list-names', feature_list_names,
                   '--target', target],
        compute_target=pipeline_cluster,
        runconfig=pipeline_run_config,
        source_directory=train_folder,
        allow_reuse=False
    )

    print("model_training_step created.")

    # Construct the pipeline
    pipeline_steps = [test_train_splitting_step, model_training_step]
    pipeline = Pipeline(workspace=ws, steps=pipeline_steps)
    print('Pipeline is built.')

    # Publish pipeline if required
    published_pipeline = None
    published_pipeline_endpoint = None
    schedule = None
    if publish:
        published_pipeline = publish_pipeline(pipeline, pipeline_name)
        published_pipeline_endpoint = publish_pipeline_endpoint(published_pipeline)
        # Schedule if required
        if schedule_config:
            schedule = schedule_pipeline(published_pipeline.id, exp_name, schedule_config)

    # set published pipeline info
    published_pipeline_id = None
    published_pipeline_status = None
    # published_pipeline_endpoint = None
    if published_pipeline:
        published_pipeline_id = published_pipeline.id
        published_pipeline_status = published_pipeline.status
        # published_pipeline_endpoint = published_pipeline.endpoint
    
    # set schedule info
    schedule_id = None
    schedule_name = None
    schedule_status = None
    if schedule:
        schedule_id = schedule.id
        schedule_name = schedule.name
        schedule_status = schedule.status
    
    # Execute pipline if required
    pipeline_run = None
    if run:
        pipeline_endpoint_by_name = PipelineEndpoint.get(workspace=ws, name=published_pipeline_endpoint.name)
        pipeline_run_name = published_pipeline_endpoint.name+'-run'
        pipeline_run = pipeline_endpoint_by_name.submit(pipeline_run_name)
        print('Pipeline submitted for execution.')
        # Wait for pipeline completion (optional)
        pipeline_run.wait_for_completion(show_output=True)
    
    return {
        "pipeline_name": pipeline_name,
        "published": {
            "id": published_pipeline_id,
            "status": published_pipeline_status,
            "endpoint": published_pipeline_endpoint.endpoint if published_pipeline_endpoint else None,
            "scheduled": {
                "id": schedule_id,
                "name": schedule_name,
                "status": schedule_status,
            }
        },
        "run": {
            "experiment_name": exp_name,
            "id": pipeline_run.id if run else None
        }
    }

def publish_pipeline(pipeline, name):
    """This is to publish the pipeline"""
    # Get list of all published pipelines
    published_pipelines = PublishedPipeline.list(ws)
    # Disable if same name found
    for published_pipeline in published_pipelines:
        if published_pipeline.name == name:
            # disable schedule first, if exist
            schedules = Schedule.list(ws, pipeline_id=published_pipeline.id)
            for schedule in schedules:
                schedule.disable()
            # disable published pipeline
            published_pipeline.disable()
    # Publish the pipeline
    published_pipeline = pipeline.publish(name=name, description=name)
    # end update
    print(f'Pipeline {name} published with id {published_pipeline.id}.')
    return published_pipeline

def publish_pipeline_endpoint(pipeline):
    pipeline_name = pipeline.name
    pipeline_endpoint_name = pipeline_name+'-endpoint'
    pipeline_desc = 'pipeline of insurance model training'
    try:
        pipeline_endpoint = PipelineEndpoint.get(workspace=ws, name=pipeline_endpoint_name)
        pipeline_endpoint.add(pipeline)
        pipeline_endpoint = update_default_pipeline_endpoint(pipeline_endpoint)
    except:
        print('pipeline endpoint {} not exists!'.format(pipeline_endpoint_name))
        pipeline_endpoint = PipelineEndpoint.publish(workspace=ws, name=pipeline_endpoint_name,
                                                pipeline=pipeline, description=pipeline_desc)
    return pipeline_endpoint

def update_default_pipeline_endpoint(pipeline_endpoint):
    all_versions = pipeline_endpoint.list_versions()
    last_idx_version = len(all_versions)-1
    pipeline_endpoint.set_default_version(str(last_idx_version))
    return pipeline_endpoint

def schedule_pipeline(pipeline_id, experiment_name, schedule_config):
    """This is to schedule the pipeline"""
    # get the schedule config
    schedule_name = schedule_config['name']

    # create Recurrence object if not empty
    if 'recurrence' in schedule_config:
        schedule_recurrence = schedule_config['recurrence']
        recurrence = None
        if schedule_recurrence:
            if 'time_zone' in schedule_recurrence:
                tz = schedule_recurrence['time_zone']
                if tz:
                    schedule_recurrence['time_zone'] = TimeZone[tz]
            recurrence = ScheduleRecurrence(**schedule_recurrence)
        schedule_config['recurrence'] = recurrence

    # create Datastore object if not empty
    if 'datastore' in schedule_config:
        schedule_datastore = schedule_config['datastore']
        datastore = None
        if schedule_datastore:
            datastore = Datastore(ws, name=schedule_datastore)
        schedule_config['datastore'] = datastore

    # check if schedule already exists
    schedules = Schedule.list(ws, pipeline_id=pipeline_id)
    for schedule in schedules:
        if schedule.name == schedule_name:
            schedule.update(**schedule_config)
            print(f'Schedule {schedule_name} with id {schedule.id} updated.')
            return schedule

    # create schedule if not exists
    schedule = Schedule.create(ws, pipeline_id=pipeline_id, experiment_name=experiment_name, **schedule_config)
    print(f'Schedule {schedule_name} with id {schedule.id} created.')
    return schedule

def save_pipeline_config(pipeline, folder, index):
    # save as json file
    os.makedirs(folder, exist_ok=True)
    # json file
    file_path = folder + '/pipeline.json'
    # if index = 0, write new file, else append
    pipelines = []
    if index > 0:
        # read existing file, if exist
        if os.path.exists(file_path):
            with open (file_path, 'r') as f:
                pipelines = json.load(f)
    # go through the existing pipelines and replace
    config_exist = False
    for i in range(len(pipelines)):
        if pipelines[i]['pipeline_name'] == pipeline['pipeline_name']:
            pipelines[i] = pipeline
            config_exist = True
            break
    # append the pipeline if config doesn't exist
    if not config_exist:
        pipelines.append(pipeline)
    # Save the pipeline config
    with open(file_path, "w+") as outfile:
        json.dump(pipelines, outfile)

def main():
    args = sys.argv[1:]

    if len(args) >= 4 and args[0] == '-config' and args[2] == '-pipeline':
        # execute load config file, pipeline creation, and publish pipeline
        pipeline_configs = read_config(args[1])

        # save pipelines to aml_config (default)
        out_folder = 'aml_config'
        if len(args) >= 6 and args[4] == '-outfolder':
            out_folder = args[5]

        # iterate through the pipeline configs, 
        for i in range(len(pipeline_configs)):
            if pipeline_configs[i]['name'] == args[3]:
                # create pipeline
                pipeline = create_pipeline(pipeline_configs[i])
                # save pipeline configuration
                save_pipeline_config(pipeline, out_folder, i)
                # stop the loop
                break
    else:
        print('Usage: -config <config file name> -pipeline <pipeline name> [-outfolder <Azure ML config folder>]')
    
if __name__ == '__main__':
    main()