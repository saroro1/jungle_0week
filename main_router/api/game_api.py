from random import shuffle

from flask import Blueprint, jsonify

from constant.eng_words import eng_word
from constant.kor_words import kor_word
from middleware import auth_middleware

game_api_router = Blueprint("game_api", __name__, url_prefix="/api/game")


@game_api_router.route("/word/<type_word>/<word_count>", methods=["GET"])
@auth_middleware()
def getWord(type_word: str, word_count: int):
    try:
        int_count = int(word_count)
        if type_word == "en":
            word = eng_word[::]

        elif type_word == "kr":
            word = kor_word[::]
        else:
            return jsonify({"error": "잘못된 요청입니다"}), 400
        shuffle(word)
        res = [{"word": value, "type": "heal" if key == 0 else "normal"} for key, value in enumerate(word[:int_count])]
        return jsonify({"result": res})
    except Exception as e:
        print(e)
        return jsonify({"error": "잘못된 요청입니다"}), 400
