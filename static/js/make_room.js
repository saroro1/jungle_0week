
import { SocketClient } from "./sdk/socket.js"; 

const socket = new SocketClient("http://127.0.0.1:9001");
const printLink = document.getElementById("link");

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
        printLink.textContent = data.room_id;
    })

}
socketConnect();
makeRoom();