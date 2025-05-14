const logoutButton = document.getElementById('logout-button');
const editNickname = document.getElementById('edit-nickname');

let isEditing = false;
let originUserData = {};

function enableEdit(fieldId) {
    const field = document.getElementById(fieldId);
    field.readOnly = false;
    field.focus();
    field.classList.remove('bg-gray-100');
    field.classList.add('bg-white');
    isEditing = true;
    checkAnyChange();
}

function checkAnyChange() {
    const passwordField = document.getElementById("passwordField");
    const userField = document.getElementById("userField");
    const saveButton = document.getElementById("saveButton");
    const isPasswordChange = passwordField.value !== "password123";
    const isUserChange = userField.value !== "User";
    saveButton.disabled = !isPasswordChange && !isUserChange;
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