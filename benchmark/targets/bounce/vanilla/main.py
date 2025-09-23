# This code is based on the SOM class library.
#
# Copyright (c) 2001-2021 see AUTHORS.md file
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the 'Software'), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import time

TIMES = {LOOP_COUNT}

class Num:
    def __init__(self, value):
        self.value = value
    def plus(self, other):
        return Num(self.value + other.value)
    def minus(self, other):
        return Num(self.value - other.value)
    def equal(self, other):
        return self.value == other.value
    def less_than_equal(self, other):
        return self.value <= other.value
    def greater_than_equal(self, other):
        return self.value >= other.value
    def greater_than(self, other):
        return self.value > other.value
    def less_than(self, other):
        return self.value < other.value
    def abs(self):
        return Num(abs(self.value))
    def modulo(self, other):
        return Num(self.value % other.value)

class Random:
    def __init__(self):
        self._seed = 74755

    def next(self):
        self._seed = ((self._seed * 1309) + 13849) & 65535
        return self._seed
    
class Ball:
    def __init__(self, random):
        self._x = Num(random.next() % 500)
        self._y = Num(random.next() % 500)
        self._x_vel = Num((random.next() % 300) - 150)
        self._y_vel = Num((random.next() % 300) - 150)

    def bounce(self):
        x_limit = Num(500)
        y_limit = Num(500)
        bounced = False

        # 算術演算をNumのメソッド呼び出しに変換
        self._x = self._x.plus(self._x_vel)
        self._y = self._y.plus(self._y_vel)

        if self._x.greater_than(x_limit):
            self._x = x_limit
            self._x_vel = self._x_vel.abs().minus(Num(0))
            bounced = True

        if self._x.less_than(Num(0)):
            self._x = Num(0)
            self._x_vel = self._x_vel.abs()
            bounced = True

        if self._y.greater_than(y_limit):
            self._y = y_limit
            self._y_vel = self._y_vel.abs().minus(Num(0))
            bounced = True

        if self._y.less_than(Num(0)):
            self._y = Num(0)
            self._y_vel = self._y_vel.abs()
            bounced = True

        return bounced

def main():
    start_time = time.perf_counter()

    for _ in range(TIMES):
        bounces = 0
        random_generator = Random()
        ball_count = 100
        balls = [None] * ball_count

        for i in range(ball_count):
            balls[i] = Ball(random_generator)

        for _ in range(50):
            for ball in balls:
                if ball.bounce():
                    bounces += 1
    
    end_time = time.perf_counter()
    avg_time = (end_time - start_time) / TIMES

    print(avg_time)

main()