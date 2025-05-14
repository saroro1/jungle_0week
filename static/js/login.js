import {AuthHelper} from './sdk/auth.js'
document.getElementById("sign_in_btn")?.addEventListener("click", async function (e){
    const formDiv = document.getElementById("login_form")
    const formData = new FormData(formDiv);
    const id = formData.get("user_id");
    const password = formData.get("password");

    if (!this.reportValidity()) {
        e.preventDefault();
        return;
    }
    e.preventDefault();
    const res = await AuthHelper.sign_in(id, password)
    if(res.error){
        alert(res.error)
    }
    else{
        window.location.replace("/game");
    }
})