from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
from datetime import datetime


class EnvVar(Base):
    __tablename__ = "env_vars"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    raw_value = Column(Text)  # Nullable, for direct values
    linked_to = Column(String(255))  # Nullable, format: "PROJECT:VAR"
    concat_parts = Column(Text)  # Nullable, format: "PROJECT:VAR|PROJECT:VAR"
    description = Column(Text)
    is_encrypted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="env_vars")
    history = relationship("VariableHistory", back_populates="env_var", cascade="all, delete-orphan", order_by="VariableHistory.version_number.desc()")
    
    def __repr__(self):
        return f"<EnvVar(id={self.id}, name='{self.name}', project_id={self.project_id})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "raw_value": self.raw_value,
            "linked_to": self.linked_to,
            "concat_parts": self.concat_parts,
            "description": self.description,
            "is_encrypted": self.is_encrypted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def value_type(self) -> str:
        """Get the type of value this variable holds"""
        if self.raw_value is not None:
            return "raw"
        elif self.linked_to is not None:
            return "linked"
        elif self.concat_parts is not None:
            return "concatenated"
        else:
            return "empty"
    
    def get_value_representation(self) -> str:
        """Get a string representation of the value for display"""
        if self.raw_value is not None:
            return f"RAW: {self.raw_value[:50]}{'...' if len(self.raw_value) > 50 else ''}"
        elif self.linked_to is not None:
            return f"LINKED: {self.linked_to}"
        elif self.concat_parts is not None:
            return f"CONCAT: {self.concat_parts}"
        else:
            return "EMPTY" 