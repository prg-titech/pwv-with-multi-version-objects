class Test__1__():
    def a(self, n):
        print(n)
    def b(self, n):
        print(n)
    def c(self, *args):
        print(args[0])
    def d(self, **kwargs):
        print(kwargs['n'])
    def legacy_method(self):
        return

class Test__2__():
    def a(self, *args):
        print(args[0])
    def b(self, **kwargs):
        print(kwargs['n'])
    def c(self, *args):
        print(args[0])
    def d(self, **kwargs):
        print(kwargs['n'])
    def new_method(self):
        return

def main():
    t = Test()
    t.a(10)
    t.b(n=20)
    t.new_method()
    t.a(10)
    t.b(n=20)
    t.legacy_method()
    t.c(30)
    t.d(n=40)
    t.new_method()
    t.c(30)
    t.d(n=40)

if __name__ == "__main__":
    main()
