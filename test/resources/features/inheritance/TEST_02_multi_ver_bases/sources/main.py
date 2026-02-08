from student import Student
def main():
    alice = Student("Alice", 67890, "Mathematics")
    bob = Student("Bob", 12345, "Computer Science")
    alice.introduce()
    bob.self_introduce()

if __name__ == "__main__":
    main()
