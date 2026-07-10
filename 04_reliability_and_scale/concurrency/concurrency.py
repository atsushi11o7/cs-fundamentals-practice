"""
concurrency.py — 並行処理の競合とロック（標準ライブラリのみ）

複数スレッドが同じデータを触ると壊れる「競合（レースコンディション）」を再現し、
ロックで防ぐ方法を示す。threading は標準ライブラリ。
"""
import threading


class UnsafeCounter:
    """ロックなし。複数スレッドから同時に増やすと値が壊れることがある。"""

    def __init__(self):
        self.value = 0

    def increment(self, times):
        for _ in range(times):
            # この "読んで→足して→書く" の3手順の途中で
            # 別スレッドが割り込むと、更新が失われる（競合）
            current = self.value
            self.value = current + 1


class SafeCounter:
    """ロックあり。increment 全体をロックで囲み、競合を防ぐ。"""

    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment(self, times):
        for _ in range(times):
            with self.lock:              # 同時に1スレッドしか入れない
                current = self.value
                self.value = current + 1


def run_with_threads(counter, num_threads, times_each):
    """counter を複数スレッドから同時に増やし、最終値を返す。"""
    threads = [
        threading.Thread(target=counter.increment, args=(times_each,))
        for _ in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return counter.value


if __name__ == "__main__":
    # 期待値は 4スレッド × 50000 = 200000
    expected = 4 * 50000

    safe = run_with_threads(SafeCounter(), 4, 50000)
    print("safe:", safe, "(expected", expected, ")")   # 常に一致

    # unsafe は環境次第で expected より小さくなることがある（競合で更新が失われる）
    unsafe = run_with_threads(UnsafeCounter(), 4, 50000)
    print("unsafe:", unsafe, "(expected", expected, ")")
