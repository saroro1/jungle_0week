const logoutButton = document.getElementById('logout-button');
const editNickname = document.getElementById('edit-nickname');
const gradeField = document.querySelectorAll('.grade')

let isEditing = false;
let isNickNameChange = false;
let isPwChange = false;
let originUserData = {};

function init() {

    //-1 처리
    gradeField.forEach(span => {
        if (span.textContent.trim() === '-1') {
            span.textContent = '기록 없음';
        }
    });

    
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

editNickname.addEventListener('click', () =>{
    enableEdit("nickname-field")
})

init();