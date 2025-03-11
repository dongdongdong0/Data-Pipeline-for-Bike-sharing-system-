![Bike Sharing Pipeline Diagram](https://github.com/dongdongdong0/Data-Pipeline-for-Bike-sharing-system-/blob/main/data608.png?raw=true)

### **Project Overview**
This project implements a real-time data pipeline to collect and process bike-sharing trip data from multiple city APIs, updated every 10 minutes. Each run ingests approximately **4,000 records per API**, accumulating **1.2 MB of data per hour**. The pipeline leverages **Apache Airflow, Apache Kafka, AWS S3, and AWS Glue**, storing data in **Parquet format** for efficient querying and analysis. 

Deployed via **Docker**, the pipeline ensures **scalability and portability**. The processed data powers a **dynamic dashboard**, visualizing bike availability trends for operational insights. Additionally, the project integrates **Prometheus and Grafana** for real-time monitoring, enabling observability of system performance and task execution. Future enhancements may include **Apache Spark and Cassandra** for advanced analytics and structured storage.


---

### **Instructions to Run the Data Pipeline**
Follow these steps to set up and run the pipeline:

#### **1. Prerequisite**
Ensure that **Python** is installed on your computer. Additionally, **Docker** is required for this project.
- [Download Docker Desktop](https://www.docker.com/products/docker-desktop) and install it.

#### **2. Start Docker**
After installing Docker, start the application.

#### **3. Download the Project**
Clone or download the entire project to your local machine.

#### **4. Navigate to the Project Directory**
Open your terminal and navigate to the folder where the project is located. Run the following command:
```bash
docker compose up -d
```
Wait for the Docker containers to start. The containers will first pull the necessary images, then initialize and become healthy. You can monitor the containers using Docker Desktop.

#### **5. Access Airflow**
Once the Docker setup is running, open your web browser and go to:
```
http://localhost:8080
```
Log in using the credentials:
- **Username**: admin  
- **Password**: admin  
You should see the Airflow dashboard with the configured tasks.

#### **6. Set Up an Airflow Connection to AWS S3**
In the Airflow UI, go to the **Admin** tab in the top navigation bar and select **Connections**. Create a new connection with the following details:
- **Connection Name**: data_608  
- **Connection Type**: Amazon Web Services  
- **AWS Access Key and Secret Key**: Enter your AWS credentials.  
Click **Save** once done.

#### **7. Modify the S3 Bucket Name in the Code**
Navigate to the file **main.py** located in the project’s **dags** folder. Find line 228:
```python
s3_hook.load_bytes(buffer.getvalue(), key=s3_path, bucket_name='test-608-project', replace=True)
```
Replace `'test-608-project'` with the name of your desired S3 bucket.

#### **8. Access the Monitoring Dashboard**
To monitor the performance of the pipeline, including system resource utilization and data ingestion status, access **Grafana** for real-time visualization:

（1）Open your web browser and navigate to:
```
http://localhost:3000
```
（2）Log in using the default credentials:
- **Username:** admin
- **Password:** admin

（3） Once inside **Grafana**, navigate to the **Dashboards** section. Here, you can view:
- **Airflow task execution metrics**
- **Kafka message throughput**
- **Container resource usage (CPU, memory, disk I/O)**
- **System-wide monitoring from Prometheus and cAdvisor**

This allows users to ensure the pipeline is running efficiently and troubleshoot any potential bottlenecks.


#### **9. Create an AWS Glue Crawler**
- Go to the AWS Glue service and create a new crawler.
- Point the crawler to the folder in your S3 bucket containing the data.
- Create a new database and configure the crawler to populate it.

#### **10. Run the Crawler**
Run the crawler to create the schema and make the data queryable.

#### **11. Prepare Dashboard Files**
- Navigate to the **dashboard** folder in the project.
- Upload the following files to a designated folder inside the S3 bucket:
  - `all_locations.csv`
  - `result_key.txt`

#### **12. Set Up an EC2 Instance**
- Launch an EC2 instance.
- Install Python and the required dependencies using the provided `requirements.txt`.
- Copy the files `dash_app.py` and `athena_query.py` to the instance.

#### **13. Configure EC2 Security Group**
- Add a rule to allow inbound traffic on **port 8050**.

#### **14. Run the Python Scripts**
- First, run:
  ```bash
  python athena_query.py
  ```
- Then, run:
  ```bash
  python dash_app.py
  ```

#### **15. Access the Dashboard**
Use the public IP address of the EC2 instance to access the web app in your browser:
```
http://<public-ip>:8050
```

**Note**: Steps 14 and 15 can also be performed locally if desired.

