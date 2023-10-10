from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "hello, world!"

def main():
    app.run("localhost", 8000)

if __name__ == "__main__":
    main()