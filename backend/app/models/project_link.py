from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
from datetime import datetime


class ProjectLink(Base):
    __tablename__ = "project_links"
    
    id = Column(Integer, primary_key=True, index=True)
    source_project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    target_project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    link_type = Column(String(50), default="dependency")  # dependency, shared, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    source_project = relationship(
        "Project",
        foreign_keys=[source_project_id],
        back_populates="source_links"
    )
    target_project = relationship(
        "Project",
        foreign_keys=[target_project_id],
        back_populates="target_links"
    )
    
    def __repr__(self):
        return f"<ProjectLink(id={self.id}, source={self.source_project_id}, target={self.target_project_id}, type='{self.link_type}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "source_project_id": self.source_project_id,
            "target_project_id": self.target_project_id,
            "link_type": self.link_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        } 