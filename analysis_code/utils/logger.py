"""
Purpose: Provides stylized and colored console logging.
Input: String log messages and data.
Output: Formatted terminal output.
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
