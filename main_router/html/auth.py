from flask import Blueprint, render_template

auth_route = Blueprint("auth", __name__, url_prefix="/auth")


@auth_route.route("/sign_in")
def sign_in_page():
    return render_template("./auth/sign_in.html")


@auth_route.route("/sign_up")
def sign_up_page():
    return render_template("./auth/sign_up.html")
