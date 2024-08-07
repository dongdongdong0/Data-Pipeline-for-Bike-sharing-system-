import csv
import requests
import time
import string
import random
import json
import pandas as pd
import os
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer
from io import BytesIO
import boto3


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


def write_json(city_data, city, request_time):
    data_to_write = []
    try:
        for station in city_data['network']['stations']:
            data_to_write.append({
                "request_id": get_id(city),
                "timestamp": station['timestamp'],
                "_id": get_id(''.join(station['name'].split()) + '-'),
                "date": get_datetime(request_time).strftime('%Y-%m-%d'),
                "day_name": get_datetime(request_time).strftime('%A'),
                "hour": get_datetime(request_time).strftime('%H:%M'),
                "city": city,
                "station_id": station['id'],
                "station_name": station['name'],
                "free_bikes": station['free_bikes'],
                "empty_slots": station['empty_slots']
            })
        return data_to_write
    except Exception as e:
        message = f"An error occurred while creating JSON data for {city}: {e}"
        request_id = get_id(city)
        success = 'NO JSON created'
        write_logger(request_id, request_time, success, message)
        print(message)


# Generate id
def get_id(loc, length=8):
    try:
        characters = string.ascii_letters + string.digits
        random_id = ''.join(random.choices(characters, k=length))
        return loc + '-' + random_id
    except Exception as e:
        print(f"An error occurred while generating ID: {e}")
        return None



def app():
  producer = KafkaProducer(bootstrap_servers=['localhost:9092'], max_block_ms=5000)
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
            # success = 'Yes'
            # message = f'Successful request for {city}'
            # write_logger(request_id, request_time, success, message,data_dir)

            # get data
            city_data = response[1]
            # json file
            data_to_write = write_json(city_data, city, request_time)

            producer.send("city_bikes", value=json.dumps(data_to_write).encode('utf-8'))
            # write to database
            #write_database(city_data, city, request_time, data_dir)
            # final print
            message = f'app.py run succesfully at {get_request_time_full(request_time)}'
            print(message)
            # write to logger
            success = 'App-executed'
            #write_logger(request_id, request_time, success, message, data_dir)
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
  finally:
      # Ensure the producer is closed and resources are released
      producer.close()




def from_consumer():
    data = []
    consumer = KafkaConsumer(
        'city_bikes',
        bootstrap_servers=['localhost:9092'],
        auto_offset_reset='earliest',
        group_id='test-group'
    )

    message_count = 0
    max_messages = 3
    try:
        for msg in consumer:
            try:
                records = json.loads(msg.value.decode('utf-8'))
                data.extend(records)
            except json.JSONDecodeError as e:
                print(f"Error decoding message: {e}")
            message_count += 1
            if message_count == max_messages:
                break
    except Exception as e:
        print(f"Error consuming messages: {e}")
    finally:
        consumer.close()

    return data
def upload_data_to_s3(data, bucket_name, prefix='', aws_access_key_id='your_access_key',
                      aws_secret_access_key='your_secret_key'):
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name='us-east-1'  # 根据你的 S3 bucket 位置选择合适的区域
    )

    df = pd.DataFrame(data)


    buffer = BytesIO()
    df.to_parquet(buffer, index=False)

    buffer.seek(0)
    parquet_data = buffer.getvalue()


    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{prefix}{timestamp}.parquet"

    try:
        response = s3.put_object(Bucket=bucket_name, Key=filename, Body=parquet_data)
        print("Data uploaded successfully")
        return response
    except Exception as e:
        print(f"Failed to upload data: {e}")


app()
data_to_write = from_consumer()
bucket_name = 'mybikedata608'

upload_data_to_s3(data_to_write, bucket_name, prefix='data/', aws_access_key_id=aws_access_key_id,
                  aws_secret_access_key=aws_secret_access_key)






