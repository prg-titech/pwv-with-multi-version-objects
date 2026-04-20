class Test__1__:
    def display(self):
        print("This is a test class of version 1.")
    def super_log(self, message: str, author: str):
        print(f"Super log: {message} (Author: {author})")
    def just_for_test(self):
        print("This method is just for testing purposes from version 1.")

class Test__2__:
    def display(self):
        print("This is a test class of version 2.")
    def log(self):
        print("Logging from Test__2__")
    def super_log(self, message: str):
        print(f"Super log: {message}")
    def just_for_test(self):
        print("This method is just for testing purposes from version 2.")
        