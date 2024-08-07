## We used Apache Airflow, Apache Kafka and other tools to construct a robust data pipeline capable of streaming large volumes of real-time data. Our pipeline is configured to perform API calls every 10 minutes, ensuring continuous data collection and access to the latest information on bike availability. 

## We preprocessed the collected data, preparing it for analysis and visualization. This data was then integrated into a dashboard web application, facilitating easy access and interaction. 

## We visualized the processed data using interactive plots that display bike availability at 10-minute intervals. These plots allow us to analyze trends and patterns in bike usage over time, providing valuable insights into demand and operational efficiency. 



### Here is the steps.

Please run our data pipeline following the instructions below. 

1.Prerequisite.  I believe you have installed python on your computer. For this project, you must install Docker on your computer. Please download this link:https://www.docker.com/products/docker-desktop/ 

2.please start the docker. 

3.Download the whole project to your computer. 

4.In the terminal, please navigate to this folder and use this command 

 " docker compose up -d" 

waiting for the docker containers to start. You will first see they are pulling and then created and healthy. You can see those containers in the docker desktop. 

5.When the docker starts to work. Type the “http://localhost:8080” in your chrome. Input the name "admin", password "admin", you will see the airflow task is on the page. 

6.Created the connection between your airflow and AWS S3 bucket. In the UI of airflow, in the “admin” (head bar), click connection. Please set the connection’s name as “data_608”, type is “Amazon Web Services”, then fill your AWS access key and secret key in the required position. Then click save at the bottom. 

7.Change the bucket name in the code. Inside “main.py” (located in the project’s subfolder “dags”), please modify the line 228 

s3_hook.load_bytes(buffer.getvalue(), key=s3_path, bucket_name='test-608-project', replace=True) 

Please replace the “bucket_name” as the bucket you want to store the data in your AWS. 

8.Go to AWS Glue to create a crawler. Point the crawler to the S3 bucket’s folder containing the files, create database and point crawler to database. 

9.Run crawler to create schema. 

10.The following steps will use the file in the folder “dashboard”. Add files all_locations.csv and result_key.txt to a folder inside the S3 bucket. 

11.Create an EC2 instance, install Python and dependencies using requirements.txt, add dash_app.py and athena_query.py to the instance. 

12.Add a rule to your instance to allow inbound traffic on port 8050. 

13.Run athena_query.py first and then dash_app.py. 

14.Use the instance public IP address to open the web app in your browser. 

Steps 13 and 14 can be run on a local computer as well.  
