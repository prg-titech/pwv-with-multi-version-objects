from member import Member
class Student__1__(Member__1__):
    def __init__(self, name, id, major):
        super().__init__(name, id)
        self.major = major
    def introduce(self):
        print(f"Hi, My id is {self.get_id()}.")

class Student__2__(Member__2__):
    def __init__(self, name, id, major):
        super().__init__(name, id)
        self.major = major
    def self_introduce(self):
        print(f"Hi, My name is {self.get_name()}.")