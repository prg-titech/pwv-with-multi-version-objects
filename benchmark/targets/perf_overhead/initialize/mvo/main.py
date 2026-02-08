import time
TIMES = {LOOP_COUNT}
class MVO__1__:
    def __init__(self):
        self.value = 0

class MVO__2__:
    def __init__(self):
        self.value = 0

def main():
    start_time = time.perf_counter()
    for _ in range(TIMES):
        obj = MVO()
    end_time = time.perf_counter()
    print(end_time - start_time)

main()
