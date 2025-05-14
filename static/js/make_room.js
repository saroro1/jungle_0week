import { SocketClient } from "./sdk/socket.js"; 

const socket = new SocketClient("127.0.0.1:9001");

function socketConnect(){
    socket.authenticate()
}