## This is a project for Diego.

### This whole folder is for you to grab the data from the API and store it into those three csvs.

### please note, the three csv are in the subfolder "data". These CSVs are not empty because I test it.

### You'd better repalce them with the empty ones.

### Here is the steps.

1. please download this whole folder in your computer.
2. please download docker and install it.https://www.docker.com/products/docker-desktop/
3. please start the docker.
4. In the terminal, please nevigate to this folder and use this command " docker compose up -d".
   waiting for the docker containers start. You will first see they are pulling and then created and healty.
   You can see those container in the docker desktop.
5. When the docker start to work. Type the “http://localhost:8080” in your chorme. Input the name"admin", password"admin"
6. you will see the airflow task is on the page.
7. Trigger it. It will run one time every 10 minutes, and grab the data into the csv inthe folder "data" every time.
8. If you have any problem, We can talk in the library. 
