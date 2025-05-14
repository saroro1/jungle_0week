import {AuthHelper} from './sdk/auth.js'

document
        .getElementById("duplicated_btn")
        ?.addEventListener("click", async (e) => {
          e.preventDefault();
          const user_id = document.getElementById("user_id").value;
          const res = await AuthHelper.check_duplicate(user_id);
          if (res.result.is_duplicated) {
            alert("이미 아이디가 있습니다. 다른 아이디를 사용해주세요");
            return;
          } else {
            alert("사용 가능한 아이디입니다.");
          }
        });

document.getElementById("sign_up_btn").addEventListener("click", async function(e){

          const formDiv = document.getElementById("sign_in_form")
          const formData = new FormData(formDiv);
          if (formData.get("password_confirm") !== formData.get("password")) {
              e.preventDefault();
            alert("비밀번호랑 비밀번호 확인 값이 다릅니다.");
            return;
          }
          if (!this.reportValidity()) {
                e.preventDefault();
                return;
              }
          e.preventDefault();
          const res = await AuthHelper.sign_up(
            formData.get("user_id"),
            formData.get("password"),
            formData.get("nickname")
          );

          if (res.error) {
            alert(res.error);
          } else {
            alert("회원가입 성공");
            window.location.replace("/auth/sign_in");

          }
        });
