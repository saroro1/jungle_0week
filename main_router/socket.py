from flask import request
from flask_socketio import SocketIO, emit, join_room as ws_join_room, leave_room as ws_leave_room, disconnect
import uuid
import time
from dataclasses import dataclass, field, asdict
from functools import wraps # 데코레이터용 임포트
import random # 단어 셔플 및 선택용

from constant import eng_word, kor_word
from utils.jwt import Jwt # JWT 유틸리티 임포트
from jwt import ExpiredSignatureError, InvalidTokenError # JWT 예외 임포트

# SocketIO 인스턴스 생성. 실제 app과의 연결은 메인 app 파일에서 수행.
socketio = SocketIO()

# --- 전역 상수 정의 ---
MIN_WORD_GENERATION_INTERVAL = 0.6 # 최소 단어 생성 간격 (초)
MAX_VALID_HIT_DURATION = 14.0  # 단어 생성 후 유효한 hit으로 인정되는 최대 시간 (초)
MAX_LIVES = 5 # 최대 생명력
AUTO_MISS_TIMEOUT = 16.0 # 이 시간(초) 동안 플레이어가 단어를 처리하지 않으면 자동으로 miss 처리

# --- 임시 단어 목록 제거 ---
# ENG_WORDS_PLACEHOLDER = [...] # 이 줄과 아래 KOR_WORDS_PLACEHOLDER 줄을 삭제합니다.
# KOR_WORDS_PLACEHOLDER = [...] 
# eng_word와 kor_word 변수가 이 파일 스코프에서 사용 가능하다고 가정합니다.

# --- 데이터 클래스 정의 (dataclass로 변경) ---
@dataclass
class GameWord:
    word: str
    type: str # "normal", "heal" 등
    speed: int # 단어 낙하 속도 (예: px/sec 또는 추상 단위)
    score: int
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    processed_by: set[str] = field(default_factory=set) # 이 단어를 처리한 user_id 집합

@dataclass
class GameUser:
    sid: str  # 현재 연결의 세션 ID
    user_id: str | None = None # JWT에서 오는 실제 사용자 ID (인증 전에는 None)
    is_host: bool = False
    count: int = 0
    score: int = 0
    life: int = 3
    room_id: str | None = None

@dataclass
class GameRoom: # 제공된 스니펫의 클래스 이름(GameRoom)을 사용 (기존 Room)
    room_id: str
    game_type: str
    host_user: GameUser # GameUser 객체
    user_guest: GameUser | None = None
    word_list: list[GameWord] = field(default_factory=list)
    game_started: bool = False
    game_ended: bool = False
    last_word_shoot_time: float = 0.0
    word_generation_interval: float = 2.0
    difficulty: int = 0
    clients: set[str] = field(default_factory=set)
    shot_word_count: int = 0 # 발사된 단어 수 카운터 (난이도 조절용)

# --- 전역 상태 관리 ---
# rooms 딕셔너리의 타입 어노테이션도 GameRoom을 사용하도록 변경
rooms: dict[str, GameRoom] = {}
game_users: dict[str, GameUser] = {} # Key: sid, Value: GameUser instance

# --- 헬퍼 함수: 상대방 플레이어 가져오기 ---
def _get_opponent(room: GameRoom, current_user: GameUser) -> GameUser | None:
    if not room or not current_user or not room.host_user or not room.user_guest:
        return None
    if current_user.user_id == room.host_user.user_id:
        return room.user_guest
    if current_user.user_id == room.user_guest.user_id:
        return room.host_user
    return None

# --- 헬퍼 함수: 단일 무작위 단어 가져오기 (수정) ---
def get_single_random_word(game_type: str) -> tuple[str, str] | None:
    source_list = []
    # 외부에서 정의된 eng_word, kor_word 사용하도록 변경
    if game_type == "en":
        source_list = eng_word[:] 
    elif game_type == "kr":
        source_list = kor_word[:]
    elif game_type == "complex":
        source_list = eng_word[:] + kor_word[:]
    else:
        print(f"[get_single_random_word] Unknown game_type: {game_type}")
        return None

    if not source_list:
        print(f"[get_single_random_word] Source list is empty for game_type: {game_type}. Make sure eng_word and kor_word are populated.")
        return None

    chosen_word = random.choice(source_list)
    
    word_actual_type = "heal" if random.random() < 0.1 else "normal"
    return chosen_word, word_actual_type

# --- 게임 종료 처리 헬퍼 함수 (수정) ---
def _handle_game_over(room: GameRoom, loser: GameUser):
    if room.game_ended: # 이미 게임 종료 처리가 되었다면 중복 실행 방지
        return

    room.game_started = False
    room.game_ended = True

    winner = None
    # 루저가 호스트면 게스트가 승자, 루저가 게스트면 호스트가 승자
    if room.host_user and room.user_guest: # 두 플레이어가 모두 정상적으로 존재할 때
        if loser.user_id == room.host_user.user_id:
            winner = room.user_guest
        elif loser.user_id == room.user_guest.user_id:
            winner = room.host_user
        # else: 루저가 호스트도 게스트도 아닌 경우는 현재 로직상 발생하기 어려움
            
    elif room.host_user and not room.user_guest and room.host_user.user_id == loser.user_id:
        # 게스트 없이 호스트만 있다가 호스트가 패배한 경우 (예: 혼자 연습모드였다면?)
        print(f"[GameOver] Room {room.room_id}: Host {room.host_user.user_id} lost, no guest was present.")
        # 이 경우 winner는 None으로 유지됨
    elif room.user_guest and not room.host_user and room.user_guest.user_id == loser.user_id:
        # 호스트 없이 게스트만 있다가 게스트가 패배한 경우
        print(f"[GameOver] Room {room.room_id}: Guest {room.user_guest.user_id} lost, no host was present.")
        # 이 경우 winner는 None으로 유지됨
    
    # loser 인자는 항상 GameUser 객체여야 함
    loser_user_id = loser.user_id
    loser_score = loser.score

    winner_user_id = winner.user_id if winner else None
    winner_score = winner.score if winner else None

    game_over_payload = {
        'room_id': room.room_id,
        'message': 'Game Over!',
        'winner_user_id': winner_user_id,
        'loser_user_id': loser_user_id,
        'winner_score': winner_score,
        'loser_score': loser_score,
    }
    socketio.emit('game_over', game_over_payload, to=room.room_id)
    print(f"[GameOver] Room {room.room_id} ended. Winner: {winner_user_id if winner else 'N/A'}, Loser: {loser_user_id}")

    # 각 플레이어에게 개별적인 win/defeat 이벤트 전송
    if winner and winner.sid in game_users: # 승자가 여전히 연결되어 있다면
        # 승자에게 보낼 페이로드 (승자 본인 정보 강조 가능)
        win_payload = {
            'message': 'Congratulations, you won!',
            'your_score': winner.score,
            'opponent_score': loser_score,
            **game_over_payload # 전체 게임 결과도 포함
        }
        emit('win', win_payload, room=winner.sid)
    
    if loser and loser.sid in game_users: # 패자가 여전히 연결되어 있다면
        # 패자에게 보낼 페이로드 (패자 본인 정보 강조 가능)
        defeat_payload = {
            'message': 'You lost. Better luck next time!',
            'your_score': loser.score,
            'opponent_score': winner_score,
            **game_over_payload # 전체 게임 결과도 포함
        }
        emit('defeat', defeat_payload, room=loser.sid)
    
    # 방 정리 로직 (예: 즉시 삭제하지 않고 disconnect 핸들러 등이 처리하도록 둘 수 있음)
    # if room.room_id in rooms:
    #     print(f"[GameOver] Room {room.room_id} marked as ended, will be cleaned up later.")
        # 실제 삭제는 disconnect 시 또는 별도의 정리 로직에서 처리하는 것이 더 안전할 수 있음
        # (예: 모든 플레이어가 방을 나가면 삭제)

# --- 방별 게임 루프 함수 (수정) ---
def game_loop_for_room(room_id: str):
    print(f"[GameLoop] Starting for room {room_id}...")
    room = rooms.get(room_id)

    if not room or not room.host_user or not room.user_guest or not room.game_started:
        print(f"[GameLoop] Pre-loop check failed for room {room_id}. Aborting.")
        if room : room.game_started = False
        return
    
    current_generation_interval = room.word_generation_interval

    while room_id in rooms and room.game_started:
        current_time_in_loop = time.time()
        current_room_state = rooms.get(room_id) # 루프 반복마다 최신 방 상태 가져오기

        if not current_room_state or not current_room_state.game_started:
            print(f"[GameLoop] Room {room_id} no longer exists or game stopped. Exiting loop.")
            break
        
        # 플레이어 연결 상태 확인 (기존 로직 유지)
        host_user = current_room_state.host_user
        guest_user = current_room_state.user_guest
        active_players_sids = {p.sid for p in [host_user, guest_user] if p and p.sid in game_users and p.sid in current_room_state.clients}
        
        if len(active_players_sids) < 2: # 한 명이라도 나갔거나 연결이 유효하지 않으면 게임 중단
            print(f"[GameLoop] A player seems to have disconnected or is invalid in room {room_id}. Stopping game.")
            current_room_state.game_started = False # 게임 중단 플래그
            # 게임 종료 처리는 disconnect 핸들러나 다른 곳에서 할 수 있도록 여기서는 루프만 탈출
            break

        # --- 자동 Miss 처리 및 단어 정리 로직 ---
        words_to_remove_indices = []
        if host_user and guest_user : # 두 플레이어가 모두 있어야 자동 miss 처리 의미 있음
            for i, word_obj in enumerate(current_room_state.word_list):
                # 자동 Miss 처리: 단어가 너무 오래되었고 아직 특정 플레이어가 처리하지 않은 경우
                if current_time_in_loop - word_obj.created_at > AUTO_MISS_TIMEOUT:
                    players_in_room = {host_user.user_id, guest_user.user_id}
                    unprocessed_by_players = players_in_room - word_obj.processed_by
                    
                    for player_user_id_to_penalize in unprocessed_by_players:
                        player_to_penalize = None
                        if host_user.user_id == player_user_id_to_penalize:
                            player_to_penalize = host_user
                        elif guest_user.user_id == player_user_id_to_penalize:
                            player_to_penalize = guest_user
                        
                        if player_to_penalize and player_to_penalize.sid in game_users: # 플레이어가 여전히 유효한 경우
                            player_to_penalize.life -= 1
                            word_obj.processed_by.add(player_user_id_to_penalize) # 자동 miss 처리됨으로 기록
                            print(f"[GameLoop-AutoMiss] User {player_user_id_to_penalize} auto-missed word {word_obj.uuid} in room {room_id}. Life: {player_to_penalize.life}")

                            emit('life_change', {
                                'user_id': player_to_penalize.user_id,
                                'new_life': player_to_penalize.life,
                                'life_delta': -1,
                                'reason': 'auto_miss_timeout',
                                'word_uuid': word_obj.uuid # 어떤 단어가 자동 미스되었는지 정보 추가
                            }, room=player_to_penalize.sid)

                            opponent = _get_opponent(current_room_state, player_to_penalize)
                            if opponent and opponent.sid in game_users:
                                emit('opponents_life_change', {
                                    'opponent_user_id': player_to_penalize.user_id,
                                    'new_life': player_to_penalize.life,
                                    'life_delta': -1,
                                    'reason': 'opponent_auto_miss_timeout',
                                    'word_uuid': word_obj.uuid
                                }, room=opponent.sid)
                            
                            if player_to_penalize.life <= 0 and not current_room_state.game_ended:
                                _handle_game_over(current_room_state, player_to_penalize)
                                break # 게임 종료되면 더 이상 단어 처리 불필요
                    
                    if current_room_state.game_ended: break # 게임 종료 시 외부 루프도 탈출

                # 단어 제거 조건: 모든 활성 플레이어가 단어를 처리했거나, 자동 miss 처리로 인해 모든 플레이어가 처리된 상태가 된 경우
                # 또는 단어가 너무 오래되어서 (AUTO_MISS_TIMEOUT 이상) 더 이상 상호작용할 필요가 없을 때
                # (이 부분은 위에서 처리했으므로, 여기서는 모든 플레이어가 처리했는지 여부만 체크)
                num_active_players = 0
                if host_user and host_user.user_id: num_active_players +=1
                if guest_user and guest_user.user_id: num_active_players +=1
                
                # 실제 게임에 참여 중인 플레이어 (user_id가 있는) 수로 판단
                # 단, 게임 시작 시점에 두 플레이어가 모두 존재했어야 함.
                # current_room_state.clients 에는 sid가 들어있고, game_users[sid].user_id로 실제 참여 유저 확인 가능.
                # 좀 더 정확하게는 게임 시작 시점의 플레이어들을 기준으로 해야 함.
                # 여기서는 간편하게 host_user와 user_guest가 모두 유효한 user_id를 가질 때 2명으로 가정.
                # 만약 한쪽이 나갔다면, 남은 한명이 처리하면 삭제될 수 있도록 해야 할 수도 있음.
                # 현재는 두명 모두 존재하고, 두명 모두 처리해야 삭제되도록 함.
                expected_processors = 0
                if current_room_state.host_user and current_room_state.host_user.user_id: expected_processors +=1
                if current_room_state.user_guest and current_room_state.user_guest.user_id: expected_processors +=1
                
                # 안전하게, 현재 방에 있는 클라이언트 수(최대 2)를 기준으로 할 수도 있으나,
                # 게임 시작 시 확정된 플레이어 기준으로 하는 것이 더 정확. 여기서는 GameRoom의 host_user, user_guest 사용
                if expected_processors > 0 and len(word_obj.processed_by) >= expected_processors:
                    if i not in words_to_remove_indices:
                         words_to_remove_indices.append(i)
                elif current_time_in_loop - word_obj.created_at > AUTO_MISS_TIMEOUT + 2.0 : # 혹시 모든 유저가 처리 안했어도 너무 오래되면 강제 삭제 (2초 여유)
                    if i not in words_to_remove_indices:
                         words_to_remove_indices.append(i)


            if current_room_state.game_ended: break # 게임 종료 시 단어 정리 중단 및 루프 탈출

            # 뒤에서부터 제거해야 인덱스 문제 없음
            for index_to_remove in sorted(words_to_remove_indices, reverse=True):
                removed_word_for_log = current_room_state.word_list[index_to_remove]
                del current_room_state.word_list[index_to_remove]
                print(f"[GameLoop-Cleanup] Word {removed_word_for_log.uuid} removed from room {room_id}.")

        # --- 단어 생성 로직 (기존 로직 일부 수정) ---
        # last_word_shoot_time은 루프 시작시의 시간이 아닌, 실제 단어 발사 시간 기준으로 업데이트 되어야 함.
        # 현재 current_room_state.last_word_shoot_time을 사용하고 있으므로, 이 부분은 그대로 유지.
        if current_time_in_loop - current_room_state.last_word_shoot_time >= current_generation_interval:
            word_data = get_single_random_word(current_room_state.game_type)
            if not word_data:
                print(f"[GameLoop] Could not get word for room {room_id}. Retrying after interval.")
                socketio.sleep(0.1) # 짧게 대기 후 다음 루프에서 재시도
                continue

            word_text, word_type = word_data
            # 난이도에 따른 속도와 점수는 여기서 결정
            speed = 50 + (current_room_state.difficulty * 8) # 난이도 강화 (기존 * 5 에서 * 8 로)
            score = 10 + (current_room_state.difficulty * 2) # 점수는 기존 유지 또는 필요시 조정

            new_word = GameWord(word=word_text, type=word_type, speed=speed, score=score)
            current_room_state.word_list.append(new_word)
            current_room_state.last_word_shoot_time = time.time() # 실제 단어 발사 시간으로 업데이트
            current_room_state.shot_word_count += 1 # 발사된 단어 수 증가 (난이도 조절용)

            print(f"[GameLoop] Room {room_id} shooting word: {asdict(new_word)} (Total shot: {current_room_state.shot_word_count})")
            socketio.emit('shoot_word', asdict(new_word), to=room_id)

            # 난이도 증가 로직 (7단어마다, speed 및 생성 주기 강화)
            if current_room_state.shot_word_count > 0 and current_room_state.shot_word_count % 7 == 0:
                current_room_state.difficulty += 1
                print(f"[GameLoop] Room {room_id} difficulty increased to {current_room_state.difficulty}")
                
                # 단어 생성 간격 업데이트
                base_interval = GameRoom.model_fields['word_generation_interval'].default 
                difficulty_reduction = current_room_state.difficulty * 0.15 # 감소폭 증가
                new_interval = base_interval - difficulty_reduction
                current_generation_interval = max(MIN_WORD_GENERATION_INTERVAL, new_interval)
                
                # 현재 단어 속도 계산 (난이도 반영, GameWord 생성 시 사용되는 값과 일치하도록)
                # 이 값은 difficulty_update 이벤트에 참고용으로만 포함됩니다.
                # 실제 단어의 속도는 GameWord 객체 생성 시 결정됩니다.
                current_speed_for_info = 50 + (current_room_state.difficulty * 8) # Speed 계산식 변경
                
                print(f"[GameLoop] Room {room_id} word generation interval updated to {current_generation_interval:.2f}s, Speed base updated for info to {current_speed_for_info} (Difficulty: {current_room_state.difficulty})")
                
                socketio.emit('difficulty_update', 
                                {'difficulty': current_room_state.difficulty, 
                                 'new_interval': current_generation_interval,
                                 'current_speed_modifier_info': current_speed_for_info # 정보성으로 현재 난이도 기준 속도 전달
                                 }, 
                                to=room_id)
        
        # 루프 주기 (짧게 유지하여 반응성 높임)
        socketio.sleep(0.1) # 0.1초마다 루프 반복 (단어 생성은 current_generation_interval에 따름)

    print(f"[GameLoop] Ended for room {room_id}.")

# --- 인증 확인 데코레이터 ---
def authenticated_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        sid = request.sid
        if not (sid in game_users and game_users[sid].user_id):
            emit('unauthorized', {'message': '인증이 필요합니다. 먼저 인증해주세요.'}, room=sid)
            # disconnect(sid) # 필요에 따라 연결 종료 결정
            print(f"Unauthorized event from {sid} for {f.__name__}. User not authenticated.")
            return # 인증되지 않으면 핸들러 실행 중단
        return f(*args, **kwargs)
    return wrapped

# --- 기본 Socket.IO 이벤트 핸들러 ---
@socketio.on('connect')
def handle_connect():
    sid = request.sid
    print(f"Client connected: {sid}")
    # GameUser 생성 시 sid를 전달, user_id는 아직 None
    game_users[sid] = GameUser(sid=sid)
    emit('connection_confirmed', {'message': 'Successfully connected!', 'sid': sid})

@socketio.on('authenticate')
def handle_authenticate(data):
    sid = request.sid
    if not isinstance(data, dict):
        print(f"Authentication attempt from {sid} with non-dict data: {data}")
        emit('auth_failed', {'message': '요청 형식이 잘못되었습니다. JSON 객체를 보내야 합니다.'}, room=sid)
        disconnect(sid)
        return
        
    token = data.get('token')

    if not token:
        print(f"Authentication attempt from {sid} without token.")
        emit('auth_failed', {'message': '토큰이 필요합니다.'}, room=sid)
        disconnect(sid)
        return

    if sid not in game_users: # Should not happen if connect precedes authenticate
        print(f"Authentication attempt from unknown sid: {sid}. Disconnecting.")
        emit('auth_failed', {'message': '세션을 찾을 수 없습니다. 다시 연결해주세요.'}, room=sid)
        disconnect(sid)
        return

    try:
        decoded_payload = Jwt.decode(token)
        actual_user_id = decoded_payload['id']
        
        user_object = game_users[sid]
        user_object.user_id = actual_user_id # GameUser의 user_id를 실제 식별자로 업데이트
        
        print(f"User {user_object.sid} authenticated as {user_object.user_id}")
        emit('auth_success', {'user_id': user_object.user_id, 'sid': user_object.sid}, room=sid)
    
    except ExpiredSignatureError:
        print(f"Authentication failed for {sid}: Token has expired.")
        emit('auth_failed', {'message': '토큰이 만료되었습니다. 다시 로그인해주세요.'}, room=sid)
        disconnect(sid)
    except InvalidTokenError as e:
        print(f"Authentication failed for {sid}: Invalid token - {str(e)}")
        emit('auth_failed', {'message': f'잘못된 토큰입니다: {str(e)}'}, room=sid)
        disconnect(sid)
    except KeyError: # 'id' field missing in token
        print(f"Authentication failed for {sid}: Token payload is missing 'id'.")
        emit('auth_failed', {'message': '토큰 정보가 올바르지 않습니다.'}, room=sid)
        disconnect(sid)
    except Exception as e:
        print(f"An unexpected error occurred during authentication for {sid}: {str(e)}")
        emit('auth_failed', {'message': '인증 중 오류가 발생했습니다. 다시 시도해주세요.'}, room=sid)
        disconnect(sid)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    print(f"Client disconnected: {sid}")
    user = game_users.pop(sid, None)

    if user and user.room_id and user.room_id in rooms:
        room = rooms[user.room_id]
        room.clients.discard(sid)
        
        # 게임 진행 중이었다면, 게임 중단 처리
        player_left_was_critical = False
        if room.host_user and room.host_user.user_id == user.user_id:
            print(f"Host {user.user_id} (sid: {sid}) disconnected from room {user.room_id}")
            player_left_was_critical = True
            # 호스트가 나가면 방 자체를 닫거나, 게스트에게 승리 처리 후 방 닫기 등
            # 여기서는 간단히 게임 종료 및 방 정리
            if room.game_started:
                room.game_started = False # 게임 루프 중단 신호
                print(f"[Disconnect] Game in room {user.room_id} stopped because host left.")
            # 남아있는 게스트에게 알림
            if room.user_guest and room.user_guest.sid in room.clients:
                emit('opponent_left_game', {'message': 'Host has left the game. Game over.'}, room=room.user_guest.sid)
            # 방 자체를 삭제 (더 이상 진행 불가)
            del rooms[user.room_id]
            print(f"[Disconnect] Room {user.room_id} closed because host left.")

        elif room.user_guest and room.user_guest.user_id == user.user_id:
            print(f"Guest {user.user_id} (sid: {sid}) disconnected from room {user.room_id}")
            player_left_was_critical = True
            room.user_guest = None # 게스트 정보 제거
            if room.game_started:
                room.game_started = False # 게임 루프 중단 신호
                print(f"[Disconnect] Game in room {user.room_id} stopped because guest left.")
            # 호스트에게 알림
            if room.host_user and room.host_user.sid in room.clients:
                 emit('opponent_left_game', {'message': 'Guest has left the game. You can wait for a new player or leave.'}, room=room.host_user.sid)
            # 이 경우, 호스트는 새 게스트를 기다릴 수 있으므로 방은 유지될 수 있음. 단, 게임은 중단.
        
        # 방에 아무도 없으면 (호스트가 나가서 이미 위에서 삭제된 경우 제외하고)
        if not player_left_was_critical and not room.clients and user.room_id in rooms:
            if room.game_started:
                room.game_started = False
            del rooms[user.room_id]
            print(f"[Disconnect] Room {user.room_id} closed because it became empty.")

# --- 새로운 이벤트 핸들러 ---
@socketio.on('create_room')
@authenticated_only
def handle_create_room(data):
    sid = request.sid
    user = game_users[sid] # @authenticated_only 데코레이터가 user 존재를 보장

    # 1. 데이터가 JSON 객체(dict)인지 확인
    if not isinstance(data, dict):
        print(f"[CreateRoom] Failed for user {user.user_id} (sid: {sid}): Invalid data format. Expected JSON object, got {type(data)}.")
        emit('room_failed', {'message': '잘못된 요청 형식입니다. 데이터는 JSON 객체여야 합니다.'}, room=sid)
        return

    # 2. 사용자가 이미 방에 있는지 확인 (기존 로직 유지)
    if user.room_id:
        # 이 메시지는 이미 적절하게 설정되어 있는 것 같습니다.
        emit('room_failed', {'message': '이미 방에 참여중입니다. 먼저 현재 방을 나간 후 시도해주세요.'}, room=sid)
        return

    game_type = data.get('game_type')
    if not game_type:
        emit('room_failed', {'message': '방을 생성하려면 game_type이 필요합니다.'}, room=sid)
        return

    room_id = str(uuid.uuid4()) # 방 ID (키) 생성
    user.is_host = True
    user.room_id = room_id
    
    new_room = GameRoom(
        room_id=room_id,
        game_type=game_type,
        host_user=user 
    )
    new_room.clients.add(sid) 
    rooms[room_id] = new_room

    ws_join_room(room_id, sid=sid) 

    print(f"User {user.user_id} (sid: {sid}) created room {room_id} of type {game_type}")
    emit('room_created', {
        'room_id': room_id,
        'game_type': game_type,
        'host_user_id': user.user_id
    }, room=sid)

@socketio.on('join_room')
@authenticated_only
def handle_join_room(data):
    sid = request.sid
    user = game_users[sid]

    if not isinstance(data, dict):
        print(f"[JoinRoom] Failed for user {user.user_id} (sid: {sid}): Invalid data format. Expected JSON object, got {type(data)}.")
        emit('joined_failed', {'message': '잘못된 요청 형식입니다. 데이터는 JSON 객체여야 합니다.'}, room=sid)
        return

    if user.room_id:
        emit('joined_failed', {'message': '이미 방에 참여중입니다. 먼저 현재 방을 나간 후 시도해주세요.'}, room=sid)
        return

    room_id_to_join = data.get('room_id') # 클라이언트에서는 room_id로 보낼 수 있으나, 서버에서는 'id'로 받고 있었으므로 유지 또는 확인 필요.
                                     # SocketClient.js 에서는 joinRoom(roomId) 이고 서버로 { room_id: roomId } 를 보냄.
                                     # 따라서 data.get('room_id') 가 더 적절해 보임. 우선은 'id' 유지 후 필요시 수정.
    if not room_id_to_join:
        # 위 주석에 따라, 클라이언트가 'room_id'로 보낸다면 여기도 'room_id is required'가 되어야 함.
        emit('joined_failed', {'message': '방 ID(id)가 필요합니다.'}, room=sid) 
        return

    if room_id_to_join not in rooms:
        emit('joined_failed', {'message': f'방 "{room_id_to_join}"을(를) 찾을 수 없습니다.'}, room=sid)
        return

    target_room = rooms[room_id_to_join]

    if target_room.host_user.user_id == user.user_id: # 호스트 재참여
        ws_join_room(room_id_to_join, sid=sid)
        old_sid_host = target_room.host_user.sid
        if old_sid_host != sid: # sid가 변경된 경우
             target_room.clients.discard(old_sid_host)
             target_room.host_user.sid = sid
        target_room.clients.add(sid)
        user.room_id = room_id_to_join
        print(f"Host {user.user_id} (sid: {sid}) re-joined room {room_id_to_join}")
        emit('joined_success', { 
            'room_id': room_id_to_join,
            'game_type': target_room.game_type,
            'is_host': True,
            'host_user_id': target_room.host_user.user_id,
            'guest_user_id': target_room.user_guest.user_id if target_room.user_guest else None,
            'game_started': target_room.game_started # 현재 게임 진행 상태도 알려줌
        }, room=sid)
        return

    if target_room.user_guest is not None: # 게스트가 이미 있는 경우
        if target_room.user_guest.user_id != user.user_id: # 다른 게스트라면 방이 찼음
            emit('joined_failed', {'message': f'방 "{room_id_to_join}"이(가) 가득 찼습니다.'}, room=sid)
            return
        else: # 같은 게스트가 재참여 (sid 변경 가능성)
            ws_join_room(room_id_to_join, sid=sid)
            old_sid_guest = target_room.user_guest.sid
            if old_sid_guest != sid:
                 target_room.clients.discard(old_sid_guest)
                 target_room.user_guest.sid = sid
            target_room.clients.add(sid)
            user.room_id = room_id_to_join
            print(f"Guest {user.user_id} (sid: {sid}) re-joined room {room_id_to_join}")
            emit('joined_success', {
                'room_id': room_id_to_join,
                'game_type': target_room.game_type,
                'is_host': False,
                'host_user_id': target_room.host_user.user_id,
                'guest_user_id': user.user_id,
                'game_started': target_room.game_started
            }, room=sid)
            return
            
    # 새로운 게스트로 방에 참여
    user.room_id = room_id_to_join
    target_room.user_guest = user
    target_room.clients.add(sid)
    ws_join_room(room_id_to_join, sid=sid)

    print(f"User {user.user_id} (sid: {sid}) joined room {room_id_to_join} as guest.")
    # 게스트에게 알림
    emit('joined_success', {
        'room_id': room_id_to_join,
        'game_type': target_room.game_type,
        'is_host': False,
        'host_user_id': target_room.host_user.user_id,
        'guest_user_id': user.user_id,
        'game_started': False # 이제 막 참여했으므로 게임 시작 전
    }, room=sid)

    # 호스트에게 알림
    if target_room.host_user and target_room.host_user.sid in game_users and target_room.host_user.sid in target_room.clients:
        emit('opponent_joined', {
            'room_id': room_id_to_join,
            'guest_user_id': user.user_id
        }, room=target_room.host_user.sid)

    # 두 명의 플레이어가 모두 준비되었고, 게임이 아직 시작되지 않았다면 게임 시작 카운트다운
    if target_room.host_user and target_room.user_guest and not target_room.game_started:
        # print(f"[SetupGame] Room {room_id_to_join} full. Starting game in 5s.")
        # emit('game_starting_soon', {'countdown': 5, 'message': '5초 후에 게임이 시작됩니다!'}, to=room_id_to_join) 
        
        # def start_game_task(r_id):
        #     room_to_start = rooms.get(r_id)
        #     # 5초 후에도 여전히 두 플레이어가 있고 게임이 시작되지 않았는지 다시 한번 확인
        #     if room_to_start and room_to_start.host_user and room_to_start.user_guest and not room_to_start.game_started:
        #         # 실제 게임 루프 시작 전 room의 game_started 상태를 True로 변경
        #         room_to_start.game_started = True 
        #         print(f"[SetupGame] Countdown finished for room {r_id}. Starting game loop.")
        #         socketio.emit('game_started', {'room_id': r_id, 'message': '게임 시작!'}, to=r_id) # 게임 시작 알림
        #         socketio.start_background_task(game_loop_for_room, r_id)
        #     elif room_to_start and room_to_start.game_started:
        #          print(f"[SetupGame] Game for room {r_id} already started. No new loop initiated.")
        #     else:
        #         print(f"[SetupGame] Conditions not met to start game for room {r_id} after delay (e.g., player left).")

        # socketio.start_background_task(start_game_task, room_id_to_join)
        print(f"[SetupGame] Room {room_id_to_join} is now full. Waiting for host to start the game.")

# --- 새로운 hit 이벤트 핸들러 ---
@socketio.on('hit')
@authenticated_only
def handle_hit(data):
    sid = request.sid
    user = game_users.get(sid)

    if not isinstance(data, dict):
        emit('hit_failed', {'message': '잘못된 요청 형식입니다. 데이터는 JSON 객체여야 합니다.'}, room=sid)
        return

    if not user or not user.room_id or user.room_id not in rooms:
        emit('hit_failed', {'message': '오류: 유효한 방에 참여하고 있지 않습니다.'}, room=sid)
        return

    target_room = rooms[user.room_id]

    if not target_room.game_started or target_room.game_ended:
        emit('hit_failed', {'message': '게임이 현재 활성화되어 있지 않습니다.'}, room=sid)
        return

    word_uuid = data.get('uuid')
    if not word_uuid:
        emit('hit_failed', {'message': '단어 UUID가 필요합니다.'}, room=sid)
        return

    hit_word_object = None
    word_index_to_remove = -1

    for i, game_word in enumerate(target_room.word_list):
        if game_word.uuid == word_uuid:
            hit_word_object = game_word
            break
    
    if not hit_word_object:
        # 이미 처리되었거나 존재하지 않는 단어
        print(f"[Hit] User {user.user_id} (sid: {sid}) tried to hit non-existent/already-processed word UUID: {word_uuid} in room {target_room.room_id}")
        emit('hit_failed', {'message': '단어를 찾을 수 없거나 이미 다른 플레이어가 처리했습니다.', 'uuid': word_uuid}, room=sid)
        return

    # 이미 현재 유저가 처리한 단어인지 확인
    if user.user_id in hit_word_object.processed_by:
        print(f"[Hit-Duplicate] User {user.user_id} (sid: {sid}) tried to hit already processed word UUID: {word_uuid} by them in room {target_room.room_id}")
        emit('hit_failed', {'message': '이미 처리한 단어입니다.', 'uuid': word_uuid}, room=sid)
        return

    # 시간 검증 (부정행위 감지)
    current_time = time.time()
    time_diff = current_time - hit_word_object.created_at

    if time_diff > MAX_VALID_HIT_DURATION:
        print(f"[Hit-Cheat] User {user.user_id} (sid: {sid}) hit word {hit_word_object.word} with suspicious time: {time_diff:.2f}s in room {target_room.room_id}")
        user.life -= 1
        # life_change 및 opponents_life_change 이벤트 추가
        emit('life_change', {
            'user_id': user.user_id,
            'new_life': user.life,
            'life_delta': -1,
            'reason': 'suspicious_hit_time'
        }, room=sid)
        
        opponent = _get_opponent(target_room, user)
        if opponent and opponent.sid in game_users:
            emit('opponents_life_change', {
                'opponent_user_id': user.user_id, # 생명력이 변경된 유저 (즉, user)
                'new_life': user.life,
                'life_delta': -1,
                'reason': 'suspicious_hit_time_opponent_view' 
            }, room=opponent.sid)

        if user.life <= 0:
            _handle_game_over(target_room, user)
        return # 부정행위 처리 후 종료

    # 정상적인 Hit 처리
    print(f"[Hit-Success] User {user.user_id} (sid: {sid}) hit word: {hit_word_object.word} in room {target_room.room_id}")
    
    hit_word_object.processed_by.add(user.user_id) # 이 유저가 단어를 처리했음을 표시

    score_delta = hit_word_object.score
    user.score += score_delta
    user.count += 1

    # score_change 이벤트 발생
    emit('score_change', {
        'user_id': user.user_id,
        'new_score': user.score,
        'score_delta': score_delta
    }, room=sid)

    is_heal_item = False
    life_delta = 0
    if hit_word_object.type == "heal":
        if user.life < MAX_LIVES:
            user.life += 1
            life_delta = 1
            is_heal_item = True
    
    if life_delta != 0: # 생명력에 변화가 있었을 경우 (힐 아이템)
        emit('life_change', {
            'user_id': user.user_id,
            'new_life': user.life,
            'life_delta': life_delta,
            'reason': 'heal_item' if life_delta > 0 else 'unknown_life_change' # heal_item 외 다른 이유 추가 가능
        }, room=sid)

        opponent = _get_opponent(target_room, user)
        if opponent and opponent.sid in game_users:
            emit('opponents_life_change', {
                'opponent_user_id': user.user_id,
                'new_life': user.life,
                'life_delta': life_delta,
                'reason': 'opponent_heal_item' if life_delta > 0 else 'opponent_unknown_life_change'
            }, room=opponent.sid)

    # 방 전체에 업데이트 알림
    socketio.emit('word_hit_update', {
        'hitter_user_id': user.user_id,
        'hit_word_uuid': hit_word_object.uuid,
        'word_text': hit_word_object.word, 
        'word_score': hit_word_object.score,
        'new_total_score': user.score,
        'new_life_count': user.life,
        'new_hit_count': user.count,
        'is_heal': is_heal_item
    }, to=target_room.room_id)

# --- 새로운 miss 이벤트 핸들러 ---
@socketio.on('miss')
@authenticated_only
def handle_miss(data):
    sid = request.sid
    user = game_users.get(sid)

    if not isinstance(data, dict):
        emit('miss_failed', {'message': '잘못된 요청 형식입니다. 데이터는 JSON 객체여야 합니다.'}, room=sid)
        return

    if not user or not user.room_id or user.room_id not in rooms:
        emit('miss_failed', {'message': '오류: 유효한 방에 참여하고 있지 않습니다.'}, room=sid)
        return

    target_room = rooms[user.room_id]

    if not target_room.game_started or target_room.game_ended:
        emit('miss_failed', {'message': '게임이 현재 활성화되어 있지 않습니다.'}, room=sid)
        return

    word_uuid = data.get('uuid')
    if not word_uuid:
        emit('miss_failed', {'message': '단어 UUID가 필요합니다.'}, room=sid)
        return

    missed_word_object = None
    word_index_to_remove = -1

    for i, game_word in enumerate(target_room.word_list):
        if game_word.uuid == word_uuid:
            missed_word_object = game_word
            break
    
    if not missed_word_object:
        print(f"[Miss] User {user.user_id} (sid: {sid}) tried to miss non-existent/already-processed word UUID: {word_uuid} in room {target_room.room_id}")
        emit('miss_failed', {'message': '단어를 찾을 수 없거나 이미 다른 플레이어가 처리했습니다.', 'uuid': word_uuid}, room=sid)
        return

    # 이미 현재 유저가 처리한 단어인지 확인 (miss의 경우 이론적으로는 발생하기 어려우나 방어적으로 추가)
    if user.user_id in missed_word_object.processed_by:
        print(f"[Miss-Duplicate] User {user.user_id} (sid: {sid}) tried to miss already processed word UUID: {word_uuid} by them in room {target_room.room_id}")
        emit('miss_failed', {'message': '이미 처리한 단어입니다.', 'uuid': word_uuid}, room=sid) # 또는 다른 적절한 메시지
        return

    print(f"[Miss-Reported] User {user.user_id} (sid: {sid}) reported miss for word: {missed_word_object.word} (UUID: {word_uuid}) in room {target_room.room_id}")
    
    missed_word_object.processed_by.add(user.user_id) # 이 유저가 단어를 처리했음을 표시
    user.life -= 1
    life_delta_on_miss = -1

    # life_change 및 opponents_life_change 이벤트 발생
    emit('life_change', {
        'user_id': user.user_id,
        'new_life': user.life,
        'life_delta': life_delta_on_miss,
        'reason': 'word_missed'
    }, room=sid)

    opponent_on_miss = _get_opponent(target_room, user)
    if opponent_on_miss and opponent_on_miss.sid in game_users:
        emit('opponents_life_change', {
            'opponent_user_id': user.user_id, # 생명력이 변경된 유저 (즉, user)
            'new_life': user.life,
            'life_delta': life_delta_on_miss,
            'reason': 'opponent_word_missed'
        }, room=opponent_on_miss.sid)

    socketio.emit('word_miss_update', {
        'missed_by_user_id': user.user_id, 
        'missed_word_uuid': missed_word_object.uuid,
        'word_text': missed_word_object.word,
        'new_life_count': user.life 
    }, to=target_room.room_id)
    
    if user.life <= 0:
        _handle_game_over(target_room, user) 

@socketio.on('start_game')
@authenticated_only
def handle_start_game(data=None):
    sid = request.sid
    user = game_users.get(sid)

    if not user or not user.room_id or user.room_id not in rooms:
        emit('start_game_failed', {'message': '오류: 유효한 방에 참여하고 있지 않습니다.'}, room=sid)
        return

    room_to_start = rooms[user.room_id]

    if not user.is_host:
        emit('start_game_failed', {'message': '호스트만 게임을 시작할 수 있습니다.'}, room=sid)
        return

    if not room_to_start.user_guest:
        emit('start_game_failed', {'message': '아직 게스트가 참여하지 않았습니다. 두 명의 플레이어가 필요합니다.'}, room=sid)
        return

    if room_to_start.game_started:
        emit('start_game_failed', {'message': '게임이 이미 시작되었습니다.'}, room=sid)
        return
    
    if room_to_start.game_ended:
        emit('start_game_failed', {'message': '이미 종료된 게임방입니다. 새로운 방을 만들어주세요.'}, room=sid)
        return

    print(f"[HostStartGame] Host {user.user_id} is starting game in room {room_to_start.room_id}. Countdown initiated.")
    
    emit('game_starting_soon', {
        'room_id': room_to_start.room_id, 
        'countdown': 5, 
        'message': '호스트가 게임을 시작합니다! 5초 후에 게임이 시작됩니다!'
    }, to=room_to_start.room_id)
    
    def _initiate_game_start_sequence(r_id):
        socketio.sleep(5) # 5초 대기
        current_room = rooms.get(r_id)
        
        if current_room and current_room.host_user and current_room.user_guest and \
           not current_room.game_started and not current_room.game_ended and \
           current_room.host_user.sid in current_room.clients and \
           current_room.user_guest.sid in current_room.clients:
            
            current_room.game_started = True 
            print(f"[HostStartGame] Countdown finished for room {r_id}. Starting game loop.")

            game_started_payload = {
                'room_id': current_room.room_id,
                'message': '게임 시작!',
                'initial_difficulty': current_room.difficulty,
                'initial_speed': 50 + (current_room.difficulty * 8),
                'initial_word_generation_interval': current_room.word_generation_interval,
                'host': asdict(current_room.host_user) if current_room.host_user else None,
                'guest': asdict(current_room.user_guest) if current_room.user_guest else None,
            }
            socketio.emit('game_started', game_started_payload, to=r_id)
            socketio.start_background_task(game_loop_for_room, r_id)
        elif current_room and (current_room.game_started or current_room.game_ended):
             print(f"[HostStartGame] Game for room {r_id} was already started or ended during countdown. No new loop initiated.")
        else:
            print(f"[HostStartGame] Conditions not met to start game for room {r_id} after delay (e.g., player left).")
            if current_room: 
                 emit('start_game_failed', {'message': '게임 시작 중 플레이어가 방을 나갔거나 문제가 발생하여 시작할 수 없습니다.'}, to=r_id)

    socketio.start_background_task(_initiate_game_start_sequence, room_to_start.room_id)


