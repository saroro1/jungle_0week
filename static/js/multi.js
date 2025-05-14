import { SocketClient } from "./sdk/socket.js";
const gameContainer = document.getElementById('game-container');
const modalJoinRoom = document.getElementById('modal_JoinRoom');
const body = document.querySelector("body");

//host modal
const modalMakeRoom = document.getElementById('modal_MakeRoom');
const roomLink = document.getElementById('room-link');
const copyButton = document.getElementById('copyButton');
const gameStartButton = document.getElementById('MultiStart_Button');
let roomCreated = false;

//guest modal
const roomCodeInput = document.getElementById('roomCodeInput');
const joinRoomButton = document.getElementById('join-Button');

//game
const gameArea = document.getElementById('game-area');
const wordInput = document.getElementById('word-input');
const opponentLivesDisplay = document.getElementById('opponent-lives');
const livesDisplay = document.getElementById('lives');
const startScreen = document.getElementById('start-screen');
const gameOverScreen = document.getElementById('game-over-screen');
const resultDisplay = document.getElementById('result');
const newHighScore = document.getElementById('new-high-score');
const countdownDisplay = document.getElementById('countdown');
const goToMainButton = document.getElementById('main-page-button');
const restartButton = document.getElementById('restart-button');
const myScoreScreen = document.getElementById('user-score');
const opponentScoreScreen = document.getElementById('opponent-score');
let isWin = false;

//음악
const sounds = {
    "bgm": new Audio("/static/asset/music/bgm.mp3"),
    "hitPath": "/static/asset/music/hit2.m4a",
    "failPath": "/static/asset/music/fail.m4a",
    "gameOver": new Audio("/static/asset/music/game_over.mp3"),
    "crashPath": "/static/asset/music/crash.m4a",
    "countDown": new Audio("/static/asset/music/countdown.mp3")
}
sounds["bgm"].loop = true;
sounds["bgm"].volume = 0.3
sounds["countDown"].volume = 0.5

// 게임 설정 및 상태 변수
const wordList = [];
let myScore = 0;
let opponentScore = 0;
let lives = 5;
let activeWords = []; // ActiveWord 클래스

let gameType = "none";

let lastTime = 0;
let animationFrameId;

let isPaused = false;      // 일시 정지 상태 여부
let gameEnd = false;


// word class
class ActiveWord {
    y = 0; // 내부 y 위치 (float)

    constructor(word, uuid, type = "normal", fallSpeed = 100) { // fallSpeed는 이제 px/sec
        // console.log(`${word}, ${type}, ${fallSpeed}`);
        const wordElement = document.createElement('div');
        wordElement.classList.add('word');
        wordElement.textContent = word;

        const gameAreaWidth = gameArea.clientWidth;
        console.log(word)
        const maxLeft = gameAreaWidth - (word.length * 30);
        wordElement.style.left = `${Math.max(0, Math.random() * maxLeft)}px`;
        this.y = 0; // y 위치 초기화
        wordElement.style.top = `${this.y}px`;

        this.type = type;
        this.uuid = uuid;
        this.fallSpeed = fallSpeed; // 초당 픽셀 이동 속도

        gameArea.appendChild(wordElement);

        this.wordElement = wordElement;
        this.setColor(type);
    }


    setColor(type) {
        switch (type) {
            case "normal":
                this.wordElement.style.color = 'black';
                break
            case "heal":
                this.wordElement.style.color = 'cyan';
                break
            default:
                { }
        }
    }

    setWord(newWord) {
        this.wordElement.textContent = newWord;
    }

    getWord() {
        return this.wordElement.textContent;
    }

    getLeft() {
        return parseInt(this.wordElement.style.left || 0);
    }

    setLeft(newLeft) {
        this.wordElement.style.left = newLeft;
    }



    setTop(newTopY) { // DOM 업데이트와 내부 y값 업데이트 분리
        this.y = newTopY;
        this.wordElement.style.top = `${this.y}px`;
    }

    move(deltaTime) {
        const distanceToMove = this.fallSpeed * deltaTime;
        this.y += distanceToMove; // 내부 y 위치 업데이트
        this.wordElement.style.top = `${this.y}px`; // DOM 업데이트
    }

    checkCrash() {
        // 바닥 충돌 감지 (내부 y 위치 사용)
        if (this.y + this.wordElement.offsetHeight >= gameArea.clientHeight) {
            this.removeWord(false);
            new Audio(sounds["crashPath"]).play();
            return true;
        }
        return false;
    }

    removeWord(matched) {
        // console.log("call removeWord");
        // 화면에서 제거
        this.wordElement.remove();

        if (!matched) { // 바닥에 닿았을 경우
            socket.sendMiss(this.uuid);

        } else { // 단어를 맞췄을 경우
            socket.sendHit(this.uuid);
        }
    }
}

// 초기화 함수
function initGame() {
    activeWords = [];
    gameType = gameContainer.dataset.gametype;

    livesDisplay.textContent = lives;
    gameArea.innerHTML = '';
    wordInput.value = '';
    wordInput.disabled = true;
    gameOverScreen.style.display = 'none';
    startScreen.style.display = 'none';
}

// 게임 루프 함수 (requestAnimationFrame 사용)
function gameLoop(currentTime) {
    if (!lastTime) {
        lastTime = currentTime;
    }
    const deltaTime = (currentTime - lastTime) / 1000;
    lastTime = currentTime;

    updateGame(deltaTime);

    if (lives > 0) {
        animationFrameId = requestAnimationFrame(gameLoop);
    }
}


// 게임 시작 함수
async function startGame(initLives = 3) {
    gameEnd = false;
    resetGameDisplay();

    // 단어 서버에서 받아오기
    wordList.length = 0;
    // console.log(gameType);

    await startCountdown();
    startScreen.style.display = 'none';
    wordInput.disabled = false;
    wordInput.focus();
    lives = initLives;

    livesDisplay.textContent = lives;
    activeWords = [];
    gameArea.innerHTML = '';

    sounds["bgm"].play();


    lastTime = 0;
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null; // 명시적으로 null 할당
    }
    animationFrameId = requestAnimationFrame(gameLoop);
}

// 게임 오버 함수
function gameOver() {
    gameEnd = true;
    sounds["bgm"].pause();
    sounds["bgm"].currentTime = 0;
    console.log(gameType)

    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
    }

    wordInput.disabled = true;

    myScoreScreen.textContent = myScore;
    opponentScoreScreen.textContent = opponentScore;
    resultDisplay.textContent = isWin ? "Victory" : "Defeat";

    gameOverScreen.style.display = 'flex';
    sounds["gameOver"].play()
}

// 게임 업데이트 함수 (단어 이동 및 충돌 감지)
function updateGame(deltaTime) {
    for (let i = activeWords.length - 1; i >= 0; i--) {
        const wordData = activeWords[i];
        wordData.move(deltaTime);
        if (wordData.checkCrash()) {
            activeWords.splice(i, 1);
        }
    }
}

// 입력 처리 함수
function checkInput(e) {
    // console.log("check");
    if (e.key === "Enter" && this === document.activeElement) {
        const typedWord = this.value.trim();
        wordInput.value = '';
        if (!typedWord) return;

        const wordIndex = activeWords.findIndex(word => word.getWord() === typedWord);
        if (wordIndex !== -1) {
            activeWords[wordIndex].removeWord(true);
            activeWords.splice(wordIndex, 1);
            new Audio(sounds["hitPath"]).play();
            // console.log("hit");
        }
        else {
            new Audio(sounds["failPath"]).play();
            // console.log("fail");
        }
    }
}


async function startCountdown() {
    sounds["countDown"].play();
    return new Promise((resolve) => {
        let count = 3;
        countdownDisplay.textContent = count;
        countdownDisplay.style.display = 'block';
        // 처음 애니메이션 클래스 추가
        countdownDisplay.classList.add('animate-countdown');

        const countdownInterval = setInterval(() => {
            count--;
            if (count > 0) {
                countdownDisplay.textContent = count;
                // 애니메이션 재실행을 위해 클래스 제거 후 다시 추가 (작은 딜레이 적용)
                countdownDisplay.classList.remove('animate-countdown');
                setTimeout(() => {
                    countdownDisplay.classList.add('animate-countdown');
                }, 50); // 딜레이 값 조정 가능
            } else if (count === 0) {
                countdownDisplay.textContent = '시작!';
                countdownDisplay.classList.remove('animate-countdown');
                setTimeout(() => {
                    countdownDisplay.classList.add('animate-countdown');
                }, 50);
            } else {
                clearInterval(countdownInterval);
                countdownDisplay.style.display = 'none';
                resolve();
            }
        }, 1000);
    });
}

function resetGameDisplay() {
    startScreen.style.display = 'flex';
    countdownDisplay.style.display = 'none';
    gameOverScreen.style.display = 'none';
    newHighScore.style.display = 'none';
    sounds["gameOver"].pause();
    sounds["gameOver"].currentTime = 0;
}

// //퍼즈 함수
// function pause() {
//     sounds["bgm"].pause();
//     if (!isPaused) {

//         // 애니메이션 프레임 중단
//         if (animationFrameId) {
//             cancelAnimationFrame(animationFrameId);
//             animationFrameId = null;
//         }
//         isPaused = true;
//         console.log("애니메이션이 일시 정지되었습니다.");
//     } else {
//         console.log("애니메이션은 이미 일시 정지된 상태입니다.");
//     }
// }

// function resume() {
//     sounds["bgm"].play();
//     if (isPaused) {

//         // 애니메이션 프레임 재개
//         if (!animationFrameId) {
//             lastTime = performance.now(); // 재개 시점 기준으로 lastTime 초기화
//             animationFrameId = requestAnimationFrame(gameLoop);
//         }
//         isPaused = false;
//         wordInput.focus();
//     } else {
//     }
// }

// document.addEventListener("visibilitychange", function () {
//     //게임 종료시는 작동 안함.
//     if (gameEnd) {
//         return;
//     }
//     if (document.hidden) {
//         // 사용자가 창을 벗어났을 때 실행할 코드
//         pause();
//     } else {
//         // 사용자가 다시 창으로 돌아왔을 때 실행할 코드
//         resume();
//     }
// });


// 이벤트 리스너 설정
restartButton.addEventListener('click', () => window.location.reload());
goToMainButton.addEventListener('click', () => {
    window.location.replace("/");
});

wordInput.addEventListener('keypress', checkInput);

// //esc 일시정지
// window.addEventListener('keydown', function (e) {
//     if (e.code === 'Escape') {
//         console.log("ESC");
//         pause();
//         alert("일시정지\n확인을 누르면 재개");
//         resume();
//     }
// });

let isHost = false;

function initScreen() {
    console.log("here");
    console.log(gameContainer.dataset.gametype);
    console.log(gameContainer.dataset.membertype);
    if (gameContainer.dataset.membertype == "host") {
        modalMakeRoom.style.display = "block";
        modalJoinRoom.remove();
        isHost = true;
    } else {
        modalJoinRoom.style.display = "block";
        modalMakeRoom.remove();
    }
}
const socket = new SocketClient(window.location.protocol + "//" + window.location.host);
function socketConnect() {
    socket.connect();
    socket.authenticate(sessionStorage.getItem("_auth_token"));
    //소켓 listen
    socket.onAuthFailed((data) => {
        console.error(data.message);
    });

    socket.onRoomFailed((data) => {
        console.error(data.message);
    })
    socket.onRoomCreated((data) => {
        console.log(`"roomCreate" ${data.room_id}`);
        console
        roomLink.textContent = data.room_id;
    })

    //곧 게임 시작
    socket.onGameStartingSoon((data) => {
        console.log(data.countdown);
        console.log(data.message);
        gameContainer.style.display = 'block';
        if (isHost) {
            modalMakeRoom.style.display = 'none';
        } else {
            modalJoinRoom.style.display = 'none';
        }

        body.classList.add("noimage");
        body.style.backgroundColor = "#000000";
        initGame(0, 3);
        startGame(3);
    });

    //워드 생성
    socket.onShootWord((data) => {
        const newWord = new ActiveWord(data.word, data.uuid, data.type, data.speed);
        activeWords.push(newWord);
    });

    //목숨 변경
    socket.onLifeChange((data) => {
        console.log(data.new_life);
        lives = data.new_life;
        livesDisplay.textContent = data.new_life;
    })

    //상대 목숨 변경
    socket.onOpponentLifeChange((data) => {
        console.log(data.new_life);
        opponentLivesDisplay.textContent = data.new_life;
    })

    //승리
    socket.onWin((data) => {
        isWin = true;
        myScore = data.your_score;
        opponentScore = data.opponent_score;
        gameOver();
    })

    //패배
    socket.onDefeat((data) => {
        isWin = false;
        myScore = data.your_score;
        opponentScore = data.opponent_score;
        gameOver();
    })

    //상대 참여
    socket.onOpponentJoined((data) => {
        console.log("상대 참여");
        gameStartButton.classList.remove("hidden");
    });

    socket.onJoinedRoom((data) => {
        console.log(data.game_started);
    });
    socket.onJoinedFailed((data) => {
        console.error(data.message)
    })

}

function makeRoom() {
    socket.createRoom(gameContainer.dataset.gametype);
}

function joinRoom(link) {
    socket.joinRoom(link);
}

copyButton.addEventListener('click', () => {
    if (roomCreated) {
        console.log("복사하기");
        window.navigator.clipboard.writeText(roomLink.textContent);
    } else {
        makeRoom();
        copyButton.textContent = "복사하기"
        roomCreated = true;
    }
});

gameStartButton.addEventListener('click', () => {
    socket.sendStartGame();
})

joinRoomButton.addEventListener('click', () => {
    const link = roomCodeInput.value;
    joinRoom(link);
})

//실행 부
initScreen();
socketConnect();

