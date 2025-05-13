from flask import Flask

import main_router
from constant import DBContainer
from flask import render_template

app = Flask(__name__, static_url_path='/static')
from pymongo import MongoClient

app.register_blueprint(main_router.html.auth_route)
app.register_blueprint(main_router.api.auth_api_router)
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


