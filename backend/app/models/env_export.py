from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
from datetime import datetime
import hashlib
import json


class EnvExport(Base):
    __tablename__ = "env_exports"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    export_path = Column(Text, nullable=False)
    exported_at = Column(DateTime(timezone=True), server_default=func.now())
    with_prefix = Column(Boolean, default=False)
    with_suffix = Column(Boolean, default=False)
    prefix_value = Column(String(50))
    suffix_value = Column(String(50))
    resolved_values = Column(JSON, nullable=False)  # Store resolved key-value pairs at export time
    export_hash = Column(String(64))  # Hash of resolved values for quick comparison
    
    # Git tracking fields
    git_repo_path = Column(Text)  # Path to git repository root
    git_branch = Column(String(255))  # Git branch name
    git_commit_hash = Column(String(40))  # Git commit hash
    git_remote_url = Column(Text)  # Git remote URL
    is_git_repo = Column(Boolean, default=False)  # Whether export was in a git repo
    
    # Relationships
    project = relationship("Project", back_populates="env_exports")
    
    def __repr__(self):
        return f"<EnvExport(id={self.id}, project_id={self.project_id}, path='{self.export_path}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "export_path": self.export_path,
            "exported_at": self.exported_at.isoformat() if self.exported_at else None,
            "with_prefix": self.with_prefix,
            "with_suffix": self.with_suffix,
            "prefix_value": self.prefix_value,
            "suffix_value": self.suffix_value,
            "resolved_values": self.resolved_values,
            "export_hash": self.export_hash,
            "git_repo_path": self.git_repo_path,
            "git_branch": self.git_branch,
            "git_commit_hash": self.git_commit_hash,
            "git_remote_url": self.git_remote_url,
            "is_git_repo": self.is_git_repo,
        }
    
    def calculate_hash(self) -> str:
        """Calculate hash of resolved values for comparison"""
        if not self.resolved_values:
            return ""
        
        # Sort the values to ensure consistent hashing
        sorted_values = dict(sorted(self.resolved_values.items()))
        value_string = json.dumps(sorted_values, sort_keys=True)
        return hashlib.sha256(value_string.encode()).hexdigest()
    
    def update_hash(self):
        """Update the export hash"""
        self.export_hash = self.calculate_hash()
    
    def is_outdated(self, current_values: dict) -> bool:
        """Check if this export is outdated compared to current values"""
        if not current_values:
            return False
        
        # Calculate hash of current values
        sorted_current = dict(sorted(current_values.items()))
        current_string = json.dumps(sorted_current, sort_keys=True)
        current_hash = hashlib.sha256(current_string.encode()).hexdigest()
        
        return current_hash != self.export_hash 