FROM python:3.11-slim

# Copy the files from the src directory
COPY src/requirements.txt /requirements.txt
COPY src/Terra_GenAI_v1.py /Terra_GenAI_v1.py

RUN pip install --no-cache-dir -r /requirements.txt
RUN pip install fastapi uvicorn google-cloud-secret-manager google-auth google-auth-oauthlib
RUN apt-get update && apt-get install -y git


EXPOSE 8000
CMD ["uvicorn", "Terra_GenAI_v1:app", "--host", "0.0.0.0", "--port", "8000"] 

