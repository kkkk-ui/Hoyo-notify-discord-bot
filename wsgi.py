from flask import Flask

app = Flask('__name__ ')

@app.route('/')
def home():
    return "I'm alive"

# WSGI サーバーはこの 'application' を起動時に探します
application = app
