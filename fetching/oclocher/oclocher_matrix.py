from pydantic import BaseModel


class OClocherMatrix(BaseModel):
    mappings: list[list[int]]
