from flask import Flask

from constant import DBContainer
from router import auth_router

app = Flask(__name__)
from pymongo import MongoClient

app.register_blueprint(auth_router)

client = MongoClient('localhost', 27017)
db = client['acid_rain']
ranking_db = db['ranking']
user_db = db['user']
DBContainer.user_db = user_db
DBContainer.ranking_db = ranking_db


@app.route("/")
def asdf():
    return "asdf"


@app.route('/api/ranking/acid_rain', methods=["GET"])
def get_acid_rain():  # put application's code here
    pass


@app.route('/api/ranking/acid_rain', methods=["POST"])
def post_acid_ranking():
    pass


if __name__ == '__main__':
    app.run()
