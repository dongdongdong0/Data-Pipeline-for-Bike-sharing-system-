import boto3
import time
import pandas as pd

def run_athena_query(query, database, output_location, region='us-east-2'):
    try:
        # Initialize a session using Amazon Athena
        session = boto3.Session(region_name=region)
        
        # Initialize Athena client
        athena_client = session.client('athena')
        
        # Start the query execution
        response = athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': database},
            ResultConfiguration={'OutputLocation': output_location}
        )
        
        # Get the query execution ID
        query_execution_id = response['QueryExecutionId']
        
        # Wait for the query to complete
        while True:
            response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
            status = response['QueryExecution']['Status']['State']
            if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
            time.sleep(1)  # Sleep for a while before polling again
        
        if status == 'SUCCEEDED':
            # Initialize list to store rows and set the token to None initially
            rows = []
            column_info = None
            next_token = None
            
            while True:
                # Get the results with pagination
                if next_token:
                    result_response = athena_client.get_query_results(QueryExecutionId=query_execution_id, NextToken=next_token)
                else:
                    result_response = athena_client.get_query_results(QueryExecutionId=query_execution_id)
                
                # Get the column info
                if not column_info:
                    column_info = result_response['ResultSet']['ResultSetMetadata']['ColumnInfo']
                
                # Parse the results and load into the list
                for row in result_response['ResultSet']['Rows'][1:]:  # Skip header row on first iteration
                    data = [col.get('VarCharValue', None) for col in row['Data']]
                    rows.append(data)
                
                # Check if there is a next token
                next_token = result_response.get('NextToken')
                if not next_token:
                    break
            
            # Create DataFrame
            df = pd.DataFrame(rows, columns=[col['Name'] for col in column_info])
            
            # Get the output location of the results
            output_location = response['QueryExecution']['ResultConfiguration']['OutputLocation']
            
            return df, output_location, result_response
        else:
            raise Exception(f"Query {status}: {response['QueryExecution']['Status']['StateChangeReason']}")
    
    except boto3.exceptions.Boto3Error as e:
        print(f"Boto3 Error: {e}")
        return None, None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None

# Usage example:
query = 'SELECT * FROM "my_database"."my_table";'  # Replace with your actual query
database = 'my_database'  # Replace with your actual database name
output_location = 's3://my_bucket/my_folder/'  # Replace with your actual S3 output location
my_bucket = 'my_bucket'  # Replace with your actual bucket name

# Run the Athena query and get the results
df, result_key, result_response = run_athena_query(query, database, output_location)
if df is not None and result_key is not None:
    print(f'Result key pre {result_key}')
    result_key = result_key.replace(f's3://{my_bucket}/', '')
    print(f'result key after {result_key}')

    # If 'city' column exists, print unique values
    if 'city' in df.columns:
        print(df['city'].unique())

    # Write the result key to a local text file
    with open('my_folder/result_key.txt', 'w') as f:
        f.write(result_key)
else:
    print("Query failed.")
