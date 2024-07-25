import csv
import requests
import time
import string
import random

import os
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

"""
This program sends a get request to an API, cleans the response, and write it in a csv file.
"""

endpoints = {
    "Vancouver": "http://api.citybik.es/v2/networks/mobibikes",
    "Toronto": "http://api.citybik.es/v2/networks/bixi-toronto",
    "Montreal": "http://api.citybik.es/v2/networks/bixi-montreal"
}

data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')

def fetch_data(city, endpoint):
    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        return (True, response.json())
    except requests.exceptions.HTTPError as http_err:
        message = f'HTTP error occurred for {city}: {http_err}'
    except requests.exceptions.ConnectionError as conn_err:
        message = f'Connection error occurred for {city}: {conn_err}'
    except requests.exceptions.Timeout as timeout_err:
        message = f'Timeout error occurred for {city}: {timeout_err}'
    except requests.exceptions.RequestException as req_err:
        message = f'Request exception occurred for {city}: {req_err}'
    return (False, message)


# request time
def get_request_time_full(timestamp):
    my_dt = datetime.fromtimestamp(timestamp)
    return my_dt.strftime('%Y-%m-%d %H:%M:%S')


# Logger
def write_logger(request_id, request_time, success, message, data_dir):
    logger_file_path = os.path.join(data_dir, 'logger.csv')
    try:
        with open(logger_file_path, 'a', newline='') as logger:
            logger_writer = csv.writer(logger)
            logger_writer.writerow(
                [request_id, get_request_time_full(request_time), success, message]
            )
    except Exception as e:
        print(f"An error occurred while writing to the log file: {e}")


# get datetime
def get_datetime(timestamp):
    return datetime.fromtimestamp(timestamp)


# Write to database
def write_database(city_data, city, request_time, data_dir):
    csv_file_path = os.path.join(data_dir, f'{city}_bikes.csv')
    try:
        with open(csv_file_path, 'a', newline='') as file:
            # Create a CSV writer object
            writer = csv.writer(file)

            # Write data rows
            for station in city_data['network']['stations']:
                writer.writerow([
                    get_id(city),  # request_id
                    station['timestamp'],  # timestamp
                    get_id(''.join(station['name'].split()) + '-'),  # _id
                    get_datetime(request_time).strftime('%Y-%m-%d'),  # date
                    get_datetime(request_time).strftime('%A'),  # day_name
                    get_datetime(request_time).strftime('%H:%M'),  # hour
                    city,  # city
                    station['id'],  # station_id
                    station['name'],  # station_name
                    station['free_bikes'],  # free_bikes
                    station['empty_slots']  # empty_slots
                ])
    except Exception as e:
        print(f"An error occurred while writing to the database: {e}")


# Generate id
def get_id(loc, length=8):
    try:
        characters = string.ascii_letters + string.digits
        random_id = ''.join(random.choices(characters, k=length))
        return loc + '-' + random_id
    except Exception as e:
        print(f"An error occurred while generating ID: {e}")
        return None


# app
def app():
  try:
    for city, endpoint in endpoints.items():
        # get data
        response = fetch_data(city, endpoint)

        # request_id
        request_id = get_id(city)
        # time
        request_time = time.time()

        if response[0]:
            # write to logger
            success = 'Yes'
            message = f'Successful request for {city}'
            write_logger(request_id, request_time, success, message,data_dir)

            # get data
            city_data = response[1]
            # write to database
            write_database(city_data, city, request_time, data_dir)
            # final print
            message = f'app.py run succesfully at {get_request_time_full(request_time)}'
            print(message)
            # write to logger
            success = 'App-executed'
            write_logger(request_id, request_time, success, message, data_dir)
        else:
            # error message
            message = response[1]
            success = 'No'
            # write to logger
            write_logger(request_id, request_time, success, message)
  except Exception as e:
    e_message = f"An unexpected error occurred in the main loop: {e} "
    print(e_message)
    success = 'App-execution-problem'
    write_logger(request_id, request_time, success, e_message, data_dir)

app()


default_args = {
    'owner': 'diego',
    'start_date': datetime(2024, 7, 23, 10, 00),
}

with DAG('user_automation',
         default_args=default_args,
         schedule_interval='*/10 * * * *',
         catchup=False) as dag:

    streaming_task = PythonOperator(
        task_id='bike_data_api',
        python_callable=app
    )