def main():
    Dog("Pochi").speak()
    cat = Cat("Tama")
    cat.speak()
    cat.introduce()

class Dog:
    def __init__(self, name):
        self.name = name

    def speak(self):
        print("Woof!")

class Cat__1__:
    def __init__(self, name):
        self.name = name

    def speak(self):
        print("Meow!")

class Cat__2__:
    def __init__(self, name):
        self.name = name

    def introduce(self):
        print(f"Hello, I am a cat named {self.name}.")

if __name__ == "__main__":
    main()
