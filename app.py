import os

from dotenv import load_dotenv

from middleware import auth_middleware

load_dotenv()

from flask import Flask, render_template, redirect

import main_router
from main_router.socket import socketio
from constant import DBContainer, word_type

app = Flask(__name__, static_url_path='/static')
socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet')

from pymongo import MongoClient, DESCENDING

app.register_blueprint(main_router.html.game_route)
app.register_blueprint(main_router.html.auth_route)
app.register_blueprint(main_router.api.auth_api_router)
app.register_blueprint(main_router.api.game_api_router)
client = MongoClient('localhost', 27017)
db = client['acid_rain']
user_db = db["user_db"]
for i in word_type:
    try:
        user_db.create_index([(f"high_score.{i}", DESCENDING)])
    except Exception as e:
        print(f"인덱싱 생성 실패 {i}")

DBContainer.user_db = user_db


@app.errorhandler(404)
def error_handling_404(error):
    return render_template("error_404.html")

@app.route("/", endpoint="page_main")
@auth_middleware(use_redirect=True)
def game_main_page():
    return redirect("/game")


# @app.route('/testgame')
# def test_game():
#     return render_template("./game/acid_game.html")
#
#
# @app.route('/testranking')
# def test_rank():
#     return render_template("./game/ranking.html")
#
# @app.route('/test/makeroom')
# def test_make_room():
#     return render_template("./game/make_room.html")
#
# @app.route('/test/joinroom')
# def test_join_room():
#     return render_template("./game/join_room.html")


if __name__ == '__main__':
    print(os.environ.get("IS_DEBUG"))
    socketio.run(app, debug=True if os.environ.get('IS_DEBUG') == 'True' else False, 
                 port=int(os.environ.get('PORT', 5000)) if os.environ.get('IS_DEBUG') == 'True' else int(os.environ.get('PORT', 9001)), 
                 host='0.0.0.0')
