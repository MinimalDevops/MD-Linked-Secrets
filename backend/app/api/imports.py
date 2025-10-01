from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import logging

from ..core.database import get_db
from ..services.env_import_service import EnvImportService
from ..models import EnvImport, Project
from ..schemas.import_schemas import (
    EnvFileImportRequest, EnvImportPreview, EnvImportResult, EnvImportRecord
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Imports"])


@router.post("/preview", response_model=EnvImportPreview)
async def preview_env_import(
    request: EnvFileImportRequest,
    db: AsyncSession = Depends(get_db)
):
    """Preview what will be imported from .env content without actually importing"""
    try:
        service = EnvImportService(db)
        preview = await service.preview_import(request)
        return preview
        
    except Exception as e:
        logger.error(f"Error previewing import: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/import", response_model=EnvImportResult)
async def import_env_variables(
    request: EnvFileImportRequest,
    db: AsyncSession = Depends(get_db)
):
    """Import variables from .env content into a project"""
    try:
        service = EnvImportService(db)
        result = await service.import_variables(request)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing variables: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/upload", response_model=EnvImportResult)
async def upload_env_file(
    project_id: int = Form(...),
    overwrite_existing: bool = Form(False),
    strip_prefix: Optional[str] = Form(None),
    strip_suffix: Optional[str] = Form(None),
    add_prefix: Optional[str] = Form(None),
    add_suffix: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload and import a .env file"""
    try:
        # Validate file type
        if not file.filename or not (file.filename.endswith('.env') or file.filename == '.env'):
            raise HTTPException(status_code=400, detail="File must be a .env file")
        
        # Read file content
        content = await file.read()
        env_content = content.decode('utf-8')
        
        # Create import request
        request = EnvFileImportRequest(
            project_id=project_id,
            env_content=env_content,
            overwrite_existing=overwrite_existing,
            strip_prefix=strip_prefix,
            strip_suffix=strip_suffix,
            add_prefix=add_prefix,
            add_suffix=add_suffix,
            description=description
        )
        
        # Import variables
        service = EnvImportService(db)
        result = await service.import_variables(request)
        
        # Update import source to indicate file upload
        if result.import_id:
            import_result = await db.execute(
                select(EnvImport).where(EnvImport.id == result.import_id)
            )
            import_record = import_result.scalar_one_or_none()
            if import_record:
                import_record.import_source = 'file_upload'
                import_record.import_description = f"Uploaded file: {file.filename}"
                await db.commit()
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading .env file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[EnvImportRecord])
async def list_imports(
    project_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List import history with optional project filtering"""
    try:
        query = select(EnvImport)
        if project_id:
            query = query.where(EnvImport.project_id == project_id)
        
        query = query.offset(skip).limit(limit).order_by(EnvImport.imported_at.desc())
        
        result = await db.execute(query)
        imports = result.scalars().all()
        
        return [EnvImportRecord.model_validate(imp.to_dict()) for imp in imports]
        
    except Exception as e:
        logger.error(f"Error listing imports: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{import_id}", response_model=EnvImportRecord)
async def get_import(
    import_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific import"""
    try:
        result = await db.execute(
            select(EnvImport).where(EnvImport.id == import_id)
        )
        import_record = result.scalar_one_or_none()
        
        if not import_record:
            raise HTTPException(status_code=404, detail="Import not found")
        
        return EnvImportRecord.model_validate(import_record.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting import: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{import_id}")
async def delete_import_record(
    import_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an import record (does not affect imported variables)"""
    try:
        result = await db.execute(
            select(EnvImport).where(EnvImport.id == import_id)
        )
        import_record = result.scalar_one_or_none()
        
        if not import_record:
            raise HTTPException(status_code=404, detail="Import not found")
        
        await db.delete(import_record)
        await db.commit()
        
        return {"message": "Import record deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting import record: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 