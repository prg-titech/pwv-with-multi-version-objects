from point import Point

class Location__1__:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def print(self):
        print(f"Location v1: ({self.x}, {self.y})")
    
class Location__2__:
    def __init__(self, p):
        self.x = p.getX()
        self.y = p.getY()

    def print(self):
        print(f"Location v2: ({self.x}, {self.y})")
        