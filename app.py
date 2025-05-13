import os

from dotenv import load_dotenv

from middleware import auth_middleware

load_dotenv()

from flask import Flask, render_template

import main_router
from constant import DBContainer

app = Flask(__name__, static_url_path='/static')
from pymongo import MongoClient, DESCENDING

app.register_blueprint(main_router.html.auth_route)
app.register_blueprint(main_router.api.auth_api_router)
app.register_blueprint(main_router.api.game_api_router)
client = MongoClient('localhost', 27017)
db = client['acid_rain']
user_db = db['user']
try:
    user_db.create_index([("high_score.kr", DESCENDING)])
except Exception as e:
    print("인덱싱 생성 실패")

# high_score.en 필드에 내림차순 인덱스 생성
try:
    user_db.create_index([("high_score.en", DESCENDING)])
except Exception as e:
    print("인덱싱 생성 실패")

@app.route("/", endpoint="page_main")
@auth_middleware(use_redirect=True)
def game_main_page():
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
def test_game():
    return render_template("./game/acid_game.html")

@app.route('/testranking')
def test_rank():
    return render_template("./game/ranking.html")

if __name__ == '__main__':
    app.run(debug=True if os.environ.get('IS_DEBUG') else False, port=5000 if os.environ.get('IS_DEBUG') else 9001)
