from sqlalchemy import Column, Integer, String, DateTime, JSON, func
from sqlalchemy.sql import func
from ..core.database import Base
from datetime import datetime


class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(50), nullable=False, index=True)
    record_id = Column(Integer, nullable=False, index=True)
    action = Column(String(20), nullable=False)  # INSERT, UPDATE, DELETE
    old_values = Column(JSON)  # Previous values (for UPDATE/DELETE)
    new_values = Column(JSON)  # New values (for INSERT/UPDATE)
    changed_by = Column(String(255))  # Could be user or system
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, table='{self.table_name}', action='{self.action}', record_id={self.record_id})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "table_name": self.table_name,
            "record_id": self.record_id,
            "action": self.action,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "changed_by": self.changed_by,
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
        }
    
    @classmethod
    def create_log_entry(cls, table_name: str, record_id: int, action: str, 
                        old_values: dict = None, new_values: dict = None, 
                        changed_by: str = "system"):
        """Create a new audit log entry"""
        return cls(
            table_name=table_name,
            record_id=record_id,
            action=action,
            old_values=old_values,
            new_values=new_values,
            changed_by=changed_by
        ) 