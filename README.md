# MLOps-K2

This is a repo to setup a CI/CD for MLOps course that organized by DataScienceWorld.Kan.
The target will be an Azure DevOps CI/CD pipeline that setup infrastructure over Azure ML workspace and run a test for training/test split dataset.

# Setup Azure-cli steps in CD

1. Get default workspace:

```
python aml-service/00-Workspace.py -config config/dev/config.json
```

2. Load datastore:

```
python aml-service/10-Datastore.py -config config/dev/config.json
```

3. Register Dataset:

```
python aml-service/22-TabularDataset.py -config config/dev/config.json
```

4. Initializing compute instances:

```
python aml-service/30-Compute.py -config config/dev/config.json
```

5. Register Environments:

```
python aml-service/40-Environment.py -config config/dev/config.json
```

6. Model training pipeline:

```
python aml-service/50-PipelineModelTraining.py -config config/dev/config.json -pipeline modeltraining
```

7. Model deployment Local service:

```
python aml-service/77-DeployToLocalService.py -config config/dev/config.json
```

8. Testing local deployment:

```
python aml-service/78-TestLocal.py -config config/dev/config.json
```

9. Delete local deployment:

```
python aml-service/79-DeleteLocalService.py -config config/dev/config.json
```

# Reference
This repo majorly refered from [MLOps-workshop](https://github.com/MG-Microsoft/MLOps_Workshop)   
