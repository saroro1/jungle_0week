import { io } from "https://cdn.socket.io/4.8.1/socket.io.esm.min.js";
/**
 * @typedef {object} GameWord
 * @property {string} word - 낙하하는 단어
 * @property {string} type - 단어 타입 ('normal', 'heal')
 * @property {number} speed - 단어 낙하 속도
 * @property {number} score - 적중 시 획득 점수
 * @property {string} uuid - 단어 식별용 UUID
 * @property {string} created_at - 생성 시간 (ISO 8601 형식)
 */

/**
 * @typedef {object} UserState
 * @property {string} user_id - 고유 사용자 ID
 * @property {number} count - 적중한 단어 개수
 * @property {number} score - 현재 점수
 * @property {number} life - 남은 생명 수
 * @property {boolean} is_host - 호스트 여부
 */

/**
 * Socket.IO 클라이언트 통신을 관리하는 클래스
 */


export class SocketClient {

  /** @type {import("socket.io-client").Socket | null} */
  socket = null;
  /** @type {string | null} */
  serverUrl = null;

  /**
   * SocketClient 인스턴스를 생성합니다.
   * @param {string} serverUrl - 연결할 Socket.IO 서버 URL
   * @example
   * const client = new SocketClient('http://localhost:5000');
   */
  constructor(serverUrl) {
    this.serverUrl = serverUrl;
  }

  /**
   * Socket.IO 서버에 연결합니다.
   * 연결 성공 또는 실패 시 콘솔에 로그를 남깁니다.
   * 외부에서 `onConnect`, `onDisconnect` 콜백을 통해 연결 상태 변경을 감지할 수 있습니다.
   */
  connect() {
    if (!this.serverUrl) {
      console.error('SocketClient: Server URL이 설정되지 않았습니다.');
      return;
    }
    // @ts-ignore
    this.socket = io(this.serverUrl, {
      transports: ['websocket'], // WebSocket을 우선적으로 사용
    });

    this.socket.on('connect', () => {
      console.log('SocketClient: 서버에 연결되었습니다. SID:', this.socket?.id);
    });

    this.socket.on('disconnect', (reason) => {
      console.log('SocketClient: 서버와 연결이 끊어졌습니다. 이유:', reason);
    });

    this.socket.on('connect_error', (error) => {
      console.error('SocketClient: 연결 오류 발생:', error);
    });
  }

  /**
   * 서버와의 연결을 명시적으로 끊습니다.
   */
  disconnect() {
    this.socket?.disconnect();
    console.log('SocketClient: 수동으로 연결을 끊었습니다.');
  }

  /**
   * 현재 서버에 연결되어 있는지 확인합니다.
   * @returns {boolean} 연결되어 있으면 true, 그렇지 않으면 false
   */
  isConnected() {
    return this.socket?.connected || false;
  }

  // --- Emitters ---

  /**
   * 서버에 사용자 인증을 요청합니다.
   * @param {string} token - 인증에 사용될 JWT 토큰
   */
  authenticate(token) {
    this.socket?.emit('authenticate', { token });
  }

  /**
   * 새로운 게임 방 생성을 요청합니다.
   * @param {"kr" | "en" | "complex"|"python"} gameType - 게임 타입 (예: 'kr', 'en')
   */
  createRoom(gameType) {
    this.socket?.emit('create_room', { game_type: gameType });
  }

  /**
   * 기존 게임 방 참가를 요청합니다.
   * @param {string} roomId - 참가할 방의 ID
   */
  joinRoom(roomId) {
    this.socket?.emit('join_room', { room_id: roomId });
  }

  /**
   * 단어 히트를 서버에 알립니다.
   * @param {string} wordUuid - 히트한 단어의 UUID
   */
  sendHit(wordUuid) {
    this.socket?.emit('hit', { uuid: wordUuid });
  }

  /**
   * 단어 미스를 서버에 알립니다.
   * @param {string} wordUuid - 미스한 단어의 UUID
   */
  sendMiss(wordUuid) {
    this.socket?.emit('miss', { uuid: wordUuid });
  }

  /**
   * 호스트가 게임 시작을 서버에 요청합니다.
   * 현재 방 ID 등은 서버에서 사용자의 세션을 통해 자동으로 알 수 있으므로 별도 파라미터는 필요 없습니다.
   */
  sendStartGame() {
    this.socket?.emit('start_game');
  }

  // --- Event Listeners (Handlers) ---

  /**
   * 서버 연결 성공 시 호출될 콜백을 등록합니다.
   * @param {() => void} callback
   */
  onConnect(callback) {
    this.socket?.on('connect', callback);
  }

  /**
   * 서버 연결 종료 시 호출될 콜백을 등록합니다.
   * @param {(reason: string) => void} callback
   */
  onDisconnect(callback) {
    this.socket?.on('disconnect', callback);
  }

  /**
   * 인증 성공 시 호출될 콜백을 등록합니다.
   * @param {(data: { user_id: string, sid: string }) => void} callback
   */
  onAuthSuccess(callback) {
    this.socket?.on('auth_success', callback);
  }

  /**
   * 인증 실패 시 호출될 콜백을 등록합니다.
   * @param {(data: { message: string }) => void} callback
   */
  onAuthFailed(callback) {
    this.socket?.on('auth_failed', callback);
  }

  /**
   * 방 생성 완료 시 호출될 콜백을 등록합니다.
   * @param {(data: { room_id: string, user_id: string, game_type: string }) => void} callback
   */
  onRoomCreated(callback) {
    this.socket?.on('room_created', callback);
  }

  /**
   * 방 참가 성공 시 호출될 콜백을 등록합니다. (본인에게 전송)
   * 서버에서 'joined_success' 이벤트를 보낼 때 호출됩니다.
   * @param {(data: { room_id: string, user_id: string, game_type: string, host_id: string, guest_id: string | null, is_host: boolean, game_started: boolean }) => void} callback
   */
  onJoinedRoom(callback) {
    this.socket?.on('joined_success', callback);
  }

  /**
   * 방 참가 실패 시 호출될 콜백을 등록합니다.
   * 서버에서 'joined_failed' 이벤트를 보낼 때 호출됩니다.
   * @param {(data: { message: string }) => void} callback
   */
  onJoinedFailed(callback) {
    this.socket?.on('joined_failed', callback);
  }

  /**
   * 방 생성 또는 기타 방 관련 작업 실패 시 호출될 콜백을 등록합니다.
   * 서버에서 'room_failed' 이벤트를 보낼 때 호출됩니다.
   * @param {(data: { message: string }) => void} callback
   */
  onRoomFailed(callback) {
    this.socket?.on('room_failed', callback);
  }

  /**
   * 상대방이 방에 참가했을 때 호출될 콜백을 등록합니다. (주로 호스트에게 전송)
   * @param {(data: { room_id: string, opponent_user_id: string }) => void} callback
   */
  onOpponentJoined(callback) {
    this.socket?.on('opponent_joined', callback);
  }

  /**
   * 게임이 곧 시작될 것을 알리는 카운트다운 시 호출될 콜백을 등록합니다.
   * @param {(data: { room_id: string, countdown: number, message?: string }) => void} callback
   */
  onGameStartingSoon(callback) {
    this.socket?.on('game_starting_soon', callback);
  }

  /**
   * 게임이 시작되었을 때 호출될 콜백을 등록합니다.
   * @param {(data: { room_id: string, message: string, initial_difficulty?: number, initial_speed?: number, initial_word_generation_interval?: number, host?: UserState, guest?: UserState }) => void} callback
   */
  onGameStarted(callback) {
    this.socket?.on('game_started', callback);
  }

  /**
   * 게임 난이도 변경 시 호출될 콜백을 등록합니다.
   * @param {(data: { room_id: string, new_difficulty: number, new_speed: number, new_word_generation_interval: number }) => void} callback
   */
  onDifficultyUpdate(callback) {
    this.socket?.on('difficulty_update', callback);
  }

  /**
   * 서버로부터 새로운 단어가 발사되었을 때 호출될 콜백을 등록합니다.
   * @param {(data: GameWord) => void} callback
   */
  onShootWord(callback) {
    this.socket?.on('shoot_word', callback);
  }

  /**
   * 단어 히트 결과 업데이트 시 호출될 콜백을 등록합니다.
   * @param {(data: { room_id: string, hitter_user_id: string, word_uuid: string, new_score: number, new_count: number, new_life: number, is_heal: boolean }) => void} callback
   */
  onWordHitUpdate(callback) {
    this.socket?.on('word_hit_update', callback);
  }

  /**
   * 단어 미스 결과 업데이트 시 호출될 콜백을 등록합니다.
   * @param {(data: { room_id: string, misser_user_id: string, word_uuid: string, new_life: number }) => void} callback
   */
  onWordMissUpdate(callback) {
    this.socket?.on('word_miss_update', callback);
  }

  /**
   * 게임 종료 시 호출될 콜백을 등록합니다.
   * @param {(data: { room_id: string, winner_id: string | null, loser_id: string | null, final_scores: Record<string, number> }) => void} callback
   */
  onGameOver(callback) {
    this.socket?.on('game_over', callback);
  }

  /**
   * 게임에서 승리했을 때 호출될 콜백을 등록합니다. (승자에게만 전송)
   * @param {(data: { room_id: string, your_score: number, opponent_score: number }) => void} callback
   */
  onWin(callback) {
    this.socket?.on('win', callback);
  }

  /**
   * 게임에서 패배했을 때 호출될 콜백을 등록합니다. (패자에게만 전송)
   * @param {(data: { room_id: string, your_score: number, opponent_score: number }) => void} callback
   */
  onDefeat(callback) {
    this.socket?.on('defeat', callback);
  }

  /**
   * 자신의 점수 변경 시 호출될 콜백을 등록합니다.
   * @param {(data: { user_id: string, new_score: number, score_delta: number }) => void} callback 
   */
  onScoreChange(callback) {
    this.socket?.on('score_change', callback);
  }

  /**
   * 자신의 생명력 변경 시 호출될 콜백을 등록합니다.
   * @param {(data: { user_id: string, new_life: number, life_delta: number, reason: string }) => void} callback 
   */
  onLifeChange(callback) {
    this.socket?.on('life_change', callback);
  }

  /**
   * 상대방의 생명력 변경 시 호출될 콜백을 등록합니다.
   * @param {(data: { opponent_user_id: string, new_life: number, life_delta: number, reason: string }) => void} callback 
   */
  onOpponentLifeChange(callback) {
    this.socket?.on('opponents_life_change', callback);
  }

  /**
 * 상대방이 게임을 떠났을 때 호출될 콜백을 등록합니다.
 * @param {(data: { message: string }) => void} callback
 */
  onOpponentLeftGame(callback) {
    this.socket?.on('opponent_left_game', callback);
  }


  /**
   * 서버로부터 일반 오류 발생 시 호출될 콜백을 등록합니다.
   * @param {(data: { message: string, details?: any }) => void} callback
   */
  onErrorOccurred(callback) {
    this.socket?.on('error_occurred', callback);
  }

  /**
   * 특정 이벤트에 대한 리스너를 제거합니다.
   * @param {string} eventName - 제거할 이벤트 이름
   * @param {Function} [callback] - 제거할 특정 콜백. 지정하지 않으면 해당 이벤트의 모든 리스너 제거.
   */
  off(eventName, callback) {
    this.socket?.off(eventName, callback);
  }
}

// 사용 예시:
// const socketClient = new SocketClient('ws://localhost:5001'); // 서버 주소에 맞게 변경
// socketClient.connect();
//
// socketClient.onConnect(() => {
//   console.log('연결 성공! 토큰으로 인증 시도.');
//   socketClient.authenticate('some-jwt-token');
// });
//
// socketClient.onAuthSuccess((data) => {
//   console.log('인증 성공:', data.user_id);
//   // 예: 방 생성 요청
//   // socketClient.createRoom('kr');
// });
//
// socketClient.onRoomCreated((data) => {
//  console.log('방 생성됨:', data);
// });
//
// socketClient.onShootWord((data) => {
//   console.log('새 단어:', data.word.word);
//   // 게임 로직 처리...
// });
//
// socketClient.onWordHitUpdate((data) => {
//   console.log('단어 히트:', data);
// });
//
// socketClient.onGameOver((data) => {
//   console.log('게임 종료!', data);
//   socketClient.disconnect();
// });
