from pydantic import BaseModel

class Subtask(BaseModel):
    name: str
    start_time: str
    end_time: str

class Subtasks(BaseModel):
    subtasks: list[Subtask]