from flask import Blueprint, render_template, Response, url_for, make_response, redirect

auth_route = Blueprint("auth", __name__, url_prefix="/auth")


@auth_route.route("/sign_in", endpoint="page_sign_in")
def sign_in_page():
    return render_template("./auth/sign_in.html")


@auth_route.route("/sign_up", endpoint="page_sign_up")
def sign_up_page():
    return render_template("./auth/sign_up.html")



@auth_route.route("/sign_out")
def sign_out():
    res = make_response(render_template("./auth/sign_out.html"))
    res.set_cookie("Authorization", "", expires=0)
    return res
