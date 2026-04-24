from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship
from .database import Base
import enum
from datetime import datetime

class TransactionStatus(str, enum.Enum):
    payment_initiated = "payment_initiated"
    payment_processed = "payment_processed"
    payment_failed = "payment_failed"
    settled = "settled"

class Merchant(Base):
    __tablename__ = "merchants"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(String, primary_key=True, index=True)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    current_status = Column(Enum(TransactionStatus), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    merchant = relationship("Merchant")
    events = relationship("Event", back_populates="transaction", order_by="Event.timestamp")

    __table_args__ = (
        Index('idx_merchant_status', 'merchant_id', 'current_status'),
    )

class Event(Base):
    __tablename__ = "events"
    id = Column(String, primary_key=True, index=True) # event_id from payload ensures idempotency
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False)
    event_type = Column(Enum(TransactionStatus), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    
    transaction = relationship("Transaction", back_populates="events")