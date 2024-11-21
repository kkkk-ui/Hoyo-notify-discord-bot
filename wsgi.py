from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "I'm alive"

# WSGI サーバーはこの 'application' を起動時に探します
application = app  # これを追加
