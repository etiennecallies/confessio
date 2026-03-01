from pydantic import BaseModel


class LocationChurchMapping(BaseModel):
    location_id: int
    church_id: int | None


class OClocherMatrix(BaseModel):
    mappings: list[LocationChurchMapping]
