"""
Purpose: Provide a small rich-based logger for consistent console output.
Input: Message strings passed into the logger methods.
Output: Styled terminal logs shown during pipeline execution.
"""
from rich.console import Console
from rich.text import Text


class Logger:
    def __init__(self):
        self.console = Console()

    def info(self, msg: str) -> None:
        self.console.print(Text(msg, style="blue"))

    def success(self, msg: str) -> None:
        self.console.print(Text(msg, style="green"))

    def fail(self, msg: str) -> None:
        self.console.print(Text(msg, style="red"))

    def warning(self, msg: str) -> None:
        self.console.print(Text(msg, style="yellow"))

    def section(self, title: str) -> None:
        self.console.print()
        self.console.print(Text(f"=== {title} ===", style="bold cyan"))
        self.console.print()


logger = Logger()
