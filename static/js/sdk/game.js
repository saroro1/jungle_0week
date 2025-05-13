export class GameHelper {
  /**
   * 단어 게임용 단어 목록을 가져옵니다.
   *
   * @async
   * @static
   * @param {string} typeWord - 단어 목록 타입 ("en", "kr" 또는 "complex")
   * @param {number} count - 가져올 단어 개수
   * @returns {Promise<
   *   | { result: Array<{ word: string; type: 'heal' | 'normal' }> }
   *   | { error: string }
   * >}
   * - 성공: `{ result: [{ word: string; type: 'heal'|'normal' }, ...] }`
   *   - `type === 'heal'`인 단어는 배열의 첫 번째 요소
   *   - 나머지는 `type === 'normal'`
   * - 실패: `{ error: string }` (서버가 반환한 error 메시지)
   *
   * @example
   * GameHelper.getWords('en', 5)
   *   .then(res => {
   *     if (res.result) {
   *       console.log('단어 목록:', res.result);
   *     } else {
   *       console.error('오류 발생:', res.error);
   *     }
   *   });
   */
  static async getWords(typeWord, count) {
    const response = await fetch(`/api/game/word/${encodeURIComponent(typeWord)}/${count}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    const data = await response.json();

    if (!response.ok) {
      return { error: data.error || '잘못된 요청입니다.' };
    }
    return { result: data.result ?? [] };
  }

  /**
   * 지정된 타입의 게임 랭킹 목록을 가져옵니다.
   *
   * @async
   * @static
   * @param {string} typeWord - 랭킹 타입 ("en", "kr" 또는 "complex")
   * @param {number} page - 가져올 페이지 번호 (1부터 시작)
   * @param {number} count - 페이지 당 항목 수
   * @returns {Promise<
   *   | { result: Array<{ nickname: string; ranking: number }> }
   *   | { error: string }
   * >}
   * - 성공: `{ result: [{ nickname: string, ranking: number }, ...] }`
   * - 실패: `{ error: string }` (서버가 반환한 error 메시지)
   */
  static async getLeaderboard(typeWord, page, count) {
    const response = await fetch(`/api/game/ranking/${encodeURIComponent(typeWord)}/${page}/${count}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    const data = await response.json();

    if (!response.ok) {
      return { error: data.error || '랭킹 정보를 가져오는데 실패했습니다.' };
    }
    return { result: data.result };
  }

  /**
   * 현재 사용자의 최고 점수를 서버에 기록합니다.
   *
   * @async
   * @static
   * @param {string} scoreType - 점수 타입 ("en", "kr" 또는 "complex")
   * @param {number} score - 기록할 점수
   * @returns {Promise<
   *   | { result: string }
   *   | { error: string }
   * >}
   * - 성공: `{ result: "하이스코어가 업데이트되었습니다." }` 또는 `{"result": "최고 기록이 아니거나 사용자 정보를 찾을 수 없습니다."}`
   * - 실패: `{ error: string }` (서버가 반환한 error 메시지)
   */
  static async setHighscore(scoreType, score) {
    const response = await fetch('/api/game/highscore', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ score_type: scoreType, score }),
    });

    const data = await response.json();

    if (!response.ok) {
      return { error: data.error || '하이스코어 기록에 실패했습니다.' };
    }
    return { result: data.result }; // 성공 시 서버 메시지 그대로 전달
  }

  /**
   * 현재 사용자의 게임 랭킹 정보를 가져옵니다.
   *
   * @async
   * @static
   * @returns {Promise<
   *   | { result: { kr: number; en: number; complex: number } }
   *   | { error: string }
   * >}
   * - 성공: `{ result: { kr: number, en: number, complex: number } }` (각 언어별 랭킹)
   * - 실패: `{ error: string }` (서버가 반환한 error 메시지)
   */
  static async getMyRank() {
    const response = await fetch('/api/game/my_rank', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    const data = await response.json();

    if (!response.ok) {
      return { error: data.error || '내 랭킹 정보를 가져오는데 실패했습니다.' };
    }
    return { result: data.result };
  }
}