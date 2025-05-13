import {GameHelper} from "./sdk/game.js";

const gameArea = document.getElementById('game-area');
const wordInput = document.getElementById('word-input');
const scoreDisplay = document.getElementById('score');
const livesDisplay = document.getElementById('lives');
const startScreen = document.getElementById('start-screen');
const gameOverScreen = document.getElementById('game-over-screen');
const startButton = document.getElementById('start-button');
const restartButton = document.getElementById('restart-button');
const finalScoreDisplay = document.getElementById('final-score');

// 게임 설정 및 상태 변수
const wordList = []; 
let gameScore = 0;
let lives = 3;
let activeWords = []; // ActiveWord 클래스
let gameInterval; // 단어 떨어지는 인터벌 ID
let wordGenerationInterval; // 단어 생성 인터벌 ID
const generationRate = 2000; // 단어 생성 간격 (ms)
const updateRate = 50; // 화면 업데이트 간격 (ms)
let difficalty = 0;
const speedConst = 0.2;
let generationCount = 0;
const STAGECHANGE = 1;
const generationBlock = 100;
const MINGENERATIONTIME = 500;
let index = 0;
const loadBuffer = 5

// word class
class ActiveWord {
    baseScore = 10
    multiplier = 1.5
    minLength = 3
    constructor(word, type = "normal", fallSpeed = 2){
        // console.log(`${word}, ${type}, ${fallSpeed}`);
        const wordElement = document.createElement('div');
        wordElement.classList.add('word');
        wordElement.textContent = word;

        // 가로 위치 랜덤 설정 (게임 영역 너비 안에서)
        const gameAreaWidth = gameArea.clientWidth;
        // 단어 너비를 고려하여 최대 left 값 계산 (대략적으로)
        const maxLeft = gameAreaWidth - (word.length * 15); // 글자 크기에 따라 조절 필요
        wordElement.style.left = `${Math.max(0, Math.random() * maxLeft)}px`;
        wordElement.style.top = `0px`; // 항상 위에서 시작

        this.type = type;
        this.score = this.getScore(word,type);
        this.fallSpeed = fallSpeed;

        gameArea.appendChild(wordElement);

        this.wordElement = wordElement;
    }

    getScore(txt, type) {
        const exponent = txt.length - this.minLength;
        switch(type){
            default:
                return Math.round(this.baseScore * Math.pow(this.multiplier, exponent)) + difficalty * 100;
        }
    }

    setWord(newWord) {
        this.wordElement.textContent = newWord;
        this.score = this.getScore(newWord,this.type);
    }

    getWord(){
        return this.wordElement.textContent;
    }

    getLeft(){
        return parseInt(this.wordElement.style.left || 0);
    }

    setLeft(newLeft){
        this.wordElement.style.left = newLeft;
    }

    getTop(){
        return parseInt(this.wordElement.style.top || 0);
    }

    setTop(newTop){
        this.wordElement.style.top = newTop;
    }

    move(){
        // 단어 아래로 이동
        const currentTop = this.getTop();
        // console.log(`call move ${currentTop}`);
        this.setTop(`${currentTop + this.fallSpeed}px`);
    }

    checkCrash(){
        // console.log("call checkCrash");
        // 바닥 충돌 감지
        if (this.getTop() + this.wordElement.offsetHeight >= gameArea.clientHeight) {
            this.removeWord(false); // false: 바닥 충돌
            return true;
        }
        return false;
    }

    removeWord(matched) {
        // console.log("call removeWord");
        // 화면에서 제거
        this.wordElement.remove();

        if (!matched) { // 바닥에 닿았을 경우
            lives--;
            livesDisplay.textContent = lives;
            if (lives <= 0) {
                gameOver();
            }
            
        } else { // 단어를 맞췄을 경우
            scoreDisplay.textContent = gameScore + this.score;
            gameScore += this.score;
        }
    }
}

// fisher yates 
function shuffle(array) {
  let m = array.length,
    t,
    i

  // While there remain elements to shuffle…
  while (m) {
    // Pick a remaining element…
    i = Math.floor(Math.random() * m--)

    // And swap it with the current element.
    t = array[m]
    array[m] = array[i]
    array[i] = t
  }

  return array
}

// 서버에 단어 요청
async function requestWords(){
    const res = await GameHelper.getWords("kr", 20);
    return res.result ?? [];
}

// 셔플 함수
async function updateWordList(){
    let newWords = await requestWords();
    newWords = shuffle(newWords);
    wordList.push(...newWords);
}

// 초기화 함수
function initGame(initScore = 0, initLives = 3) {
    activeWords = [];
    gameScore = initScore;
    lives = initLives;
    scoreDisplay.textContent = gameScore;
    livesDisplay.textContent = lives;
    gameArea.innerHTML = ''; // 게임 영역 초기화
    wordInput.value = '';
    wordInput.disabled = true; // 게임 시작 전 입력 비활성화
    gameOverScreen.style.display = 'none';
    startScreen.style.display = 'flex'; // 시작 화면 표시
}

// 게임 시작 함수
function startGame(initLives = 3) {
    // 단어 서버에서 받아오기
    updateWordList();
    console.log(wordList);

    startScreen.style.display = 'none';
    gameOverScreen.style.display = 'none';
    wordInput.disabled = false;
    wordInput.focus();
    lives = initLives; // 시작 시 목숨 초기화
    gameScore = 0; // 시작 시 점수 초기화
    index = 0;
    difficalty = 0;
    livesDisplay.textContent = lives;
    scoreDisplay.textContent = gameScore;
    activeWords = [];
    gameArea.innerHTML = '';

    // 일정 간격으로 단어 생성 시작
    wordGenerationInterval = setInterval(generateWord, generationRate);
    // 일정 간격으로 단어 이동 및 충돌 감지 시작
    gameInterval = setInterval(updateGame, updateRate);
}

// 게임 오버 함수
function gameOver() {
    clearInterval(gameInterval);
    clearInterval(wordGenerationInterval);
    wordInput.disabled = true;
    finalScoreDisplay.textContent = gameScore;
    gameOverScreen.style.display = 'flex'; // 게임 오버 화면 표시
}

// 단어 생성 함수 -> 서버에서 보내주면 셔플
function generateWord() {
    console.log("generate word");
    const newWord = new ActiveWord(wordList[index].word,wordList[index].type,2+difficalty * speedConst);
    index++;
    activeWords.push(newWord);

    //남은 갯수가 loadBuffer이하면 wordListUpdate
    if(wordList.length - index < loadBuffer){
        updateWordList();
    }
    if(generationCount++ == STAGECHANGE){
        generationCount = 0;
        difficalty ++;
        clearInterval(wordGenerationInterval);
        let generateRate = generationRate - difficalty * generationBlock;
        generateRate = generateRate < MINGENERATIONTIME ? MINGENERATIONTIME : generateRate
        wordGenerationInterval = setInterval(generateWord, generateRate);
    }
}

// 게임 업데이트 함수 (단어 이동 및 충돌 감지)
function updateGame() {
    let i = 0
    while(i<activeWords.length){
        const wordData = activeWords[i++];
        wordData.move();
        if(wordData.checkCrash()){
            i--;
            activeWords.splice(i,1);
        }
    }
}

// 입력 처리 함수
function checkInput(e) {
    if(e.key === "Enter" && this === document.activeElement){
        const typedWord = this.value.trim();
        wordInput.value = ''; // 입력 필드 초기화
        if (!typedWord) return; // 빈 입력 무시
        const index = activeWords.findIndex(word => word.getWord() === typedWord);
        if (index !== -1) {
            // 맞는게 있을 때
            activeWords[index].removeWord(true);
            activeWords.splice(index,1);
        }
    }
    
}

// 이벤트 리스너 설정
startButton.addEventListener('click', () => startGame(3));
restartButton.addEventListener('click', () => startGame(3)); // 다시 시작 버튼도 startGame 호출
wordInput.addEventListener('keydown', checkInput); // 입력할 때마다 체크

// 페이지 로드 시 초기화
initGame(0,3);