from pydantic import BaseModel
from typing import Optional

class AccountUpdate(BaseModel):
    display_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
