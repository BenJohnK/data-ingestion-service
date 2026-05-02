from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, CheckConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(150), unique=True, nullable=False)

    first_name = Column(String(150), default="")
    last_name = Column(String(150), default="")

    email = Column(String(254), nullable=False)

    user_type = Column(Integer, default=1)

    phone_number = Column(String(32), default="")

    # Self-referencing FK
    supervisor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

    is_active = Column(Boolean, default=True)

    created_on = Column(TIMESTAMP, server_default=func.now())
    modified_on = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Constraint from schema
    __table_args__ = (
        CheckConstraint("user_type IN (1, 2, 3, 7)", name="check_user_type"),
    )

    # Self-referencing relationship
    supervisor = relationship("User", remote_side=[id], backref="subordinates")