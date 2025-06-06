Installing Containerized Apache Airflow

https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html

This needs docker and docker compose. Opted to use the docker-compose-plugin package in my WSL2 Ubuntu Environment. 
Had to add docker repository to apt-get:
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update

sudo apt-get install docker-compose-plugin

After that, it worked. Launched:

docker compose run airflow-cli airflow config list

Initialized database:
docker compose up airflow-init

Up the service:
docker compose up

Seems good:
docker ps
CONTAINER ID   IMAGE                  COMMAND                  CREATED         STATUS                   PORTS      NAMES
8f1c6490f948   apache/airflow:3.0.1   "/usr/bin/dumb-init …"   3 minutes ago   Up 3 minutes (healthy)   8080/tcp   03-orchestration-airflow-dag-processor-1
6ad2640bc5ac   apache/airflow:3.0.1   "/usr/bin/dumb-init …"   3 minutes ago   Up 3 minutes (healthy)   8080/tcp   03-orchestration-airflow-scheduler-1
266cb307b8db   apache/airflow:3.0.1   "/usr/bin/dumb-init …"   3 minutes ago   Up 3 minutes (healthy)   8080/tcp   03-orchestration-airflow-triggerer-1
ed381bb2ea1e   redis:7.2-bookworm     "docker-entrypoint.s…"   9 minutes ago   Up 9 minutes (healthy)   6379/tcp   03-orchestration-redis-1
c459b8feee28   postgres:13            "docker-entrypoint.s…"   9 minutes ago   Up 9 minutes (healthy)   5432/tcp   03-orchestration-postgres-1


Added the recommended wrapper scripts:
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/3.0.1/airflow.sh'
chmod +x airflow.sh

---> not really working...
Workaround: just go inside the worker container and run the commands from there:
docker exec -it 03-orchestration-airflow-worker-1 bash

Anyway, seems up, access to UI:
http://localhost:8080/



Also added MLFlow Container, as described in the course page:
MLFlow UI:
http://localhost:5000


Issue: not detecting xgboost.
Guess will have to work out the docker image a bit:
https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#special-case-adding-dependencies-via-requirements-txt-file

Also, can't use "localhost" in the scripting from within airflow, as this is a containerized environment.

For Homework:

Question 1. Select the Tool
You can use the same tool you used when completing the module, or choose a different one for your homework.

What's the name of the orchestrator you chose?
Apache Airflow              |                     

Question 2. Version
What's the version of the orchestrator?
3.0.1 

Question 3. Creating a pipeline
Let's read the March 2023 Yellow taxi trips data.

How many records did we load?

3,403,766

Question 4. Data preparation

Let's apply to the data we loaded in question 3.

What's the size of the result?

3,316,216


Question 5. Train a model
We will now train a linear regression model using the same code as in homework 1.
-Fit a dict vectorizer.
-Train a linear regression with default parameters.
-Use pick up and drop off locations separately, don't create a combination feature.

Let's now use it in the pipeline. We will need to create another transformation block, and return both the dict vectorizer and the model.

What's the intercept of the model?

Hint: print the intercept_ field in the code block

24.77 (23.847835639296278)


Question 6. Register the model
The model is trained, so let's save it with MLFlow.
Find the logged model, and find MLModel file. What's the size of the model? (model_size_bytes field):

4,534 (4508)
