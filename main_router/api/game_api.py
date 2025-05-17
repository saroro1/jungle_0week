from random import shuffle
from typing import TYPE_CHECKING
import math

from flask import Blueprint, g, jsonify, request

from constant import word_type, DBContainer
from constant.eng_words import eng_word
from constant.kor_words import kor_word
from constant.python_function_name import python_function_and_method_names
from middleware import auth_middleware
from type.database.user_entity import UserEntity

game_api_router = Blueprint("game_api", __name__, url_prefix="/api/game")

if TYPE_CHECKING:
    g.current_user: UserEntity


@game_api_router.route("/word/<type_word>/<word_count>", methods=["GET"])
@auth_middleware()
def getWord(type_word: str, word_count: int):
    try:
        int_count = int(word_count)
        if type_word == "en":
            word = eng_word[::]

        elif type_word == "kr":
            word = kor_word[::]
        elif type_word == "complex":
            word = eng_word[::] + kor_word[::]
        elif type_word == "python":
            word = python_function_and_method_names[::]
        else:
            return jsonify({"error": "잘못된 요청입니다"}), 400
        shuffle(word)
        res = [{"word": value, "type": "heal" if key == 0 else "normal"} for key, value in enumerate(word[:int_count])]
        return jsonify({"result": res})
    except Exception as e:
        print(e)
        return jsonify({"error": "잘못된 요청입니다"}), 400


@game_api_router.route("/ranking/<type_word>/<page>/<count>", methods=["GET"])
@auth_middleware()
def get_leaderboard(type_word: str, page: int, count: int):
    try:
        page = int(page)
        count = int(count)
        if type_word not in word_type:
            return jsonify({"error": "잘못된 요청입니다"}), 400
        if page <= 0 or count <= 0:
            return jsonify({"error": "페이지와 카운트는 0보다 커야합니다."}), 400

        leaderboard_users = UserEntity.getLeaderBoard(type=type_word, page=page, count=count)
        leaderboard_result = [{"nickname": user.nickname, "ranking": user.ranking} for user in leaderboard_users]

        total_users_count = UserEntity.countLeaderBoardUsers(type_word=type_word)
        total_page = math.ceil(total_users_count / count) if count > 0 else 0

        return jsonify({
            "result": {
                "ranking": leaderboard_result,
                "total_count": total_users_count,
                "total_page": total_page,
                "page": page,
                "count": count
            }
        })
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(e)
        return jsonify({"error": "서버 오류가 발생했습니다"}), 500


@game_api_router.route("/highscore", methods=["POST"])
@auth_middleware()
def set_highscore():
    try:
        data = request.get_json()
        score_type = data.get("score_type")
        requested_score = data.get("score")

        if not all([score_type, isinstance(requested_score, int)]):
            return jsonify({"error": "잘못된 요청 파라미터입니다."}), 400
        if score_type not in word_type:
            return jsonify({"error": "지원되지 않는 점수 타입입니다."}), 400

        user_id = g.current_user.id

        UserEntity.setHighScore(user_id=user_id, score_type=score_type, score=requested_score)
        user_doc_for_score = UserEntity.findUserById(
            user_id=user_id
        )
        if not user_doc_for_score:
            print(f"Critical: User {user_id} identified by auth_middleware, but not found in DB for highscore check.")
            return jsonify({"error": "사용자 정보를 찾는 데 문제가 발생했습니다."}), 500

        is_new_score_a_highscore = (requested_score > g.current_user.high_score.get(score_type))

        my_ranking_info = UserEntity.getMyRanking(user_id=user_id)
        my_ranking = -1
        if my_ranking_info and my_ranking_info[score_type] > 0:
            my_ranking = my_ranking_info[score_type]

        response_data = {
            "nickname" : user_doc_for_score.nickname,
            "is_highscore": is_new_score_a_highscore,
            "my_ranking": my_ranking,
            "word_type": score_type
        }

        return jsonify({"result": response_data}), 200

    except Exception as e:
        import traceback
        print(
            f"Error in set_highscore for user {g.current_user.id if g.get('current_user') else 'Unknown'}: {e}\\n{traceback.format_exc()}")
        return jsonify({"error": "서버 내부 오류가 발생했습니다."}), 500


@game_api_router.route("/my_rank", methods=["GET"])
@auth_middleware()
def get_my_rank():
    try:
        user_id = g.current_user.id
        ranking = UserEntity.getMyRanking(user_id=user_id)
        if ranking:
            return jsonify({"result": ranking})
        else:
            return jsonify({"error": "랭킹 정보를 가져올 수 없습니다."}), 404
    except Exception as e:
        print(e)
        return jsonify({"error": "서버 오류가 발생했습니다"}), 500
