from pydantic import BaseModel


class CheckUpdate(BaseModel):
    checked: bool
