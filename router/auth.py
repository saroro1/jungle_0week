import bcrypt
import jwt
from flask import request, Blueprint, jsonify

from constant import DBContainer
from type.req import LoginReq, SignUpReq

auth_router = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_router.route("/sign_in", methods=["POST"])
def sign_in():
    try:
        data = request.get_json()
        print(data)
        login_req = LoginReq(**data)
        user = DBContainer.user_db.find_one({"id": login_req.id})
        if not user:
            return jsonify({"error": "아이디나 비밀번호가 틀렸습니다."}), 401
        stored_hashed_pw = user.get("password")  # 이미 해싱된 비밀번호
        if not bcrypt.checkpw(login_req.password.encode('utf-8'), stored_hashed_pw.encode('utf-8')):
            return jsonify({"error": "아이디나 비밀번호가 틀렸습니다."}), 401
        access_token = jwt.encode({"id": user.get("id")}, "asdfasfasfsaf", algorithm="HS256")

        response = jsonify({"result": {
            "type": "bearer",
            "access_token": access_token
        }})
        response.headers["Authorization"] = f"Bearer {access_token}"
        return response
    except Exception as e:
        print(e)
        return jsonify({"error": "올바르지 않은 요청입니다"}), 400


@auth_router.route("/sign_up", methods=["POST"])
def sign_up():
    try:
        data = request.get_json()
        print(data)
        sign_up_req = SignUpReq(**data)
        user = DBContainer.user_db.find_one({"id": sign_up_req.id})
        if user:
            return jsonify({"error": "이미 아이디가 존재합니다."}), 400
        password_result = bcrypt.hashpw(sign_up_req.password.encode("utf-8"), bcrypt.gensalt())
        sign_up_req.password = password_result.decode("UTF-8")
        if len(sign_up_req.nickname) > 20:
            return jsonify({"error": "별명은 20자를 넘을 수 없습니다."}), 400
        DBContainer.user_db.insert_one(sign_up_req.__dict__)
        return jsonify({
            data: {
                "id": sign_up_req.id,
                "nickname": sign_up_req.nickname
            }
        })
    except Exception as e:
        print(e)
        return jsonify({"error": "올바르지 않은 요청입니다"}), 400
