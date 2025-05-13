export class GameHelper {
  /**
   * 단어 게임용 단어 목록을 가져옵니다.
   *
   * @async
   * @static
   * @param {string} typeWord - 단어 목록 타입 ("en" 또는 "kr")
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
      // 서버에서 전달한 error 메시지를 그대로 반환
      return { error: data.error || '잘못된 요청입니다.' };
    }

    // 성공 시 result 배열 반환
    return { result: data.result };
  }
}