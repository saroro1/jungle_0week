import { SocketClient } from "./sdk/socket.js"; 
const gameContainer = document.getElementById('game-container');
const modalMakeRoom = document.getElementById('modal_MakeRoom');
const modalJoinRoom = document.getElementById('modal_JoinRoom');

//host modal
const roomLink = document.getElementById('room-link');
const copyButton = document.getElementById('copyButton');
const gameStartButton = document.getElementById("");

let isHost = false;

function initScreen(){
    console.log("here");
    console.log(gameContainer.dataset.gametype);
    console.log(gameContainer.dataset.membertype);
    if(gameContainer.dataset.membertype == "host"){
        modalMakeRoom.style.display = "block";
        modalJoinRoom.remove();
        isHost = true;
    } else{
        modalJoinRoom.style.display = "block";
        modalMakeRoom.remove();
    }
}
const socket = new SocketClient(window.location.protocol+"//"+window.location.host);
function socketConnect(){
    socket.connect();
    socket.authenticate(sessionStorage.getItem("_auth_token"));
    socket.onAuthFailed((data)=>{
        console.error(data.message);
    });
}

function makeRoom(){
    socket.createRoom("kr");
    socket.onRoomFailed((data)=>{
        console.error(data.message);
    })
    socket.onRoomCreated((data)=>{
        console.log("roomCreate");
        roomLink.textContent = data.room_id;
    })

}

copyButton.addEventListener('click',()=>{
    navigator.clipboard.writeText(roomLink.textContent);
});



initScreen();
socketConnect();
if(isHost){
    makeRoom();
}