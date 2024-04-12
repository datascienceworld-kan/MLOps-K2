# MLOps-K2

# About teacher

<p align="center">
  <img src="https://imgur.com/KN1SGVr.png" style="width: 50%;">
</p>

# Introduction

This is a tutorial repo of Course 5 - Machine Learning in Production - MLOps organized by DataScienceWorld.Kan.
Its' oriented target towards building an Azure DevOps CI/CD pipeline that comprises the steps as follows:
1. Setup infrastructure over Azure ML workspace
2. Connect to Azure ML workspace
3. Running register Dataset and Datastore
4. Training a machine learning model
5. Endpoint deployment of machine learning model
6. Test model performance.

# Infrastructure

<img src="https://learn.microsoft.com/en-us/azure/architecture/ai-ml/idea/_images/many-models-machine-learning-azure.png#lightbox"></img>

Source: [Azure Machine Learning Architecture](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/idea/many-models-machine-learning-azure-machine-learning)

# Setup Infrastructure as Code via ARM template file

To manipulate datasets and train models you need to initialize an AzureML working space as a priority. The [Lession 9 - Part II - Deploying infrastructure as code](https://youtu.be/NtFypy2DTvM) has provided a hands-on guideline for your to complete this. 

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
