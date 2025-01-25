# tech-docs-rag

A Retrieval-Augmented Generation (RAG) system for managing and querying technical documentation.

## Introduction

This repository contains everything you need to set up a working FastAPI application and a Streamlit demo app. Below you will find the step-by-step procedure to install the necessary dependencies (including Homebrew and Vespa), run the Vespa Docker container, and launch both the FastAPI service and the Streamlit demo interface.

---

## 1. Install Homebrew (on Linux)

Run the following command to install Homebrew:

    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

### Next steps after installation

- Run these commands in your terminal to add Homebrew to your PATH:
  
      echo >> /home/aldin/.bashrc
      echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> /home/aldin/.bashrc
      eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

- Install Homebrew's dependencies if you have sudo access:

      sudo apt-get install build-essential

  For more information, see:
  https://docs.brew.sh/Homebrew-on-Linux

- It is recommended to install GCC:

      brew install gcc

- Run `brew help` to get started

- Further documentation:
  https://docs.brew.sh

---

## 2. Install vespa-cli

Once Homebrew is set up, you can install the Vespa CLI by running:

    brew install vespa-cli

---

## 3. Run the Vespa Docker Container

Use the following command to start the Vespa Docker container. Make sure to mount the `vespa` folder from this project directory into the container so we can deploy the Vespa app/schema from it.

    sudo docker run --detach --name vespa --hostname vespa-container \
      --volume /path/to/project/tech-docs-rag/vespa:/app \
      --publish 8080:8080 --publish 19071:19071 \
      vespaengine/vespa

### Accessing the container

Once the container is running, you can execute into it with:

    sudo docker exec -it vespa bash

Then move into the app directory:

    cd /app

Finally, deploy the application/schema with:

    vespa deploy

---

## 4. Install Python Dependencies

To run the FastAPI application and the Streamlit demo, you must install all required Python packages. You can use either of the following commands:

    pip install -r requirements.txt

or

    pip install -I .

---

## 5. Run the FastAPI Application

To start the FastAPI application, run:

    uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

---

## 6. Run the Streamlit Demo

Once the FastAPI application is running, you can launch the Streamlit demo (which depends on the FastAPI service) by running:

    streamlit run src/chatbot/chatbot_ui.py

---

## Environment Variables

Before running any of the above, ensure you have set up all the environment variables as indicated in the `.env.example` file. 
Set any API_USERNAME and API_PASSWORD of your choice.
Below is an example of local variables used for testing (replace the values accordingly):

    OPENAI_API_KEY="YOUR_OPENAI_API_KEY"

    VESPA_HOST=localhost
    VESPA_PORT=8080

    FASTAPI_HOST=localhost
    FASTAPI_PORT=8000

    API_USERNAME="YOUR_API_USERNAME"
    API_PASSWORD="YOUR_API_PASSWORD"