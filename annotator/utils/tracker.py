from rich.console import Console
from rich.table import Table

class UsageTracker:

    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_requests = 0
        self.reasoning_tokens = 0
        self.total_tokens = 0

    def add_request(self):
        self.total_requests += 1

    def add_reasoning_tokens(self, tokens: int):
        self.reasoning_tokens += tokens
        self.total_tokens += tokens

    def add_input_tokens(self, tokens: int):
        self.input_tokens += tokens
        self.total_tokens += tokens
    
    def add_output_tokens(self, tokens: int):
        self.output_tokens += tokens
        self.total_tokens += tokens

    def get_total_tokens(self):
        return self.total_tokens

    def get_total_requests(self):
        return self.total_requests

    def get_reasoning_tokens(self):
        return self.reasoning_tokens
    
    def print_summary(self):
        table = Table(title="Usage Summary")
        table.add_column("Metric", justify="right")
        table.add_column("Value", justify="right")
        table.add_row("Total requests", str(self.total_requests))
        table.add_row("Total tokens", str(self.total_tokens))
        table.add_row("Reasoning tokens", str(self.reasoning_tokens))
        table.add_row("Input tokens", str(self.input_tokens))
        table.add_row("Output tokens", str(self.output_tokens))
        console = Console()
        console.print(table)