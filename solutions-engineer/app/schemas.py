from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from .models import TransactionStatus

# 1. The payload we receive from the partner (kept as event_id to match the JSON file)
class EventPayload(BaseModel):
    event_id: str
    event_type: TransactionStatus
    transaction_id: str
    merchant_id: str
    merchant_name: str
    amount: float
    currency: str
    timestamp: datetime

# 2. The response we send out (changed 'event_id' to 'id' to perfectly match models.Event)
class EventResponse(BaseModel):
    id: str  # <--- THIS WAS CHANGED FROM 'event_id' to 'id'
    event_type: TransactionStatus
    timestamp: datetime

    class Config:
        from_attributes = True

# 3. The transaction response
class TransactionResponse(BaseModel):
    id: str
    merchant_id: str
    amount: float
    currency: str
    current_status: TransactionStatus
    created_at: datetime
    updated_at: datetime
    events: Optional[List[EventResponse]] = []

    class Config:
        from_attributes = True