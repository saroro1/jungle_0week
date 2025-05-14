import { AuthHelper } from "./sdk/auth.js";

const logoutButton = document.getElementById('logout-button');
const editNickname = document.getElementById('edit-nickname');
const editPw = document.getElementById('edit-pw');
const gradeField = document.querySelectorAll('.grade');
const nicknameField = document.getElementById('nickname-field');
const pwField = document.getElementById('password-field');
const saveButton = document.getElementById('saveButton');

let isEditing = false;

let isNickNameChange = false;
let isPwChange = false;

let originUserData = { "nickname": "", "pw": "" };

function init() {

    //-1 처리
    gradeField.forEach(span => {
        if (span.textContent.trim() === '-1') {
            span.textContent = '기록 없음';
        }
    });

    originUserData["nickname"] = nicknameField.value;
}

function enableEdit(fieldId) {
    const field = document.getElementById(fieldId);
    field.readOnly = false;
    field.focus();
    field.classList.remove('bg-gray-100');
    field.classList.add('bg-white');
    isEditing = true;
}


function saveChanges() {
    const passwordField = document.getElementById("passwordField");
    const userField = document.getElementById("userField");
    const saveButton = document.getElementById("saveButton");

    alert(
        `Changes saved:\nUsername: ${userField.value}\nPassword: ${passwordField.value}`
    );
    saveButton.disabled = true;
}

logoutButton.addEventListener('click', () => {
    console.log("push");
    window.location.replace("/auth/sign_out");
})

editNickname.addEventListener('click', () => {
    enableEdit("nickname-field");
})

editPw.addEventListener('click', () => {
    enableEdit("password-field");
});

nicknameField.addEventListener('keypress', checkChange);
pwField.addEventListener('keypress', checkChange);

function checkChange(e) {
    console.log(e.key);
    if (nicknameField.value !== originUserData["nickname"]) {
        isNickNameChange = true;
    }
    if (pwField.value !== originUserData["pw"]) {
        isPwChange = true;
    }
    if (isNickNameChange || isPwChange) {
        saveButton.disabled = false;
    }
}

async function modifyUser() {
    const new_nickname = nicknameField.value;
    const new_pw = pwField.value === "" ? null : pwField.value;

    if (new_nickname === "") {
        alert("닉네임은 공백일 수 없습니다.");
    } else {
        response = await AuthHelper.modify_user({ nickname: new_nickname, password: new_pw });
        if (response.result === "ok") {
            alert("수정 성공");
            originUserData["nickname"] = new_nickname;
            originUserData["pw"] = new_pw;
        }
        if (respone.error) {
            alert("정보 수정에 실패하였습니다.");
        }
    }
}

saveButton.addEventListener('click', modifyUser);

init();