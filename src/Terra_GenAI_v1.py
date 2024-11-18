import re
import os
import time
import json
from fastapi import FastAPI, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain_google_vertexai import VertexAI
from googleapiclient.discovery import build
from typing import List, Optional
from enum import Enum
import zipfile
import io
import shutil
from datetime import datetime
import stat
from git import Repo, GitCommandError
from google.auth.transport.requests import Request
from google.cloud import secretmanager
from google.oauth2 import service_account
import requests
from bs4 import BeautifulSoup
from http.client import HTTPException\


TOKEN=os.environ['TOKEN']

# Define the required scopes
SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/cloud-ai-platform"
]

# Function to fetch the service account key from Secret Manager
# def get_service_account_key(project_id, secret_id, version_id="latest"):
def get_service_account_key(project_id, secret_id, version_id="3"):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    # response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

# Fetch the service account key from Secret Manager
PROJECT_ID_CRED = "lumen-b-ctl-047"
SECRET_ID = "terraform-secret"

service_account_info = get_service_account_key(PROJECT_ID_CRED, SECRET_ID)

# Load the credentials from the service account key JSON
credentials_info = json.loads(service_account_info)
credentials = service_account.Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
credentials.refresh(Request())

# Initialize the VertexAI client with the scoped credentials
llm_mdl = VertexAI(model_name="gemini-1.5-flash-001", temperature=0, credentials=credentials)

os.system('apt-get update')
os.system('apt-get install -y git')
os.system('apt-get install -y gettext')
os.system('git config --global user.email "terraAI@example.com"')
os.system('git config --global user.name "terraAI"')

app = FastAPI()
origins = ["*"] 
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def gitcmt(username: str ,repo: str,token: str,new_branch:str):
    global TOKEN
    temp_clone_cmd='git clone https://'+TOKEN+'@github.com/Nancy047/terraform-template deplobase'
    src_clone_cmd   = 'git clone https://'+token+'@github.com/'+username+'/'+repo+' codebase'
    copy_cmnd       = 'cp -r deplobase/* codebase/'
    copy_command    = 'cp main.tf codebase/'

    os.system(temp_clone_cmd)
    os.system(src_clone_cmd)
    os.system(copy_cmnd)
    os.system(copy_command)

    current_path    = os.getcwd()
    path2           = current_path+'/'+'codebase'
    os.chdir(path2)

    update_cmnd     = 'envsubst < gaction.tmpl > gaction.yaml'
    os.system(update_cmnd)
    
    git_wrkflw_dir  = 'mkdir .github'
    git_wrkflw_dir2 = 'mkdir .github/workflows'
    os.system(git_wrkflw_dir)
    os.system(git_wrkflw_dir2)
    copy_yaml_cmnd  = 'cp gaction.yaml .github/workflows/'
    os.system(copy_yaml_cmnd)
    dlt_cmnd        = 'rm gaction.tmpl gaction.yaml'
    os.system(dlt_cmnd)
    
    git_nw_brnch_cmd= 'git checkout -b '+new_branch
    time.sleep(4)
    git_add_cmnd    = 'git add .'
    git_commit_cmnd = 'git commit -m "Commit made by the backend process"'
    git_push_cmnd   = 'git push origin '+new_branch+':'+new_branch

    os.system(git_nw_brnch_cmd)  
    os.system(git_add_cmnd)
    os.system(git_commit_cmnd)
    os.system(git_push_cmnd)
    message = 'Files added successfully.Check github actions for latest status.'
    
    return message

@app.post("/to_generate_terraform_script/")
async def gcp(projectid: str,gcp_service: List[str],usage: str,username: str ,repo: str,token: str,new_branch: str):

    
    acc = ''' provider "google" {
            credentials = file("keys.json")
           project     = "abc"
               }
          '''
    auth = ''' master_auth {
    username = "admin"
  }'''
    prompt = f"""
        You are a cloud architect and your task is to generate a Terraform script for creating resources in GCP based on the provided services list. Ensure the script is valid and free of errors. Use the example below to guide your configuration.

        Example:
        # Configure the Google Cloud Provider
        terraform {{
          required_providers {{
            google = {{
              source  = "hashicorp/google"
              version = "~> 4.0"
            }}
          }}
        }}

        # Example resource configuration for GCS bucket
        resource "google_storage_bucket" "basic_bucket" {{
          name          = "basic-bucket"
          location      = "US"
          force_destroy = true
          storage_class = "STANDARD"
        }}

        # Example resource configuration for GKE cluster
        resource "google_container_cluster" "basic_cluster" {{
          name               = "basic-cluster"
          location           = "us-central1"
          initial_node_count = 1
          node_config {{
            machine_type = "e2-medium"
          }}
          network            = "default"
        }}

        # Example resource configuration for Google App Engine Application
        resource "google_app_engine_application" "basic_app" {{
          location_id = "us-central"
          project     = {projectid}
        }}

        # Example resource configuration for Google App Engine Standard Environment Service
        resource "google_app_engine_standard_app_version" "basic_service" {{
          service   = "basic-service"
          project   = {projectid}
          runtime   = "nodejs16"
          version_id = "v1"
          entrypoint {{
            shell = "node app.js"
          }}
          deployment {{
            zip {{
              source_url = "gs://{projectid}/app.zip"
            }}
          }}
          automatic_scaling {{
            max_idle_instances = 1
            min_idle_instances = 0
          }}
        }}

        # Example resource configuration for Cloud Functions (2nd gen)
        resource "google_cloudfunctions_function" "basic_function" {{
          name        = "basic-function"
          runtime     = "nodejs16"
          entry_point = "helloHTTP"
          source_archive_bucket = "your-bucket-name"
          source_archive_object = "your-function-code.zip"
          trigger_http = true
          timeout     = 60
          available_memory_mb = 128
        }}

        # Example resource configuration for Cloud Run
        resource "google_cloud_run_v2_service" "basic_service" {{
          name     = "basic-service"
          location = "us-central1"
          template {{
            spec {{
              containers {{
                image = "gcr.io/{projectid}/your-image"
                resources {{
                  limits = {{
                    memory = "128Mi"
                    cpu    = "1"
                  }}
                }}
              }}
            }}
          }}
        }}

        Notes:
        1. Based on the input context, fill in values for variables in the prompt as: ['Basic', 'Medium', 'Heavy']
        2. Basic: Minimize cost and resource utilization.
        3. Medium: Balance performance and cost.
        4. Heavy: Prioritize performance over cost.
    

        Rules:
        1. Use the list of GCP services in {gcp_service} to generate the Terraform script for each service, using appropriate values based on {usage} usage.
        2. The Terraform script should include the provider configuration once at the beginning.
        3.Include this block of code{acc} , onetime in the final terraform file generated  and this block {auth} should not be included in the terraform script and do not include autoscaling in terraform script and remove spec block for cloud run service alone.
        4. Handle common errors and ensure the script is valid and error-free.
        5. Ensure that where and all the generating terraform script by LLM Model, is asking for project or projectid it should be filled with the "projectid" given by the user - {projectid}
        
        GCP services list:
        {gcp_service}

        Generate the Terraform script:
        """
    
    response = llm_mdl.invoke(prompt)
    try:
        response2 = response.replace('```terraform','```')
        ss        = response2.split('```')[1]
    except:
        ss        = response.split('```')[1]
    
    with open(f"main.tf", "w") as f:
        f.write(ss)
    
    gt_action = gitcmt(username,repo,token,new_branch)
    
    msg = 'Resource created using Terraform AI bot'    
    return msg,gt_action
    
@app.post("/user_input/serv_recom/")
def service_suggested_user_input(input: str):
    prompt = f"""
    You are a cloud architect and you help people to create solutions for business requirements in the cloud.
   
    Based on the following input: {input}, suggest the best Google Cloud Associated services.
   a
    Steps to follow:
    1. If the input is "gke", suggest only "Google Kubernetes Engine".
    2. If the input is "gcs", suggest only "Google Cloud Storage".
    3. For any other input, analyze the provided requirements thoroughly and note the key points such as coding language and the project use case.
    4. Identify the best Google Cloud Associated services that meet these requirements.
    5. If the generated Google services provide the same functionality, then provide only one Google service among the services.
    6. Provide the description, pricing for each service, and explain why we are suggesting these services as the best services for this particular input in a point-by-point manner.
    7. Provide the billing and charge details in three formats (basic, medium, heavy) for each suggested service.
    8. Do not include the keyword 'here' in any form in the final list of suggested GCP service names.
    9. Finally, provide a separate list of suggested GCP service names without its charge details alone inside "[]" like [1st suggested service name, 2nd suggested service name] and add "-12345-" before the separate list of suggested GCP service names  .
    10. Do not include "here" or [here] in that separate list of suggested GCP services.
    11. Do not include any URLs or HTTP requests in that separate list of suggested GCP services.
    12. Do not include the keyword 'pricing' or 'charges' in the final list of suggested GCP service names.
    13. Ensure to follow the instructions strictly without adding any additional context or services that are not directly requested.
    """
   
    response = llm_mdl.invoke(prompt)
 
    def extract_messages(text):
        pattern = r'\[([^\]]+)\]'
        matches = re.findall(pattern, text)
        messages = [message.strip() for match in matches for message in match.split(',')]
        return messages
 
    def remove_content_after_pattern(input_string: str) -> str:
        # Define the regex pattern to match everything before *-/-*
        pattern = r"(.*?)(?:\s*-\s*12345\s*-\s*)"
    
        # Search for the pattern in the input string
        match = re.search(pattern, input_string, re.DOTALL)
        
        # If a match is found, return the matched group
        if match:
            return match.group(1)
        
        # If no match is found, return the original string
        return input_string
 
    # cleaned_response = clean_response(response)
    sug_services = extract_messages(response)
   
    response_modified = remove_content_after_pattern(response)
    msg={"description":response_modified, "sug_services":sug_services}
    return msg
    
@app.get("/")
async def hlth():
    sttr = 'Health Check' 
    return sttr

@app.post("/pricing_for_modifiedlist/")
async def suggest_google_cloud1(sug_services_casefolded: List[str]):
    prompt4 = f"""You are a cloud architect and you help people to create solutions for business requirements in the cloud.
   
    Based on the following input: {sug_services_casefolded}, give all the user provided Google Cloud Associated services and do not miss any services which is in {sug_services_casefolded}.
   
    Steps to follow:
    1. If the input is "gke", suggest only "Google Kubernetes Engine".
    2. If the input is "gcs", suggest only "Google Cloud Storage".
    3. For any other input, analyze the provided requirements thoroughly and note the key points such as coding language and the project use case.
    4. Identify the best Google Cloud Associated services that meet these requirements.
    5. If the generated Google services provide the same functionality, then provide only one Google service among the services.
    6. Provide the reason, pricing, and description for each service, and explain why we are suggesting these services as the best services for this particular input in a point-by-point manner.
    7. Provide the billing and charge details in three formats (basic, medium, heavy) for each suggested service.
    8. Do not include the keyword 'here' in any form in the final list of suggested GCP service names.
    9. Finally, provide a separate list of suggested GCP service names without its charge details alone inside "[]" like [1st suggested service name, 2nd suggested service name].
    10. Do not include "here" or [here] in that separate list of suggested GCP services.
    11. Do not include any URLs or HTTP requests in that separate list of suggested GCP services.
    12. Ensure to follow the instructions strictly without adding any additional context or services that are not directly requested.
    13. Do not return any python code as the output, just format whatever the input you are provided with.
    14. Strictly do not say "You've provided a great example of how to format the output based on user input" in my response.
    
    Example output format 1:
    [Google Kubernetes Engine (GKE), Cloud Run, App Engine, Cloud Functions ,Dialogflow API]
    Google Kubernetes Engine - Reason: GKE is a managed Kubernetes service that provides a highly scalable and reliable platform for deploying and managing containerized applications. It's ideal for deploying Java APIs as it offers flexibility, scalability, and ease of management.
    Cloud Run  - Reason: Cloud Run is a fully managed serverless platform that allows you to deploy and scale containerized applications without managing any infrastructure. It's a good option for deploying Java APIs that require minimal resource management and automatic scaling.
    App Engine - Reason: App Engine Standard Environment is a fully managed platform for deploying and scaling web applications. It's a good option for deploying Java APIs that require a managed environment and automatic scaling.
    Cloud Functions - Reason: Cloud Functions is a serverless compute platform that lets you execute code in response to events without managing any infrastructure. It's a good option for deploying APIs that are triggered by events, such as HTTP requests or changes to data in Cloud Storage. It's also a good choice for applications that need to be highly scalable and cost-effective.
    Dialogflow API - Reason: Dialogflow API is a natural language understanding platform that allows you to build conversational interfaces for your applications. It's a good option for building chatbots, virtual assistants, and other conversational applications. It's also a good choice for applications that need to understand and respond to natural language.

    [ basic :
    1. Google Kubernetes Engine: - * **Basic:** $0.10 per vCPU per hour for the first 100 vCPUs, $0.08 per vCPU per hour for the next 100 vCPUs, and $0.06 per vCPU per hour for vCPUs beyond 200.
    2. Cloud Run: - * **Basic:** $0.004 per request for the first 1 million requests, $0.002 per request for the next 1 million requests, and $0.001 per request for requests beyond 2 million.
    3. App Engine: - * **Basic:** $0.004 per request for the first 1 million requests, $0.002 per request for the next 1 million requests, and $0.001 per request for requests beyond 2 million.
    4. Cloud Functions - * **Basic:** $0.004 per request for the first 1 million requests, $0.002 per request for the next 1 million requests, and $0.001 per request for requests beyond 2 million.
    5. Dialogflow API:- * **Basic:** $0.002 per request for the first 1 million requests, $0.001 per request for the next 1 million requests, and $0.0005 per request for requests beyond 2 million.
    ]
    
    [ medium :
    1. Google Kubernetes Engine: - * **Medium:** $0.20 per vCPU per hour for the first 100 vCPUs, $0.16 per vCPU per hour for the next 100 vCPUs, and $0.12 per vCPU per hour for vCPUs beyond 200.
    2. Cloud Run: - * **Medium:** $0.008 per request for the first 1 million requests, $0.004 per request for the next 1 million requests, and $0.002 per request for requests beyond 2 million.
    3. App Engine: - * **Medium:** $0.008 per request for the first 1 million requests, $0.004 per request for the next 1 million requests, and $0.002 per request for requests beyond 2 million.
    4. Cloud Functions - * **Medium:** $0.008 per request for the first 1 million requests, $0.004 per request for the next 1 million requests, and $0.002 per request for requests beyond 2 million.
    5. Dialogflow API:- * **Medium:** $0.004 per request for the first 1 million requests, $0.002 per request for the next 1 million requests, and $0.001 per request for requests beyond 2 million.
    ]
    
    [ heavy :
    1. Google Kubernetes Engine: - * **Heavy:** $0.30 per vCPU per hour for the first 100 vCPUs, $0.24 per vCPU per hour for the next 100 vCPUs, and $0.18 per vCPU per hour for vCPUs beyond 200.
    2. Cloud Run: - * **Heavy:** $0.012 per request for the first 1 million requests, $0.006 per request for the next 1 million requests, and $0.003 per request for requests beyond 2 million.
    3. App Engine: - * **Heavy:** $0.012 per request for the first 1 million requests, $0.006 per request for the next 1 million requests, and $0.003 per request for requests beyond 2 million.
    4.Cloud Functions: - * **Heavy:** $0.012 per request for the first 1 million requests, $0.006 per request for the next 1 million requests, and $0.003 per request for requests beyond 2 million.
    5.Dialogflow API: - * **Heavy:** $0.006 per request for the first 1 million requests, $0.003 per request for the next 1 million requests, and $0.0015 per request for requests beyond 2 million.
    ]
    
    If the user doesn't give the requirements details instead he mentions the Google service name directly (like gke, gcs, cloud run) then the output should be like the following:
    
    Example output format 2:
    
    [Google Kubernetes Engine (GKE)] 
    [ basic :
    1. Google Kubernetes Engine: - Basic: Pay-as-you-go pricing based on the number of nodes and the time they are running. \n* **Nodes:** $0.15 per hour for a standard n1-standard-1 node.\n* **Cluster Management:** $0.10 per hour per cluster
    ]
    
    [ medium :
    1. Google Kubernetes Engine: - medium : Monthly commitment for a fixed number of nodes. \n* **Nodes:** $0.12 per hour for a standard n1-standard-1 node.\n* **Cluster Management:** $0.08 per hour per cluster]
    
    [ heavy :
    1. Google Kubernetes Engine: - Heavy :Annual commitment for a fixed number of nodes. \n* **Nodes:** $0.10 per hour for a standard n1-standard-1 node.\n* **Cluster Management:** $0.06 per hour per cluster
    ]
    
    Pick any one of the formats according to the input and strictly follow that format."""
    
    response4 = llm_mdl.invoke(prompt4)

    def extract_messages(text):
       pattern = r'\[([^\]]+)\]'
       matches = re.findall(pattern, response4)

    # Filter out the list of service names
       services_list = [match.strip() for match in matches[0].split(',')]
       return services_list
 
    # cleaned_response = clean_response(response)
    sug_services = extract_messages(response4)
   
    def format_pricing_details(response):
    
    # Strip any leading/trailing triple backticks
        response = response.strip('```')
        
        # Define regex patterns for basic, medium, and heavy pricing details
        basic_pattern = re.compile(r'\[ basic :\n(.*?)\n\]', re.DOTALL)
        medium_pattern = re.compile(r'\[ medium :\n(.*?)\n\]', re.DOTALL)
        heavy_pattern = re.compile(r'\[ heavy :\n(.*?)\n\]', re.DOTALL)

        # Extract pricing details using the defined patterns
        basic_pricing = basic_pattern.search(response).group(1).strip()
        medium_pricing = medium_pattern.search(response).group(1).strip()
        heavy_pricing = heavy_pattern.search(response).group(1).strip()

        # Format the extracted details into the desired list format
        basic_list = f"basic : [\n{basic_pricing}\n]"
        medium_list = f"medium : [\n{medium_pricing}\n]"
        heavy_list = f"heavy : [\n{heavy_pricing}\n]"

        # Combine the formatted lists into a single string
        formatted_pricing_details = f"{basic_list}\n\n{medium_list}\n\n{heavy_list}"
        final = {"basic":basic_list, "medium":medium_list,"heavy": heavy_list}
        return final
    price = format_pricing_details(response4)

    
    def extract_service_details(response):
    
    # Use regex to capture up to the point before "[ basic"
        pattern1 = r'(.+?)(?=\[\s*basic\s*:)'
        match = re.search(pattern1, response, re.DOTALL)
        
        if match:
            result = match.group(1).strip()
            return result
        else:
            return "No match found"
    
    description = extract_service_details(response4)
    return description,sug_services,price

@app.post("/getting_gcp_services/")
async def getting_list_of_gcp_services():

    url = "https://cloud.google.com/products?hl=en"

    # Send a GET request to the page
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors

    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all product names inside the specified structure
    product_elements = soup.select('li .SVGK7b .CilWo')

    # Extract and print the product names
    product_names = [element.text.strip() for element in product_elements]

    # combined_gcp_services = list(set(sug_services + product_names))

    response=categorize_list(product_names)

    return response

def categorize_list(combined_gcp_services):
    example="""[
    {
        "Compute": [
            "Compute Engine", "Cloud Run", "Google Kubernetes Engine", "App Engine", 
            "Bare Metal Solution", "Batch", "Cloud GPUs", "Deep Learning VM Image", 
            "Migrate to Virtual Machines", "Recommender", "Shielded VMs", 
            "Sole-tenant Nodes", "Spot VMs", "SQL Server on Google Cloud", 
            "Tau VM", "VMware Engine", "Cloud Build", "Cloud Code", "Cloud Deploy", 
            "Deep Learning Containers", "Google Kubernetes Engine (GKE)", "Knative", 
            "Kubernetes applications on Google Cloud Marketplace", "Migrate to Containers", 
            "Cloud Functions", "Cloud Workstations", "Google Distributed Cloud Edge", 
            "Google Distributed Cloud Hosted", "Anthos", "Cloud Service Mesh", "Cloud Shell", 
            "Cloud Mobile App", "Cloud Endpoints", "Cloud APIs", "Cloud Console"
        ]
    },
    {
        "Storage": [
            "Cloud Storage", "Cloud Storage for Firebase", "Filestore", "Local SSD", 
            "Persistent Disk", "NetApp Volumes", "Parallelstore", "Block storage", 
            "Artifact Registry", "Cloud Build", "Cloud Code", "Cloud Deploy", "Cloud Run", 
            "Deep Learning Containers", "Google Kubernetes Engine (GKE)", "Knative", 
            "Kubernetes applications on Google Cloud Marketplace", "Migrate to Containers", 
            "Artifact Registry", "Cloud Build", "Cloud Code", "Cloud Deploy"
        ]
    }
    ]
    """

    prompt_cat=f"""You are given a list of Google Cloud Platform (GCP) service names. Your task is to categorize these services 
    into appropriate groups based on their primary functions. some of the The category examples like - Compute, Storage, Databases, Networking, Machine Learning, and Security. Here is the list of GCP services:
    {combined_gcp_services}

    Please provide the categorized list of services within a python list like the example provided below
    {example}

    Note: 
    1.The final output should consist only the list of categorized services in the valid JSON format as per the example dont return any extra descriptions
    2. Ensure that the final output meets the below requirements
      > Quotation Marks for Keys: JSON keys must be in double quotes.
      > Trailing Commas: JSON format does not allow trailing commas.
    3.finnaly Ensure that the final output is json error free.
    """
    response_cat= llm_mdl.invoke(prompt_cat)

    cleaned_response = re.sub(r'```json\n|\n```', '', response_cat)
    return cleaned_response

@app.post("/customize_sug_list/")
async def customize_sug_list(sug_services: List[str], services_to_add: List[str], services_to_delete: List[str]):

    sug_services_casefolded = [service.casefold() for service in sug_services]
    services_to_add_casefolded = [service.casefold() for service in services_to_add]
    services_to_delete_casefolded = [service.casefold() for service in services_to_delete]
    # Process list2 to append unique GCP services to list1
    for service in services_to_add_casefolded:
        if service not in sug_services_casefolded:
            sug_services_casefolded.append(service)

    # Process list3 to remove GCP services from list1
    for service in services_to_delete_casefolded:
        if service in sug_services_casefolded:
            sug_services_casefolded.remove(service)

    return {"modified_list1": sug_services_casefolded}

@app.get("/use_rsrc/gke")
async def use_gke(username: str, repo: str, branch: str, token: str, app_name: str, new_branch: str):
    global TOKEN
    os.environ['GIT_DISCOVERY_ACROSS_FILESYSTEM'] = '1'
    os.environ['APPNAME']                         = app_name
    token2 = TOKEN
    temp_clone_cmd  = 'git clone https://'+token2+'@github.com/Nancy047/cicd-template deplobase'
    src_clone_cmd   = 'git clone https://'+token+'@github.com/'+username+'/'+repo+' codebase'
    copy_cmnd       = 'cp -r deplobase/* codebase/'
    
    os.system(temp_clone_cmd)
    os.system(src_clone_cmd)
    os.system(copy_cmnd)

    current_path    = os.getcwd()
    path2           = current_path+'/'+'codebase'
    os.chdir(path2)
    
    current_path2    = os.getcwd()
    
    git_wrkflw_dir  = 'mkdir .github'
    git_wrkflw_dir2 = 'mkdir .github/workflows'
    os.system(git_wrkflw_dir)
    os.system(git_wrkflw_dir2)
    copy_yaml_cmnd  = 'cp gaction.yaml .github/workflows/'
    os.system(copy_yaml_cmnd)
    
    update_cmnd     = 'envsubst < deployment.tmpl > deployment.yaml'
    update_cmnd2    = 'envsubst < service.tmpl > service.yaml'
    update_cmnd3    = 'envsubst < ingress.tmpl > ingress.yaml'

    os.system(update_cmnd)
    os.system(update_cmnd2)
    os.system(update_cmnd3)    
    
    tmpl_files_rm   = 'find . -name "*.tmpl" -type f -delete'
    os.system(tmpl_files_rm)

    git_nw_brnch_cmd= 'git checkout -b '+new_branch
    time.sleep(4)
    git_add_cmnd    = 'git add .'
    git_commit_cmnd = 'git commit -m "Commit made by the backend process"'
    git_push_cmnd   = 'git push origin '+new_branch+':'+new_branch
 
    os.system(git_nw_brnch_cmd)  
    os.system(git_add_cmnd)
    os.system(git_commit_cmnd)
    os.system(git_push_cmnd)
    message = 'Files added successfully'
    return message

def get_values_from_dict(keys):
    my_dict = {
        'Spring Web':'web',
        'Spring Data JPA':'data-jpa',
        'Spring Security':'security',
        'Spring Boot Actuator':'actuator',
        'Spring Data MongoDB':'data-mongodb',
        'Spring Data Redis':'data-redis',
        'Spring Data Cassandra':'data-cassandra',
        'Spring Data Couchbase':'data-couchbase',
        'Spring Data Elasticsearch':'data-elasticsearch',
        'H2 Database':'h2',
        'MySQL Driver':'mysql',
        'PostgreSQL Driver':'postgresql',
        'Oracle Driver':'oracle',
        'SQL Server Driver':'sqlserver',
        'Spring Kafka':'kafka',
        'Spring AMQP':'amqp',
        'Spring Web Services':'web-services',
        'Spring Cloud Config':'config-client',
        'Spring Cloud Netflix Eureka':'eureka',
        'Spring Cloud Gateway':'gateway',
        'Spring Cloud Circuit Breaker':'circuitbreaker-resilience4j',
        'Spring Cloud OpenFeign':'openfeign',
        'Spring WebFlux':'webflux',
        'Project Reactor':'reactor-core',
        'Spring Boot DevTools':'devtools',
        'Spring Boot Admin':'admin',
        'Spring Boot Test':'test',
        'JUnit':'junit',
        'Mockito':'mockito',
        'Thymeleaf':'thymeleaf',
        'Freemarker':'freemarker',
        'Mustache':'mustache',
        'Validation':'validation'
    }
    values = [my_dict[key] for key in keys if key in my_dict]
    return ','.join(values)

def git_template_push(url,repo_url,new_branch_name,repo_name):
    # Define unique local repo path
    LOCAL_REPO_PATH = "unique_string"

    def unzip_file(zip_file, extract_to):
        """Unzips a file to the specified directory."""
        with zip_file as zf:
            zf.extractall(extract_to)

    def clone_repo(repo_url, local_repo_path):
        """Clones the Git repository to the specified local path."""
        try:
            repo = Repo.clone_from(repo_url, local_repo_path)
            return repo
        except GitCommandError as e:
            raise Exception(f"Error cloning repository: {e}")

    def push_to_new_branch(repo, branch_name):
        """Creates a new branch and pushes the changes to the remote repository."""
        new_branch = repo.create_head(branch_name)
        repo.head.reference = new_branch
        repo.head.reset(index=True, working_tree=True)

    def change_permissions(path):
        """Changes permissions of files and directories to allow deletion."""
        for root, dirs, files in os.walk(path):
            for dir in dirs:
                os.chmod(os.path.join(root, dir), stat.S_IWUSR | stat.S_IREAD | stat.S_IEXEC)
            for file in files:
                os.chmod(os.path.join(root, file), stat.S_IWUSR | stat.S_IREAD | stat.S_IEXEC)

    def close_and_delete(path):
        """Closes open files and deletes the directory."""
        change_permissions(path)  # Ensure permissions allow deletion
        try:
            shutil.rmtree(path, ignore_errors=False)  # Remove the directory
        except PermissionError as e:
            print(f"PermissionError: {e}")

    try:
        # Download and unzip the file
        response = requests.get(url)
        response.raise_for_status()
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))

        # Clone the repo and push to the new branch
        if os.path.exists(LOCAL_REPO_PATH):
            close_and_delete(LOCAL_REPO_PATH)
        
        repo = clone_repo(repo_url, LOCAL_REPO_PATH)
        push_to_new_branch(repo, new_branch_name)

        # Unzip the file into the repo, add, commit, and push changes
        unzip_file(zip_file, LOCAL_REPO_PATH)
        repo.git.add(A=True)
        repo.index.commit("Add files from in-memory zip file")
        origin = repo.remote(name='origin')
        origin.push(new_branch_name)

        # Clean up local repo after push
        close_and_delete(LOCAL_REPO_PATH)

        return f"Successfully pushed to branch {new_branch_name} in repository {repo_name}"

    except requests.exceptions.RequestException as e:
        return str(e)

@app.post("/java_items/")
async def create_items(
    dependency: List[str],
    baseDir: str,
    bootVersion: str,
    type: str,
    groupId: str,
    artifactId: str,
    name: str,
    description: str,
    packageName: str,
    javaVersion: str,
    username: str,
    repo: str,
    token: str,
    new_branch: str
):

    result_depe = get_values_from_dict(dependency)
    url = 'http://34.44.234.14:8080/api/generate?dependencies='+result_depe+'&baseDir='+baseDir+'&bootVersion='+bootVersion+'&type='+type+'&language=java&groupId='+groupId+'&artifactId='+artifactId+'&name='+name+'&description='+description+'&packageName='+packageName+'&javaVersion='+javaVersion+''
 
    # Git and repository details
    GIT_TOKEN = token  # Replace with your Git token
    GIT_USERNAME = username  # Replace with your Git username
    REPO_NAME = repo  # Replace with your repository name
    NEW_BRANCH_NAME = new_branch  # Replace with your new branch name
    REPO_URL = f"https://{GIT_USERNAME}:{GIT_TOKEN}@github.com/{GIT_USERNAME}/{REPO_NAME}.git"
    
    result_template=git_template_push(url,REPO_URL,NEW_BRANCH_NAME,REPO_NAME)

    return result_template


@app.post("/java_items_tmf/")
async def create_items(
    dependency: List[str],
    type: str,
    javaVersion: str,
    tmfStandard: str,
    dbConfig: str,
    username: str,
    repo: str,
    token: str,
    new_branch: str
):

    result_depe = get_values_from_dict(dependency)
    url = 'http://34.44.234.14:8087/api/generate?dependencies='+result_depe+'&type='+type+'&language=java&javaVersion='+javaVersion+'&TMFStandard='+tmfStandard+'&dbConfig='+dbConfig+''
 
    # Git and repository details
    GIT_TOKEN = token  # Replace with your Git token
    GIT_USERNAME = username  # Replace with your Git username
    REPO_NAME = repo  # Replace with your repository name
    NEW_BRANCH_NAME = new_branch  # Replace with your new branch name
    REPO_URL = f"https://{GIT_USERNAME}:{GIT_TOKEN}@github.com/{GIT_USERNAME}/{REPO_NAME}.git"

    result_template=git_template_push(url,REPO_URL,NEW_BRANCH_NAME,REPO_NAME)

    return result_template
