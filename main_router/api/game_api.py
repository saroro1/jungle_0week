from flask import Blueprint

game_api_router = Blueprint("game_api", __name__, url_prefix="/api/game")


# kr en complex
@game_api_router.route('/word/<word_type>/<count>', methods=["GET"])
def get_words(word_type: str, count: int):
    pass
