from typing import TypedDict, Optional
from pydantic import Field
from pymongo.asynchronous.collection import AsyncCollection
from ..db import database


class FileSchema(TypedDict):
    name: str = Field(..., description="Name of the file")
    status: str = Field(..., description="Status of the file")
    result: Optional[str] = Field(None, description="The result form AI")


COLLECTION_NAME = "files"
files_collection: AsyncCollection = database[COLLECTION_NAME]
