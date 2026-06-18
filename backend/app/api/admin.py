from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import json
import os
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Settings

router = APIRouter(tags=["admin"])

# Helper function to check if user is admin
def require_admin(current_user: User = Depends(get_current_user)):
    """Check if current user is admin"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

class GoogleDriveSettings(BaseModel):
    folder_id: str
    service_account_json: str

class SettingsResponse(BaseModel):
    google_drive_configured: bool
    google_drive_folder_id: Optional[str] = None

@router.get("/settings", response_model=SettingsResponse)
def get_settings_status(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Получить статус настроек Google Drive"""
    
    # Проверяем наличие настроек Google Drive
    folder_id_setting = db.query(Settings).filter(Settings.key == "google_drive_folder_id").first()
    credentials_setting = db.query(Settings).filter(Settings.key == "google_service_account_json").first()
    
    configured = bool(folder_id_setting and credentials_setting)
    folder_id = folder_id_setting.value if folder_id_setting else None
    
    return SettingsResponse(
        google_drive_configured=configured,
        google_drive_folder_id=folder_id
    )

@router.post("/settings/google-drive")
async def configure_google_drive(
    folder_id: str,
    service_account_file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Настроить Google Drive через загрузку service-account.json"""
    
    # Проверяем что файл JSON
    if not service_account_file.filename.endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service account file must be a JSON file"
        )
    
    # Читаем и валидируем JSON
    try:
        content = await service_account_file.read()
        service_account_data = json.loads(content.decode('utf-8'))
        
        # Проверяем обязательные поля
        required_fields = ["type", "project_id", "private_key", "client_email"]
        for field in required_fields:
            if field not in service_account_data:
                raise ValueError(f"Missing required field: {field}")
        
        if service_account_data.get("type") != "service_account":
            raise ValueError("Invalid service account file")
            
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON file"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Сохраняем настройки в БД
    folder_id_setting = db.query(Settings).filter(Settings.key == "google_drive_folder_id").first()
    if folder_id_setting:
        folder_id_setting.value = folder_id
    else:
        folder_id_setting = Settings(key="google_drive_folder_id", value=folder_id)
        db.add(folder_id_setting)
    
    credentials_setting = db.query(Settings).filter(Settings.key == "google_service_account_json").first()
    if credentials_setting:
        credentials_setting.value = content.decode('utf-8')
    else:
        credentials_setting = Settings(key="google_service_account_json", value=content.decode('utf-8'))
        db.add(credentials_setting)
    
    db.commit()
    
    # Также сохраняем файл на диск для локальной разработки
    service_account_path = os.path.join("backend", "service-account.json")
    try:
        os.makedirs(os.path.dirname(service_account_path), exist_ok=True)
        with open(service_account_path, 'w') as f:
            f.write(content.decode('utf-8'))
    except Exception as e:
        print(f"Warning: Could not save service-account.json to disk: {e}")
    
    return {
        "success": True,
        "message": "Google Drive configured successfully",
        "folder_id": folder_id,
        "service_account_email": service_account_data.get("client_email")
    }

@router.delete("/settings/google-drive")
def remove_google_drive_config(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Удалить настройки Google Drive"""
    
    # Удаляем настройки из БД
    db.query(Settings).filter(Settings.key.in_([
        "google_drive_folder_id",
        "google_service_account_json"
    ])).delete(synchronize_session=False)
    
    db.commit()
    
    return {"success": True, "message": "Google Drive configuration removed"}

@router.post("/settings/google-drive/test")
def test_google_drive_connection(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Протестировать подключение к Google Drive"""
    
    # Получаем настройки
    folder_id_setting = db.query(Settings).filter(Settings.key == "google_drive_folder_id").first()
    credentials_setting = db.query(Settings).filter(Settings.key == "google_service_account_json").first()
    
    if not folder_id_setting or not credentials_setting:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Drive not configured"
        )
    
    try:
        # Пытаемся подключиться к Google Drive
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        import json
        
        credentials_data = json.loads(credentials_setting.value)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_data,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        service = build('drive', 'v3', credentials=credentials)
        
        # Проверяем доступ к папке
        folder = service.files().get(
            fileId=folder_id_setting.value,
            fields='id,name,capabilities',
            supportsAllDrives=True
        ).execute()
        
        return {
            "success": True,
            "message": "Successfully connected to Google Drive",
            "folder_name": folder.get("name"),
            "folder_id": folder.get("id"),
            "can_edit": folder.get("capabilities", {}).get("canAddChildren", False)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect to Google Drive: {str(e)}"
        )


# Admin Management Endpoints

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    created_at: str

class UpdateUserRoleRequest(BaseModel):
    user_id: int
    role: str  # "user" or "admin"

@router.get("/admins", response_model=List[UserResponse])
def get_all_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Получить список всех пользователей"""
    users = db.query(User).all()
    return [
        UserResponse(
            id=user.id,
            email=user.email,
            role=user.role,
            created_at=user.created_at.isoformat()
        )
        for user in users
    ]

@router.post("/admins/update-role")
def update_user_role(
    request: UpdateUserRoleRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Изменить роль пользователя (сделать админом или обычным пользователем)"""
    
    # Проверяем что роль валидна
    if request.role not in ["user", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'user' or 'admin'"
        )
    
    # Находим пользователя
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Нельзя изменить роль самому себе
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    # Обновляем роль
    user.role = request.role
    db.commit()
    db.refresh(user)
    
    return {
        "success": True,
        "message": f"User {user.email} role updated to {request.role}",
        "user": UserResponse(
            id=user.id,
            email=user.email,
            role=user.role,
            created_at=user.created_at.isoformat()
        )
    }

@router.delete("/admins/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Удалить пользователя (только для админов)"""
    
    # Находим пользователя
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Нельзя удалить самого себя
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    # Удаляем пользователя (каскадно удалятся альбомы и фото)
    db.delete(user)
    db.commit()
    
    return {
        "success": True,
        "message": f"User {user.email} deleted successfully"
    }
