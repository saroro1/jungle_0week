
import { SocketClient } from "./sdk/socket.js"; 

const socket = new SocketClient("http://127.0.0.1:9001");
const inputLink = document.getElementById("link");
const join_room_button = document.getElementById("join_room");

function socketConnect(){
    socket.connect();
    socket.authenticate(sessionStorage.getItem("_auth_token"));
    socket.onAuthFailed((data)=>{
        console.error(data.message);
    });
}

function joinRoom(link){
    socket.joinRoom(link);
    socket.onJoinedRoom((data)=>{
        console.log(data.game_started);
    });
    socket.onJoinedFailed((data)=>{
        console.error(data.message)
    })

}
socketConnect();

join_room_button.addEventListener("click",()=>{
    const link = inputLink.value;
    joinRoom(link);
})