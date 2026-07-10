"""
rest_api.py — REST の考え方を最小ルータで動かす（標準ライブラリのみ）

Web フレームワークを使わず、「(メソッド, パス) をハンドラに振り分ける」だけの
小さなルータを自作する。リソース指向のパス設計・ステータスコード・べき等性が、
実際の挙動としてどう現れるかを、ネットワーク無しで確認する。

ハンドラは (params, body) を受け取り、(status, result) を返す約束にする。
"""


class Router:
    """(メソッド, パスパターン) をハンドラに対応づけ、リクエストを振り分ける。

    パスパターンの `{name}` は可変部分（パスパラメータ）。
    - どのパターンにもパスが一致しない → 404 Not Found
    - パスは一致するがメソッドが無い → 405 Method Not Allowed
    """

    def __init__(self):
        self._routes = []      # (method, [pattern_parts], handler)

    def add(self, method, pattern, handler):
        self._routes.append((method, pattern.strip("/").split("/"), handler))

    def _match(self, pattern_parts, path_parts):
        """パターンとパスが一致すれば params(dict) を、しなければ None を返す。"""
        if len(pattern_parts) != len(path_parts):
            return None
        params = {}
        for pat, actual in zip(pattern_parts, path_parts):
            if pat.startswith("{") and pat.endswith("}"):
                params[pat[1:-1]] = actual        # 可変部分は捕捉
            elif pat != actual:
                return None                       # 固定部分は完全一致が必要
        return params

    def dispatch(self, method, path, body=None):
        path_parts = path.strip("/").split("/")
        path_matched = False
        for m, pattern_parts, handler in self._routes:
            params = self._match(pattern_parts, path_parts)
            if params is None:
                continue
            path_matched = True
            if m == method:
                return handler(params, body)
        # パスは在るがメソッド違い → 405、そもそも無い → 404
        return (405, None) if path_matched else (404, None)


def make_users_api():
    """/users リソースの CRUD を配線した Router を返す。

    メモリ上の dict をストアにして、リソース指向の設計例をそのまま動かす。
    """
    store = {}
    next_id = {"v": 1}

    def list_users(params, body):
        return (200, list(store.values()))

    def create_user(params, body):
        # POST = 作成。毎回新しい id を採番する（べき等ではない）
        uid = next_id["v"]
        next_id["v"] += 1
        user = {"id": uid, **(body or {})}
        store[uid] = user
        return (201, user)

    def get_user(params, body):
        uid = int(params["id"])
        if uid not in store:
            return (404, None)
        return (200, store[uid])

    def put_user(params, body):
        # PUT = 全体置換。無ければ 404。同じ PUT を繰り返しても状態は同じ（べき等）
        uid = int(params["id"])
        if uid not in store:
            return (404, None)
        user = {"id": uid, **(body or {})}
        store[uid] = user
        return (200, user)

    def delete_user(params, body):
        uid = int(params["id"])
        if uid not in store:
            return (404, None)
        del store[uid]
        return (204, None)

    r = Router()
    r.add("GET", "/users", list_users)
    r.add("POST", "/users", create_user)
    r.add("GET", "/users/{id}", get_user)
    r.add("PUT", "/users/{id}", put_user)
    r.add("DELETE", "/users/{id}", delete_user)
    return r


if __name__ == "__main__":
    api = make_users_api()
    print(api.dispatch("POST", "/users", {"name": "alice"}))   # (201, {'id': 1, ...})
    print(api.dispatch("POST", "/users", {"name": "bob"}))     # (201, {'id': 2, ...})
    print(api.dispatch("GET", "/users"))                        # (200, [alice, bob])
    print(api.dispatch("GET", "/users/1"))                      # (200, {'id': 1, ...})
    print(api.dispatch("GET", "/users/999"))                    # (404, None)
    print(api.dispatch("DELETE", "/users/1"))                   # (204, None)
    print(api.dispatch("GET", "/users/1"))                      # (404, None)
    print(api.dispatch("POST", "/users/2"))                     # (405, None) メソッド違い
