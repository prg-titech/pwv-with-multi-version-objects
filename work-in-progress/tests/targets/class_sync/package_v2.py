class Point:
    def __init__(self, r: float, theta: float):
        self.r = r
        self.theta = theta

    def get_polar(self) -> tuple[float, float]:
        return (self.r, self.theta)
