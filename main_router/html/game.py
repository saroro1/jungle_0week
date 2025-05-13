from flask import Blueprint, render_template, Response, url_for, make_response, redirect

from middleware import auth_middleware

game_route = Blueprint("game", __name__, url_prefix="/game")
'''
/play
/mypage
/
/ranking
'''





@game_route.route("/play", endpoint="play")
def game_play_page():
    return render_template("./game/acid_game.html")
