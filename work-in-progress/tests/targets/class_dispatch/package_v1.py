class Test:
    def display(self) -> str:
        return "display-v1"

    def super_log(self, message: str, author: str) -> str:
        return f"super-v1:{message}:{author}"

    def just_for_test(self) -> str:
        return "test-v1"
