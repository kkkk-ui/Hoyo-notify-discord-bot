FROM python:3.12.4
WORKDIR /discord_bot
COPY requirements.txt /discord_bot/
RUN pip install -r requirements.txt
COPY . /discord_bot
CMD python main.py
