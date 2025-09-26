class A__1__:
    x: int = 1

class A__2__:
    x: int = 1


def main():
    a1 = A()
    a2 = A()
    print(a1.x)
    print(a2.x)
    A.x = 2
    print(a1.x)
    print(a2.x)

if __name__ == "__main__":
    main()
