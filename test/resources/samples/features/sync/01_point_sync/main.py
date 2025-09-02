def main():
    p = Point(3.0, 4.0)

    polar_coords = p.get_polar()
    print(f"Polar coords: r={polar_coords[0]:.2f}, theta={polar_coords[1]:.2f}")

    p.r = 0

    cartesian_coords = p.get_cartesian()
    print(f"Cartesian coords: x={cartesian_coords[0]:.2f}, y={cartesian_coords[1]:.2f}")

class Point__1__:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        print(f"V1 Point created at (x={self.x}, y={self.y})")

    def get_cartesian(self) -> tuple:
        return (self.x, self.y)

class Point__2__:
    def __init__(self, r: float, theta: float):
        self.r = r
        self.theta = theta # in radians
        print(f"V2 Point created at (r={self.r}, theta={self.theta})")

    def get_polar(self) -> tuple:
        return (self.r, self.theta)

if __name__ == "__main__":
    main()
