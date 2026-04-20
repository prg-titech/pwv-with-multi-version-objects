def log(message: str) -> None:
    print(f"[BENCH] {message}")


def log_kv(label: str, value: object) -> None:
    log(f"{label}: {value}")


def log_section(title: str) -> None:
    log(title)
