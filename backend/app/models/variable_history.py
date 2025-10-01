from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class VariableHistory(Base):
    __tablename__ = "variable_history"
    
    id = Column(Integer, primary_key=True, index=True)
    env_var_id = Column(Integer, ForeignKey("env_vars.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    
    # Variable state at time of change
    version_number = Column(Integer, nullable=False)  # 1, 2, 3, etc.
    variable_name = Column(String(255), nullable=False)
    raw_value = Column(Text)
    linked_to = Column(String(255))
    concat_parts = Column(Text)
    description = Column(Text)
    is_encrypted = Column(Boolean, default=False)
    
    # Change metadata
    change_type = Column(String(50), nullable=False)  # 'created', 'updated', 'deleted'
    change_reason = Column(String(255))  # 'manual_edit', 'import', 'api_update', etc.
    changed_by = Column(String(255))  # User identifier (future use)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    env_var = relationship("EnvVar", back_populates="history")
    project = relationship("Project")
    
    def __repr__(self):
        return f"<VariableHistory(id={self.id}, env_var_id={self.env_var_id}, version={self.version_number}, change_type={self.change_type})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "env_var_id": self.env_var_id,
            "project_id": self.project_id,
            "version_number": self.version_number,
            "variable_name": self.variable_name,
            "raw_value": self.raw_value,
            "linked_to": self.linked_to,
            "concat_parts": self.concat_parts,
            "description": self.description,
            "is_encrypted": self.is_encrypted,
            "change_type": self.change_type,
            "change_reason": self.change_reason,
            "changed_by": self.changed_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        } 