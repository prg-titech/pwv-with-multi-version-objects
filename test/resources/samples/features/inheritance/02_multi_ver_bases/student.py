from member import Member
class Student__1__(Member):
    def __init__(self, name, id, major):
        self.__init__(name, id)
        self.major = major
    def introduce(self):
        print(f"Hi, My id is {self.get_id()}.")

class Student__2__(Member):
    def __init__(self, name, id, major):
        self.__init__(name, id)
        self.major = major
    def self_introduce(self):
        print(f"Hi, My name is {self.get_name()}.")