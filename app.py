import os

from dotenv import load_dotenv

from middleware import auth_middleware

load_dotenv()

from flask import Flask, render_template

import main_router
from constant import DBContainer

app = Flask(__name__, static_url_path='/static')
from pymongo import MongoClient

app.register_blueprint(main_router.html.auth_route)
app.register_blueprint(main_router.api.auth_api_router)
app.register_blueprint(main_router.api.game_api_router)
client = MongoClient('localhost', 27017)
db = client['acid_rain']
ranking_db = db['ranking']
user_db = db['user']
DBContainer.user_db = user_db
DBContainer.ranking_db = ranking_db


@app.route("/")
def asdf():
    return render_template("./main.html")


@app.route('/api/ranking/acid_rain', methods=["GET"])
def get_acid_rain():  # put application's code here
    pass


@app.route('/api/ranking/acid_rain', methods=["POST"])
def post_acid_ranking():
    pass

@app.route('/game')
@auth_middleware(use_redirect=True)
def main_game():
    return render_template("./game/acid_game.html")

@app.route('/testgame')
def main_game():
    return render_template("./game/acid_game.html")

if __name__ == '__main__':
    app.run(debug=True if os.environ.get('IS_DEBUG') else False, port=5000 if os.environ.get('IS_DEBUG') else 9001)
