FROM python:3.8-slim-buster

WORKDIR /root
ENV VENV /opt/venv
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONPATH /root

RUN apt-get update && apt-get install -y build-essential git

# Install the AWS cli separately to prevent issues with boto being written over
RUN pip3 install awscli
# Similarly, if you're using GCP be sure to update this command to install gsutil
# RUN curl -sSL https://sdk.cloud.google.com | bash
# ENV PATH="$PATH:/root/google-cloud-sdk/bin"

ENV VENV /opt/venv
# Virtual environment
RUN python3 -m venv ${VENV}
ENV PATH="${VENV}/bin:$PATH"

# Install Python dependencies
COPY ./requirements.txt /root
RUN pip install -r /root/requirements.txt

# RUN git clone https://github.com/flyteorg/flytekit.git && cd flytekit && git checkout remote-register1 && pip install . && cd ..
#RUN git clone https://github.com/pingsutw/flytekit.git && cd flytekit && git checkout schema-arrow && pip install . && cd ..
#RUN git clone https://github.com/pingsutw/flyteidl.git && cd flyteidl && git checkout new-schema && pip install . && cd ..
RUN pip install fsspec google-cloud-bigquery-storage google-cloud-bigquery s3fs
COPY ./gcp.json /opt
ENV GOOGLE_APPLICATION_CREDENTIALS "/opt/gcp.json"

# Copy the actual code
COPY . /root

# This tag is supplied by the build script and will be used to determine the version
# when registering tasks, workflows, and launch plans
ARG tag
ENV FLYTE_INTERNAL_IMAGE $tag
