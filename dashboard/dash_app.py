import boto3
import pytz
import pandas as pd
from io import StringIO
from datetime import datetime, time, timedelta
from dash import Dash, html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

def read_csv_from_s3(bucket_name, key):
    # Initialize a session using Amazon S3
    s3 = boto3.client('s3')

    # Get the CSV file object
    csv_obj = s3.get_object(Bucket=bucket_name, Key=key)
    body = csv_obj['Body'].read().decode('utf-8')

    # Use StringIO to read the CSV data into a pandas DataFrame
    df = pd.read_csv(StringIO(body))

    return df

def read_txt_from_s3(bucket_name, key):
    # Initialize a session using Amazon S3
    s3 = boto3.client('s3')

    # Get the text file object
    txt_obj = s3.get_object(Bucket=bucket_name, Key=key)
    body = txt_obj['Body'].read().decode('utf-8')

    return body.strip()

# Convert UTC to Calgary time
def convert_to_calgary(series):
    # Define the UTC and Calgary time zones
    utc_tz = pytz.utc
    calgary_tz = pytz.timezone('America/Edmonton')  # Calgary is in the Mountain Time Zone

    # Initialize lists to store the converted values
    calgary_dates = []
    calgary_day_names = []
    calgary_times = []

    for timestamp in series:
        # Convert the timestamp string to a datetime object in UTC
        dt_utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        # Convert to Calgary time
        dt_calgary = dt_utc.astimezone(calgary_tz)

        # Extract the desired components
        calgary_dates.append(dt_calgary.date())
        calgary_day_names.append(dt_calgary.strftime('%A'))
        calgary_times.append(dt_calgary.time())  # Use time object directly

    # Create a DataFrame with the converted values
    df = pd.DataFrame({
        'Calgary_Date': calgary_dates,
        'Calgary_Day_Name': calgary_day_names,
        'Calgary_Hour': calgary_times
    })

    return df

# Usage example
bucket_name = 'my_bucket'  # General bucket name
result_key_path = 'my_folder/result_key.txt'  # General folder name
stations_key = 'my_folder/all_locations.csv'  # General folder name

# Read the data_key from the text file in S3
data_key = read_txt_from_s3(bucket_name, result_key_path)

# Read the CSV files from S3
data = read_csv_from_s3(bucket_name, data_key)
all_stations = read_csv_from_s3(bucket_name, stations_key)

# Coordinates for the cities
city_coords = {
    'Toronto': {'lat': 43.65107, 'lon': -79.347015},
    'Vancouver': {'lat': 49.282729, 'lon': -123.120738},
    'Montreal': {'lat': 45.501690, 'lon': -73.567253}
}

# Convert UTC to Calgary hour
temp_df = convert_to_calgary(data['timestamp'])

# Add converted columns to the main DataFrame
data['date'] = temp_df['Calgary_Date']
data['day_name'] = temp_df['Calgary_Day_Name']
data['hour'] = temp_df['Calgary_Hour']

app = Dash(__name__)

# Get unique day names for the RadioItems options
unique_days = data['day_name'].unique()

# Define the layout of the Dash app
app.layout = html.Div([
    html.Div([
        html.H1('Bike Sharing Systems', style={'text-align': 'center'}),
        
        dcc.Dropdown(
            id='select_city',                
            options=[
                {'label': 'Toronto', 'value': 'Toronto'},
                {'label': 'Vancouver', 'value': 'Vancouver'},
                {'label': 'Montreal', 'value': 'Montreal'}
            ],
            multi=False,
            value=None,
            style={'width': '40%', 'margin': 'auto'}
        ),
        
        dcc.Graph(id='map')
    ], style={'width': '80%', 'margin': 'auto'}),
    
    html.Div([
        html.H1('Selected Locations Trends', style={'text-align': 'center'}),

        dcc.RadioItems(
            id='day_radio',
            options=[{'label': day, 'value': day} for day in unique_days],
            value=None,  # Default to no days selected
            labelStyle={'display': 'inline-block', 'marginRight': 10}
        ),

        dcc.Graph(id='time_series')
    ], style={'width': '80%', 'margin': 'auto', 'marginTop': 50})
])

# Global variables to track selected stations and their city
selected_stations = []
current_city = None

def convert_hour(selected_city, datetime_series):
    # Define time zone offsets
    if selected_city == 'Vancouver':
        temp_series = datetime_series.apply(
            lambda x: (datetime.combine(datetime.today(), x) - timedelta(hours=1)).time()
        )
        return temp_series
    elif selected_city in ['Toronto', 'Montreal']:
        temp_series = datetime_series.apply(
            lambda x: (datetime.combine(datetime.today(), x) + timedelta(hours=2)).time()
        )
        return temp_series
    else:
        return datetime_series

# Callback to update the map based on the selected city
@app.callback(
    Output('map', 'figure'),
    [Input('select_city', 'value')]
)
def update_map(selected_city):
    fig = px.scatter_mapbox(
        all_stations,
        lat="latitude",
        lon="longitude",
        hover_name="station_name",
        hover_data=["station_id", "city"],
        color_discrete_sequence=["fuchsia"],
        zoom=3,
        height=500
    )
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    if selected_city:
        coords = city_coords[selected_city]
        fig.update_layout(mapbox_center={"lat": coords['lat'], "lon": coords['lon']})
        fig.update_layout(mapbox_zoom=10)
    
    return fig

# Callback to update the time series plot based on the selected station and day
@app.callback(
    Output('time_series', 'figure'),
    [Input('map', 'clickData'),
     Input('day_radio', 'value')]
)
def update_time_series(clickData, selected_day):
    global selected_stations, current_city
    
    # Number of stations to track
    n_stations = 1

    if clickData is None:
        return px.scatter()  # Return an empty plot

    station_id = clickData['points'][0]['customdata'][0]
    station_city = clickData['points'][0]['customdata'][1]  # Extract the city from clickData

    if station_city != current_city:
        selected_stations = []  # Reset selected stations if the city changes
        current_city = station_city

    if station_id not in selected_stations:
        if len(selected_stations) >= n_stations:
            selected_stations.pop(0)
        selected_stations.append(station_id)

    # Adjust filtering for single day
    filtered_data = data[(data['station_id'].isin(selected_stations)) & (data['day_name'] == selected_day)].copy()
    filtered_data['hour'] = convert_hour(current_city, filtered_data['hour'])
    
    # Sort the DataFrame by 'hour'
    filtered_data.sort_values(by='hour', inplace=True)
    
    # Create the time-series plot
    fig = px.line(filtered_data, x='hour', y='free_bikes', color='station_name', title='Trend for Selected Station', markers=True)
    fig.update_layout(
        xaxis_title='Hour',
        yaxis_title='Available Bikes',
        legend_title_text='Station Name'
    )
    fig.update_traces(mode='markers+lines')

    return fig

# Run the Dash app
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)
