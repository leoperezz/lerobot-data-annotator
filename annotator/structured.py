from pydantic import BaseModel, Field

class Subtask(BaseModel):
    name: str
    start_time: str
    end_time: str

class Subtasks(BaseModel):
    subtasks: list[Subtask]

class Annotation(BaseModel):
    name: str
    start_time: str
    end_time: str
    start_frame: int
    end_frame: int