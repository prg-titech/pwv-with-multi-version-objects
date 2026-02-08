from models.point import Point

def main():
    p = Point(10, 20)
    coords = p.get_coords()
    print(f"Coordinates: {coords}")

if __name__ == "__main__":
    main()
