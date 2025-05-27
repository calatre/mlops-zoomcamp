# Experiment Tracking

## 1.0 Introduction

[MLOps Zoomcap Chapter 2 ](https://github.com/DataTalksClub/mlops-zoomcamp/tree/main/02-experiment-tracking)

Great notes I'm following:

-[MLFlow on Minikube
](https://asfandqazi.substack.com/p/mlflow-on-minikube?r=2o17tf&utm_campaign=post&utm_medium=web&triedRedirect=true)

-[MLOps Zoomcamp 2025 Cohort notes by fonsecagabriella
](https://github.com/fonsecagabriella/ml_ops/blob/main/02_experiment_tracking/__notes.md)

### 1.1 Preparing the environment

For simplicity and because it's nice, will just use Minikube.

Create Python Environment
Use it in Jupyter notebook
Install the requirements (better in a requirements.txt) using pip or conda
Get the data
  

## 2.0 Tracking Experiments

We try different models with different conditions, parameters, data... and we often just keep track of it in a spreadsheet.
After a while this is not scalable or easily automatable.
For that, tools like MLFlow exist.

Also hyperopt to automate analysis of different hyperparameters.



### 2.1 Tracking Experiments with MLflow
After installing MLFlow and have the environment ready, you call it from your script/jupyter notebook, to log your experiments data.

My Notebook is here - check it for the details.

#### 2.1.1 Common commands:



## 3.0 MLflow Tracking UI

By default in my case, available on port 5000

## 4.0 Organizing Runs in Experiments



## 5.0 Best Practices for Experiment Tracking
