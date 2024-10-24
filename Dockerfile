FROM python:3.9-slim

WORKDIR /usr/src/app

COPY requirements.txt .

RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libffi-dev \
    libopenblas-dev \
    libblas-dev \
    liblapack-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

# Install Jupyter
RUN pip install jupyter ipykernel notebook

# Generate Jupyter config
RUN jupyter notebook --generate-config

# Allow root access and configure Jupyter to be accessible
RUN echo "c.NotebookApp.ip = '0.0.0.0'" >> ~/.jupyter/jupyter_notebook_config.py
RUN echo "c.NotebookApp.allow_root = True" >> ~/.jupyter/jupyter_notebook_config.py
RUN echo "c.NotebookApp.token = ''" >> ~/.jupyter/jupyter_notebook_config.py
RUN echo "c.NotebookApp.password = ''" >> ~/.jupyter/jupyter_notebook_config.py

# Expose ports
EXPOSE 4001 8888

# Start Jupyter Notebook
CMD ["jupyter", "notebook", "--no-browser", "--allow-root", "--ip=0.0.0.0", "--port=8888"]
