from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class EnvImport(Base):
    __tablename__ = "env_imports"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    import_source = Column(String(50), nullable=False)  # 'file_upload', 'cli', 'api'
    import_description = Column(Text)  # Optional description of import
    variables_imported = Column(Integer, default=0)
    variables_skipped = Column(Integer, default=0)
    variables_overwritten = Column(Integer, default=0)
    import_hash = Column(String(64))  # Hash of imported content for deduplication
    imported_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="env_imports")
    
    def __repr__(self):
        return f"<EnvImport(id={self.id}, project_id={self.project_id}, variables_imported={self.variables_imported})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "import_source": self.import_source,
            "import_description": self.import_description,
            "variables_imported": self.variables_imported,
            "variables_skipped": self.variables_skipped,
            "variables_overwritten": self.variables_overwritten,
            "import_hash": self.import_hash,
            "imported_at": self.imported_at.isoformat() if self.imported_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        } 