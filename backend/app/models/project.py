from sqlalchemy import Column, Integer, String, Text, DateTime, func, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
from datetime import datetime


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)
    
    # History settings
    history_enabled = Column(Boolean, default=True, nullable=False)
    history_limit = Column(Integer, default=5, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    env_vars = relationship("EnvVar", back_populates="project", cascade="all, delete-orphan")
    env_exports = relationship("EnvExport", back_populates="project", cascade="all, delete-orphan")
    env_imports = relationship("EnvImport", back_populates="project", cascade="all, delete-orphan")
    
    # Project links (as source)
    source_links = relationship(
        "ProjectLink",
        foreign_keys="ProjectLink.source_project_id",
        back_populates="source_project",
        cascade="all, delete-orphan"
    )
    
    # Project links (as target)
    target_links = relationship(
        "ProjectLink",
        foreign_keys="ProjectLink.target_project_id",
        back_populates="target_project",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        } 