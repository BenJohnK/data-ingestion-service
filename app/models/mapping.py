from sqlalchemy import Column, Integer, Boolean, ForeignKey, TIMESTAMP, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class PermanentJourneyPlan(Base):
    __tablename__ = "permanent_journey_plans"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)

    date = Column(Date)

    is_active = Column(Boolean, default=True)

    created_on = Column(TIMESTAMP, server_default=func.now())
    modified_on = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Unique constraint from schema
    __table_args__ = (
        UniqueConstraint("user_id", "store_id", "date", name="unique_user_store_date"),
    )

    # Relationships (optional but useful)
    user = relationship("User")
    store = relationship("Store")