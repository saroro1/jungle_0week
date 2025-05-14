from typing import TYPE_CHECKING
from flask import Blueprint, render_template, Response, url_for, make_response, redirect, request, g
import math

from constant import word_type
from middleware import auth_middleware
from type.database.user_entity import UserEntity

if TYPE_CHECKING:
    g.current_user: UserEntity

game_route = Blueprint("game", __name__, url_prefix="/game")
'''
/play/{gameType}
/mypage
/
/ranking
'''


@game_route.route("/ranking/<type_word>/<int:page>", endpoint="ranking")
@auth_middleware(use_redirect=True)
def game_ranking_page(type_word: str, page: int):
    if page < 1:
        page = 1

    count_per_page = 10

    my_ranking_value = None
    my_score_value = None
    current_user_nickname = None

    if hasattr(g, 'current_user') and g.current_user:
        current_user_nickname = g.current_user.nickname

        user_entity_for_score = UserEntity.findUserById(g.current_user.id)
        if user_entity_for_score and user_entity_for_score.high_score:
            my_score_value = user_entity_for_score.high_score.get(type_word)

        # 점수가 1점 이상일 때만 유효한 랭킹으로 간주, 그렇지 않으면 -1
        if my_score_value is not None and my_score_value > 0:
            rank_dict = UserEntity.getMyRanking(g.current_user.id)
            if rank_dict:
                my_ranking_value = rank_dict.get(type_word)
        else:
            my_ranking_value = -1  # 1점 이상이 아니면 랭킹 -1
            if my_score_value is None:  # 점수 자체가 없으면 0점으로 표시 (템플릿에서 '-' 처리)
                my_score_value = 0

    total_users_overall = UserEntity.countLeaderBoardUsers(type_word=type_word)

    all_leaderboard_entities = []
    if total_users_overall > 0:
        all_leaderboard_entities = UserEntity.getLeaderBoard(type=type_word, page=1, count=total_users_overall)

    top_player_data = []
    if all_leaderboard_entities:
        top_player_data = [
            {"nickname": u.nickname, "ranking": u.ranking, "score": u.high_score.get(type_word, 0)}
            for u in all_leaderboard_entities[:3]
        ]

    start_slice_for_current_page = (page - 1) * count_per_page
    end_slice_for_current_page = page * count_per_page
    current_page_entities = all_leaderboard_entities[start_slice_for_current_page:end_slice_for_current_page]

    ranking_data_for_current_page = [
        {"nickname": u.nickname, "ranking": u.ranking, "score": u.high_score.get(type_word, 0)}
        for u in current_page_entities
    ]

    total_pages_overall = 0
    if count_per_page > 0:
        total_pages_overall = math.ceil(total_users_overall / count_per_page)
    if total_pages_overall == 0 and total_users_overall > 0:
        total_pages_overall = 1

    if page > total_pages_overall and total_pages_overall > 0:
        page = total_pages_overall

    context = {
        "current_type": type_word,
        "page": page,
        "total_count": total_users_overall,
        "total_pages": total_pages_overall,
        "data": {
            "my_nickname": current_user_nickname,
            "my_ranking": my_ranking_value,
            "my_score": my_score_value,
            "top_player": top_player_data,
            "ranking": ranking_data_for_current_page
        }
    }
    return render_template("./game/ranking.html", **context)


@game_route.route("/", endpoint="main")
@auth_middleware(use_redirect=True)
def game_main_page():
    return render_template("./main.html")


@game_route.route("/play/<gametype>", endpoint="play")
@auth_middleware(use_redirect=True)
def game_play_page(gametype: str):
    print(gametype)
    if gametype not in word_type:
        return redirect("/")
    return render_template("./game/acid_game.html", gametype=gametype)


@game_route.route("/mypage", endpoint="mypage")
@auth_middleware(use_redirect=True)
def game_my_page():
    user_id = g.current_user.id
    user_nickname = g.current_user.nickname
    user_ranking = g.current_user.getMyRanking(g.current_user.id)
    user_score = g.current_user.high_score
    return render_template("./mypage.html", user_id=user_id, user_nickname=user_nickname, user_ranking=user_ranking, user_score = user_score)
