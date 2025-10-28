from member import Member
class Student__1__(Member):
    def __init__(self, name, id):
        super().__init__(name, id)

class Student__2__(Member):
    def __init__(self, name, id):
        super().__init__(name, id)
    def get_id(self, rebundant_param):
        return self.id