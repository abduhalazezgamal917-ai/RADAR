from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "ZenoX Guard System is Online and Running! 🚀"

def run():
    # المنفذ 8080 هو المعتاد في الاستضافات السحابية
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

