class AuthHelper{
        /**
         * 아이디 중복 체크
         * @async
         * @static
         * @param {string} id - 사용자 아이디
         * @returns {Promise<
         *   | { result: { is_duplicated : boolean } }

         * >} is_duplicated가 참이면 중복 아니면 아님
         */
        static async check_duplicate(id){
            const response = await fetch(`/api/auth/check_duplicate/${id}`, {
                method: "GET",

            });

            const data = await response.json();
            return {result : data}

        }
        /**
         * 아이디와 비밀번호로 로그인합니다.
         * @async
         * @static
         * @param {string} id - 사용자 아이디
         * @param {string} password - 사용자 비밀번호
         * @returns {Promise<
         *   | { result: { access_token: string, type: string } }
         *   | { error: string }
         * >} 로그인 성공 시 result 반환, 실패 시 서버에서 받은 error 메시지 반환
         * - 성공: `{ result: { access_token: string, type: string } }`
         * - 실패: `{ error: string }` (서버 응답의 message 필드 사용)
         */
        static async sign_in(id, password) {
            const response = await fetch("/api/auth/sign_in", {
                method: "POST",
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id, password })
            });

            const data = await response.json();

            console.log(data);
            if (!response.ok) {
                return { error: data.error };
            }

            localStorage.setItem("_auth_token", data.result.access_token)
            return { result: data.result };
        }
        /**
         * 아이디, 비밀번호, 닉네임으로 회원가입을 요청합니다.
         *
         * @async
         * @static
         * @param {string} id - 생성할 사용자 아이디
         * @param {string} password - 생성할 사용자 비밀번호
         * @param {string} nickname - 생성할 사용자 닉네임
         * @returns {Promise<
         *   | { data: { id: string; nickname: string } }
         *   | { error: string }
         * >}
         * - 성공: `{ data: { id: string; nickname: string } }`
         * - 실패: `{ error: string }` (서버가 반환한 error 메시지)
         *
         */
        static async  sign_up(id, password, nickname) {
          const response = await fetch("/api/auth/sign_up", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id, password, nickname }),
          });

          const data = await response.json();

          if (!response.ok) {
            // 서버에서 전달한 error 메시지를 그대로 반환
            return { error: data.error };
          }

          // 성공 시 가입된 id, nickname 반환
          return { data: { id: data.data.id, nickname: data.data.nickname } };
        }

}