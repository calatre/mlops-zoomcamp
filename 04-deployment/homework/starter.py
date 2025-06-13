#!/usr/bin/env python
# coding: utf-8

import pickle
import pandas as pd
import argparse


#parametrizing the script to accept year and month as command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('-y', '--year', type=int, help='Year')
parser.add_argument('-m', '--month', type=int, help='Month')

args = parser.parse_args()

print(f'Year: {args.year}')
print(f'Month: {args.month}')

year = args.year #2023
month = args.month

with open('model.bin', 'rb') as f_in:
    dv, model = pickle.load(f_in)


categorical = ['PULocationID', 'DOLocationID']

def read_data(year, month):
    filename = f'https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year:04d}-{month:02d}.parquet'
    print(f'Reading data from {filename}')

    df = pd.read_parquet(filename)

    df['duration'] = df.tpep_dropoff_datetime - df.tpep_pickup_datetime
    df['duration'] = df.duration.dt.total_seconds() / 60

    df = df[(df.duration >= 1) & (df.duration <= 60)].copy()

    df[categorical] = df[categorical].fillna(-1).astype('int').astype('str')

    return df


df = read_data(year, month)


dicts = df[categorical].to_dict(orient='records')
X_val = dv.transform(dicts)
y_pred = model.predict(X_val)


df['prediction'] = y_pred
df['prediction'].describe()

print(f'Predictions:\n{df["prediction"].describe()}')

df['ride_id'] = f'{year:04d}/{month:02d}_' + df.index.astype('str')

df_result = df[['ride_id','prediction']]

output_file = f'./data/output-{year:04d}-{month:02d}.parquet'

df_result.to_parquet(
    output_file,
    engine='pyarrow',
    compression=None,
    index=False
)

