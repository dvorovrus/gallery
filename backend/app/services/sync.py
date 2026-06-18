"""
Синхронизация состояния Google Drive -> локальная БД.

Если файл/альбом удалены на Drive (или перемещены в корзину),
соответствующие записи удаляются из БД, чтобы UI не показывал "битые" фото.

Масштабируемый механизм — Drive Changes API:
  * первый запуск: один полный обход дерева папок (list_descendants) и сверка,
    после чего сохраняется startPageToken;
  * последующие запуски: инкрементальная выборка только изменившихся файлов
    (changes.list), O(изменений), а не O(N).

Для хранилищ без Changes API (например, локальное) выполняется
перебор по file_exists().
"""
import logging
from typing import Dict
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.models import Album, Photo, Share, Settings as SettingsModel

logger = logging.getLogger(__name__)
settings = get_settings()

PAGE_TOKEN_KEY = "google_drive_changes_page_token"


def _select_storage():
    if settings.STORAGE_TYPE == "google_drive":
        from app.services.google_drive import drive_service as storage
    elif settings.STORAGE_TYPE == "google_drive_oauth":
        from app.services.google_drive_oauth import drive_oauth_service as storage
    else:
        from app.services.local_storage import storage_service as storage
    return storage


def _get_setting(db: Session, key: str) -> str | None:
    row = db.query(SettingsModel).filter(SettingsModel.key == key).first()
    return row.value if row and row.value else None


def _set_setting(db: Session, key: str, value: str):
    row = db.query(SettingsModel).filter(SettingsModel.key == key).first()
    if row:
        row.value = value
    else:
        db.add(SettingsModel(key=key, value=value))
    db.commit()


def _delete_photo_row(db: Session, photo: Photo):
    """Удалить фото и его share-ссылки из БД (каскад shares через relationship)."""
    db.query(Share).filter(Share.photo_id == photo.id).delete(synchronize_session=False)
    db.delete(photo)


def _delete_album_row(db: Session, album: Album):
    """Удалить альбом, его фото и share-ссылки из БД."""
    photos = db.query(Photo).filter(Photo.album_id == album.id).all()
    for p in photos:
        _delete_photo_row(db, p)
    db.query(Share).filter(Share.album_id == album.id).delete(synchronize_session=False)
    db.delete(album)


def _sync_initial_full(db: Session, storage) -> Dict:
    """
    Первичная полная сверка: один обход дерева папок, далее удаляем
    записи БД, ссылающиеся на отсутствующие файлы.
    """
    stats = {
        "mode": "initial_full",
        "scanned": 0,
        "removed_photos": 0,
        "removed_albums": 0,
        "cleared_thumbnails": 0,
    }

    try:
        existing_ids = storage.list_descendants(storage.root_folder_id)
    except Exception as e:
        logger.error(f"[sync] list_descendants failed: {e}")
        existing_ids = set()

    stats["scanned"] = len(existing_ids)

    # Фото
    for photo in db.query(Photo).all():
        if photo.drive_file_id and photo.drive_file_id in existing_ids:
            continue
        logger.info(f"[sync] removing orphan photo {photo.id} (drive_file_id missing)")
        _delete_photo_row(db, photo)
        stats["removed_photos"] += 1

    db.commit()

    # Альбомы: папка альбома должна существовать внутри пользовательской папки
    for album in db.query(Album).all():
        try:
            user_folder_id = storage.create_user_folder(album.user_id)
            if storage.get_album_folder_id(user_folder_id, album.id) is None:
                logger.info(f"[sync] removing orphan album {album.id} (folder missing)")
                _delete_album_row(db, album)
                stats["removed_albums"] += 1
        except Exception as e:
            logger.error(f"[sync] album {album.id} check failed: {e}")

    db.commit()

    # Сохраняем точку отсчёта для последующей инкрементальной сверки
    try:
        token = storage.get_start_page_token()
        if token:
            _set_setting(db, PAGE_TOKEN_KEY, token)
    except Exception as e:
        logger.error(f"[sync] get_start_page_token failed: {e}")

    return stats


def _sync_incremental(db: Session, storage, start_token: str) -> Dict:
    """
    Инкрементальная сверка через Drive Changes API.
    """
    stats = {
        "mode": "incremental",
        "scanned": 0,
        "removed_photos": 0,
        "removed_albums": 0,
        "cleared_thumbnails": 0,
    }
    had_removal = False

    page_token = start_token
    try:
        while page_token:
            result = storage.list_changes(page_token)
            stats["scanned"] += len(result.get("changes", []))

            for ch in result.get("changes", []):
                file_id = ch.get("fileId")
                if not file_id:
                    continue
                # Удалено физически ИЛИ в корзине
                if not (ch.get("removed") or ch.get("trashed")):
                    continue
                had_removal = True

                # 1) Фото по основному файлу
                photo = db.query(Photo).filter(Photo.drive_file_id == file_id).first()
                if photo:
                    logger.info(f"[sync] removing photo {photo.id} (file {file_id} gone)")
                    _delete_photo_row(db, photo)
                    stats["removed_photos"] += 1
                    continue

                # 2) Фото по thumbnail-файлу — очищаем только thumbnail
                photo = db.query(Photo).filter(Photo.thumbnail_file_id == file_id).first()
                if photo:
                    logger.info(f"[sync] clearing thumbnail for photo {photo.id}")
                    photo.thumbnail_file_id = None
                    stats["cleared_thumbnails"] += 1
                    continue

            db.commit()

            new_token = result.get("new_start_page_token")
            if new_token:
                _set_setting(db, PAGE_TOKEN_KEY, new_token)
                break
            page_token = result.get("next_page_token")

        # Если были удаления — проверяем альбомы: папка удалена -> убираем альбом.
        # Папка альбома не хранится в БД, поэтому сверяем по существованию папки.
        # Этот шаг выполняется только при реальных удалениях (пропорционально
        # числу альбомов, а не на каждый запуск).
        if had_removal:
            stats["removed_albums"] += _sweep_missing_album_folders(db, storage)

    except Exception as e:
        logger.error(f"[sync] incremental failed: {e}")

    return stats


def _sweep_missing_album_folders(db: Session, storage) -> int:
    """Удалить альбомы, у которых больше нет папки в хранилище. Возвращает счётчик."""
    removed = 0
    # Кэшируем user_folder_id по user_id, чтобы не создавать/запрашивать повторно
    user_folder_cache: Dict[int, str] = {}
    for album in db.query(Album).all():
        try:
            user_folder_id = user_folder_cache.get(album.user_id)
            if user_folder_id is None:
                user_folder_id = storage.create_user_folder(album.user_id)
                user_folder_cache[album.user_id] = user_folder_id
            if storage.get_album_folder_id(user_folder_id, album.id) is None:
                logger.info(f"[sync] removing orphan album {album.id} (folder missing)")
                _delete_album_row(db, album)
                removed += 1
        except Exception as e:
            logger.error(f"[sync] album {album.id} folder check failed: {e}")
    db.commit()
    return removed


def _sync_via_file_exists(db: Session, storage) -> Dict:
    """
    Fallback для хранилищ без Changes API (локальное хранилище):
    проверяем каждое фото через file_exists().
    """
    stats = {
        "mode": "file_exists",
        "scanned": 0,
        "removed_photos": 0,
        "removed_albums": 0,
        "cleared_thumbnails": 0,
    }

    for photo in db.query(Photo).all():
        stats["scanned"] += 1
        if not storage.file_exists(photo.drive_file_id):
            logger.info(f"[sync] removing orphan photo {photo.id}")
            _delete_photo_row(db, photo)
            stats["removed_photos"] += 1

    db.commit()

    for album in db.query(Album).all():
        try:
            user_folder_id = storage.create_user_folder(album.user_id)
            if storage.get_album_folder_id(user_folder_id, album.id) is None:
                logger.info(f"[sync] removing orphan album {album.id}")
                _delete_album_row(db, album)
                stats["removed_albums"] += 1
        except Exception as e:
            logger.error(f"[sync] album {album.id} check failed: {e}")

    db.commit()
    return stats


def sync_drive_to_db(db: Session) -> Dict:
    """
    Главная точка входа: сверить состояние хранилища с БД и удалить
    записи, ссылающиеся на отсутствующие файлы/альбомы.
    """
    storage = _select_storage()

    has_changes_api = all(hasattr(storage, m) for m in ("get_start_page_token", "list_changes", "list_descendants"))

    try:
        if has_changes_api:
            token = _get_setting(db, PAGE_TOKEN_KEY)
            if not token:
                return _sync_initial_full(db, storage)
            return _sync_incremental(db, storage, token)
        return _sync_via_file_exists(db, storage)
    except Exception as e:
        logger.exception(f"[sync] aborted: {e}")
        return {
            "mode": "error",
            "scanned": 0,
            "removed_photos": 0,
            "removed_albums": 0,
            "cleared_thumbnails": 0,
            "error": str(e),
        }
