FROM python:latest

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install pyyaml==5.3

RUN apt-get update && apt-get install -y \
    curl \
    vim \
    net-tools \
    iputils-ping \
    openssh-client

COPY src ./src

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
