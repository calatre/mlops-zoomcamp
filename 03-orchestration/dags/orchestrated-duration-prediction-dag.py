#!/usr/bin/env python
# coding: utf-8

"""
This script defines an Airflow DAG for orchestrating the training of a machine learning model to predict NYC taxi trip durations.
It includes tasks for setting up the environment, loading and preparing data, feature engineering, training the model with XGBoost, and validating the model performance using MLflow for experiment tracking.

Used Claude Sonnet 4 for first draft.
"""

from datetime import datetime, timedelta
import pickle
from pathlib import Path

import pandas as pd
import xgboost as xgb
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import root_mean_squared_error
import mlflow

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.models import Variable


# Default arguments for the DAG
default_args = {
    'owner': 'ml-team',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
dag = DAG(
    'nyc_taxi_duration_prediction',
    default_args=default_args,
    description='Train ML model to predict NYC taxi trip duration',
    schedule='@monthly',  # Run monthly
    catchup=False,
    max_active_runs=1,
    tags=['ml', 'xgboost', 'mlflow', 'taxi'],
)


def setup_environment(**context):
    """Setup MLflow and create necessary directories"""
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("nyc-taxi-experiment")
    
    models_folder = Path('models')
    models_folder.mkdir(exist_ok=True)
    
    print("Environment setup completed")


def read_dataframe(year, month):
    """Read and preprocess taxi data"""
    url = f'https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_{year}-{month:02d}.parquet'
    df = pd.read_parquet(url)

    df['duration'] = df.lpep_dropoff_datetime - df.lpep_pickup_datetime
    df.duration = df.duration.apply(lambda td: td.total_seconds() / 60)

    df = df[(df.duration >= 1) & (df.duration <= 60)]

    categorical = ['PULocationID', 'DOLocationID']
    df[categorical] = df[categorical].astype(str)

    df['PU_DO'] = df['PULocationID'] + '_' + df['DOLocationID']

    return df


def load_and_prepare_data(**context):
    """Load training and validation data"""
    # Get parameters from Airflow Variables or use defaults
    year = int(Variable.get("training_year", default_var=2024))
    month = int(Variable.get("training_month", default_var=1))
    
    print(f"Loading data for year: {year}, month: {month}")
    
    # Load training data
    df_train = read_dataframe(year=year, month=month)
    
    # Calculate next month for validation data
    next_year = year if month < 12 else year + 1
    next_month = month + 1 if month < 12 else 1
    df_val = read_dataframe(year=next_year, month=next_month)
    
    # Save dataframes for next tasks
    df_train.to_parquet('/tmp/df_train.parquet')
    df_val.to_parquet('/tmp/df_val.parquet')
    
    print(f"Training data shape: {df_train.shape}")
    print(f"Validation data shape: {df_val.shape}")
    
    return {"train_shape": df_train.shape, "val_shape": df_val.shape}


def create_X(df, dv=None):
    """Create feature matrix"""
    categorical = ['PU_DO']
    numerical = ['trip_distance']
    dicts = df[categorical + numerical].to_dict(orient='records')

    if dv is None:
        dv = DictVectorizer(sparse=True)
        X = dv.fit_transform(dicts)
    else:
        X = dv.transform(dicts)

    return X, dv


def prepare_features(**context):
    """Prepare features for training"""
    # Load dataframes
    df_train = pd.read_parquet('/tmp/df_train.parquet')
    df_val = pd.read_parquet('/tmp/df_val.parquet')
    
    # Create feature matrices
    X_train, dv = create_X(df_train)
    X_val, _ = create_X(df_val, dv)
    
    # Prepare target variables
    target = 'duration'
    y_train = df_train[target].values
    y_val = df_val[target].values
    
    # Save preprocessed data
    with open('/tmp/X_train.pkl', 'wb') as f:
        pickle.dump(X_train, f)
    with open('/tmp/X_val.pkl', 'wb') as f:
        pickle.dump(X_val, f)
    with open('/tmp/y_train.pkl', 'wb') as f:
        pickle.dump(y_train, f)
    with open('/tmp/y_val.pkl', 'wb') as f:
        pickle.dump(y_val, f)
    with open('/tmp/dv.pkl', 'wb') as f:
        pickle.dump(dv, f)
    
    print(f"Feature preparation completed")
    print(f"X_train shape: {X_train.shape}")
    print(f"X_val shape: {X_val.shape}")


def train_model(**context):
    """Train XGBoost model with MLflow tracking"""
    # Load preprocessed data
    with open('/tmp/X_train.pkl', 'rb') as f:
        X_train = pickle.load(f)
    with open('/tmp/X_val.pkl', 'rb') as f:
        X_val = pickle.load(f)
    with open('/tmp/y_train.pkl', 'rb') as f:
        y_train = pickle.load(f)
    with open('/tmp/y_val.pkl', 'rb') as f:
        y_val = pickle.load(f)
    with open('/tmp/dv.pkl', 'rb') as f:
        dv = pickle.load(f)
    
    with mlflow.start_run() as run:
        train = xgb.DMatrix(X_train, label=y_train)
        valid = xgb.DMatrix(X_val, label=y_val)

        best_params = {
            'learning_rate': 0.09585355369315604,
            'max_depth': 30,
            'min_child_weight': 1.060597050922164,
            'objective': 'reg:linear',
            'reg_alpha': 0.018060244040060163,
            'reg_lambda': 0.011658731377413597,
            'seed': 42
        }

        mlflow.log_params(best_params)

        booster = xgb.train(
            params=best_params,
            dtrain=train,
            num_boost_round=30,
            evals=[(valid, 'validation')],
            early_stopping_rounds=50
        )

        y_pred = booster.predict(valid)
        rmse = root_mean_squared_error(y_val, y_pred)
        mlflow.log_metric("rmse", rmse)

        # Save preprocessor
        models_folder = Path('models')
        models_folder.mkdir(exist_ok=True)
        
        with open("models/preprocessor.b", "wb") as f_out:
            pickle.dump(dv, f_out)
        mlflow.log_artifact("models/preprocessor.b", artifact_path="preprocessor")

        # Log model
        mlflow.xgboost.log_model(booster, artifact_path="models_mlflow")

        run_id = run.info.run_id
        
        # Save run_id for potential downstream tasks
        with open("run_id.txt", "w") as f:
            f.write(run_id)
        
        print(f"MLflow run_id: {run_id}")
        print(f"RMSE: {rmse}")
        
        return run_id


def validate_model(**context):
    """Validate the trained model performance"""
    with open("run_id.txt", "r") as f:
        run_id = f.read().strip()
    
    # You can add model validation logic here
    # For example, checking if RMSE is below a threshold
    print(f"Validating model with run_id: {run_id}")
    
    # Example validation logic
    client = mlflow.tracking.MlflowClient()
    run = client.get_run(run_id)
    rmse = run.data.metrics.get('rmse')
    
    if rmse and rmse < 10.0:  # Example threshold
        print(f"Model validation passed. RMSE: {rmse}")
        return True
    else:
        raise ValueError(f"Model validation failed. RMSE: {rmse}")


# Define tasks
setup_task = PythonOperator(
    task_id='setup_environment',
    python_callable=setup_environment,
    dag=dag,
)

load_data_task = PythonOperator(
    task_id='load_and_prepare_data',
    python_callable=load_and_prepare_data,
    dag=dag,
)

prepare_features_task = PythonOperator(
    task_id='prepare_features',
    python_callable=prepare_features,
    dag=dag,
)

train_model_task = PythonOperator(
    task_id='train_model',
    python_callable=train_model,
    dag=dag,
)

validate_model_task = PythonOperator(
    task_id='validate_model',
    python_callable=validate_model,
    dag=dag,
)

# Optional: Clean up temporary files
cleanup_task = BashOperator(
    task_id='cleanup_temp_files',
    bash_command='rm -f /tmp/df_train.parquet /tmp/df_val.parquet /tmp/X_*.pkl /tmp/y_*.pkl /tmp/dv.pkl',
    dag=dag,
)

# Define task dependencies
setup_task >> load_data_task >> prepare_features_task >> train_model_task >> validate_model_task >> cleanup_task