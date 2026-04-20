class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def get_cartesian(self) -> tuple[float, float]:
        return (self.x, self.y)
