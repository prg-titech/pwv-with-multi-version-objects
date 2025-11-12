# A simple logger for the transpiler.

# This flag controls whether debug-level messages are printed.
# It can be enabled from the command line.
DEBUG_MODE = False

def debug_log(message: str):
    """Prints a debug message."""
    if DEBUG_MODE:
        print(f"[LOG]     {message}")

def success_log(message: str):
    """Prints a success message."""
    if DEBUG_MODE:
        print(f"[SUCCESS] {message}")

def error_log(message: str):
    """Prints an error message."""
    print(f"[ERROR]   {message}")

def warning_log(message: str):
    """Prints a warning message."""
    print(f"[WARNING] {message}")

def no_header_log(message: str):
    """Prints a message without a header."""
    if DEBUG_MODE:
        print(message)

def log(message: str):
    """Prints a general message that should always be visible."""
    print(message)