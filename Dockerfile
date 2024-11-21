FROM python:3.11
WORKDIR /discord_bot
COPY requirements.txt /discord_bot/
RUN pip install -r requirements.txt
RUN apt-get update -y && \
    apt-get install -y wget curl unzip && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb && \
    apt-get -f install -y && \
    wget https://chromedriver.storage.googleapis.com/113.0.5672.63/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver
RUN apt-get install -y xvfb
COPY . /discord_bot
CMD python main.py
