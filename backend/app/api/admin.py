from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import json
import os
import secrets
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
    google_drive_auth_type: Optional[str] = None

@router.get("/settings", response_model=SettingsResponse)
def get_settings_status(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Получить статус настроек Google Drive"""
    
    # Проверяем наличие настроек Google Drive
    folder_id_setting = db.query(Settings).filter(Settings.key == "google_drive_folder_id").first()
    auth_type_setting = db.query(Settings).filter(Settings.key == "google_drive_auth_type").first()
    auth_type = auth_type_setting.value if auth_type_setting else "service_account"
    credentials_key = "google_oauth_token_json" if auth_type == "oauth" else "google_service_account_json"
    credentials_setting = db.query(Settings).filter(Settings.key == credentials_key).first()
    
    configured = bool(folder_id_setting and credentials_setting)
    folder_id = folder_id_setting.value if folder_id_setting else None
    
    return SettingsResponse(
        google_drive_configured=configured,
        google_drive_folder_id=folder_id,
        google_drive_auth_type=auth_type if configured else None
    )


def upsert_setting(db: Session, key: str, value: str):
    setting = db.query(Settings).filter(Settings.key == key).first()
    if setting:
        setting.value = value
    else:
        db.add(Settings(key=key, value=value))


def get_oauth_redirect_uri(request: Request) -> str:
    return f"{str(request.base_url).rstrip('/')}/api/settings/google-drive/oauth/callback"

@router.post("/settings/google-drive")
async def configure_google_drive(
    folder_id: str = Form(...),
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


@router.post("/settings/google-drive/oauth/start")
async def start_google_drive_oauth(
    request: Request,
    folder_id: str = Form(...),
    oauth_client_file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Start Google Drive OAuth web flow."""
    if not oauth_client_file.filename.endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth client file must be a JSON file"
        )

    try:
        content = await oauth_client_file.read()
        client_config = json.loads(content.decode('utf-8'))
        if "web" not in client_config and "installed" not in client_config:
            raise ValueError("Invalid OAuth client JSON file")
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

    from google_auth_oauthlib.flow import Flow

    state = secrets.token_urlsafe(32)
    redirect_uri = get_oauth_redirect_uri(request)
    flow = Flow.from_client_config(
        client_config,
        scopes=['https://www.googleapis.com/auth/drive'],
        redirect_uri=redirect_uri,
    )
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        state=state,
    )

    upsert_setting(db, "google_drive_folder_id", folder_id)
    upsert_setting(db, "google_oauth_client_json", content.decode('utf-8'))
    upsert_setting(db, "google_oauth_state", state)
    upsert_setting(db, "google_oauth_redirect_uri", redirect_uri)
    upsert_setting(db, "google_drive_auth_type", "oauth")
    db.commit()

    return {"auth_url": auth_url}


@router.get("/settings/google-drive/oauth/callback")
def google_drive_oauth_callback(
    request: Request,
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    saved_state = db.query(Settings).filter(Settings.key == "google_oauth_state").first()
    client_setting = db.query(Settings).filter(Settings.key == "google_oauth_client_json").first()
    redirect_setting = db.query(Settings).filter(Settings.key == "google_oauth_redirect_uri").first()

    if not saved_state or saved_state.value != state or not client_setting:
        return RedirectResponse(url="/setting?oauth=invalid_state", status_code=status.HTTP_302_FOUND)

    try:
        from google_auth_oauthlib.flow import Flow

        client_config = json.loads(client_setting.value)
        redirect_uri = redirect_setting.value if redirect_setting else get_oauth_redirect_uri(request)
        flow = Flow.from_client_config(
            client_config,
            scopes=['https://www.googleapis.com/auth/drive'],
            redirect_uri=redirect_uri,
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials

        upsert_setting(db, "google_oauth_token_json", credentials.to_json())
        upsert_setting(db, "google_drive_auth_type", "oauth")
        db.query(Settings).filter(Settings.key == "google_oauth_state").delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        print(f"OAuth callback failed: {e}")
        return RedirectResponse(url="/setting?oauth=failed", status_code=status.HTTP_302_FOUND)

    return RedirectResponse(url="/setting?oauth=success", status_code=status.HTTP_302_FOUND)

@router.delete("/settings/google-drive")
def remove_google_drive_config(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Удалить настройки Google Drive"""
    
    # Удаляем настройки из БД
    db.query(Settings).filter(Settings.key.in_([
        "google_drive_folder_id",
        "google_service_account_json",
        "google_oauth_client_json",
        "google_oauth_token_json",
        "google_oauth_state",
        "google_oauth_redirect_uri",
        "google_drive_auth_type"
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
    auth_type_setting = db.query(Settings).filter(Settings.key == "google_drive_auth_type").first()
    auth_type = auth_type_setting.value if auth_type_setting else "service_account"
    credentials_key = "google_oauth_token_json" if auth_type == "oauth" else "google_service_account_json"
    credentials_setting = db.query(Settings).filter(Settings.key == credentials_key).first()
    
    if not folder_id_setting or not credentials_setting:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Drive not configured"
        )
    
    try:
        # Пытаемся подключиться к Google Drive
        from google.oauth2 import service_account
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        import json

        scopes = ['https://www.googleapis.com/auth/drive']
        credentials_data = json.loads(credentials_setting.value)
        if auth_type == "oauth":
            credentials = Credentials.from_authorized_user_info(credentials_data, scopes=scopes)
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                credentials_setting.value = credentials.to_json()
                db.commit()
        else:
            credentials = service_account.Credentials.from_service_account_info(
                credentials_data,
                scopes=scopes
            )
        service = build('drive', 'v3', credentials=credentials)
        
        # Проверяем доступ к папке
        folder = service.files().get(
            fileId=folder_id_setting.value,
            fields='id,name,capabilities,driveId',
            supportsAllDrives=True
        ).execute()
        is_shared_drive = bool(folder.get("driveId"))
        can_edit = folder.get("capabilities", {}).get("canAddChildren", False)

        if auth_type != "oauth" and not is_shared_drive:
            return {
                "success": False,
                "message": "Folder is in My Drive. Service Accounts cannot upload there because they have no storage quota. Create a Shared Drive and use a folder from it.",
                "folder_name": folder.get("name"),
                "folder_id": folder.get("id"),
                "can_edit": can_edit
            }
        
        return {
            "success": True,
            "message": "Successfully connected to Google Drive",
            "folder_name": folder.get("name"),
            "folder_id": folder.get("id"),
            "can_edit": can_edit
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


@router.post("/sync")
def sync_storage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Сверить состояние хранилища (Google Drive) с БД и удалить записи,
    ссылающиеся на удалённые файлы/альбомы. Доступна любому аутентифицированному
    пользователю: сверка глобальная (токен Drive Changes общий), удаляются только
    уже осиротевшие записи, возвращаются лишь счётчики.
    """
    from app.services.sync import sync_drive_to_db
    stats = sync_drive_to_db(db)
    return {"success": True, **stats}
