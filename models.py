# models.py
from typing import List, Optional
from pydantic import BaseModel

class ConversationContext(BaseModel):
    conversation_id: str
    intent: Optional[str] = None
    outlet_id: Optional[int] = None
    candidate_menu_item_ids: List[int] = []
    order_id: Optional[int] = None
    raw_user_message: str
