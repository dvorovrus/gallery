import { memo, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Plus, Trash2, X, Upload, Calendar, Type,
  ChevronLeft, ChevronRight, Share2, Globe, Lock, Copy, CheckCircle,
  Sun, Moon, Image as ImageIcon, Camera, LayoutGrid, CheckSquare, Square, LogOut, Download
} from 'lucide-react';
import Login from './components/Login';
import * as api from './services/api';

const THEME_STORAGE_KEY = 'gallery_theme';
const ruDateFormatter = new Intl.DateTimeFormat('ru-RU');
const getPhotoFullUrl = (photoId) => `http://localhost:8000/photos/${photoId}`;
const getPhotoThumbnailUrl = (photoId) => `http://localhost:8000/photos/${photoId}?thumbnail=true&width=400`;
const sortPhotosByDateDesc = (items) => [...items].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
const formatRuDate = (value) => ruDateFormatter.format(new Date(value));
const serializeAlbum = (album) => ({ id: album.id, title: album.title, created_at: album.created_at });
const serializePhoto = (photo) => ({
  id: photo.id,
  caption: photo.caption,
  created_at: photo.created_at,
  fullUrl: photo.fullUrl || getPhotoFullUrl(photo.id),
  thumbnailUrl: photo.thumbnailUrl || getPhotoThumbnailUrl(photo.id),
});

const toBase64Url = (value) => {
  if (typeof window === 'undefined') return '';
  return window.btoa(unescape(encodeURIComponent(value))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
};

const fromBase64Url = (value) => {
  if (typeof window === 'undefined') return '';
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
  const padding = normalized.length % 4 === 0 ? '' : '='.repeat(4 - (normalized.length % 4));
  return decodeURIComponent(escape(window.atob(`${normalized}${padding}`)));
};

const encodeSharePayload = (payload) => toBase64Url(JSON.stringify(payload));

const decodeSharePayload = (encodedPayload) => {
  if (!encodedPayload) return null;
  try {
    return JSON.parse(fromBase64Url(encodedPayload));
  } catch (error) {
    return null;
  }
};

const bytesToHex = (bytes) => Array.from(bytes).map((byte) => byte.toString(16).padStart(2, '0')).join('');

const hashPasswordValue = async (value) => {
  if (typeof window !== 'undefined' && window.crypto?.subtle) {
    const buffer = await window.crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
    return bytesToHex(new Uint8Array(buffer));
  }

  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = ((hash << 5) - hash) + value.charCodeAt(index);
    hash |= 0;
  }
  return `fallback-${Math.abs(hash)}`;
};

const getAppBasePath = (pathname) => pathname.startsWith('/share/') ? '/' : pathname;

const parseShareFromLocation = (locationLike) => {
  const shareRoute = locationLike.hash.startsWith('#/share/')
    ? locationLike.hash.slice(1)
    : locationLike.pathname.startsWith('/share/')
      ? `${locationLike.pathname}${locationLike.search}`
      : null;

  if (!shareRoute) return null;

  const [pathPart, queryString = ''] = shareRoute.split('?');
  const segments = pathPart.split('/').filter(Boolean);
  if (segments.length < 3 || segments[0] !== 'share') return null;

  const [, type, token] = segments;
  const payload = decodeSharePayload(new URLSearchParams(queryString).get('data'));
  if (!payload || payload.type !== type || payload.token !== token) return null;

  return payload;
};

// --- Скелетон для загрузки фото ---
const PhotoSkeleton = () => (
  <div className="break-inside-avoid relative rounded-2xl sm:rounded-3xl overflow-hidden bg-neutral-200 dark:bg-neutral-800 animate-pulse">
    <div className="w-full aspect-[3/4] bg-gradient-to-br from-neutral-300 to-neutral-200 dark:from-neutral-700 dark:to-neutral-800 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 dark:via-white/5 to-transparent shimmer" />
    </div>
  </div>
);

// --- Компонент фото с lazy загрузкой ---
const PhotoCard = memo(function PhotoCard({
  photo,
  index,
  onPhotoLoad,
  isLoaded,
  onOpenIndex,
  onSharePhoto,
  onDeletePhoto,
  onDownloadPhoto,
  isSelectionMode,
  isSelected,
  onToggleSelectPhoto,
}: any) {
  return (
    <div
      className="break-inside-avoid relative group rounded-2xl sm:rounded-3xl overflow-hidden bg-neutral-200 dark:bg-neutral-800"
      onClick={() => {
        if (!isSelectionMode && isLoaded) {
          onOpenIndex(index);
        }
      }}
      style={{ cursor: isSelectionMode ? 'default' : (isLoaded ? 'zoom-in' : 'default') }}
    >
      {/* Скелетон пока фото не загружено */}
      {!isLoaded && (
        <div className="absolute inset-0 bg-gradient-to-br from-neutral-300 to-neutral-200 dark:from-neutral-700 dark:to-neutral-800 animate-pulse">
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 dark:via-white/5 to-transparent shimmer" />
        </div>
      )}

      <img
        src={photo.thumbnailUrl || getPhotoThumbnailUrl(photo.id)}
        alt={photo.caption}
        className={`w-full h-auto object-cover transition-all duration-700 ${isLoaded ? 'opacity-100 group-hover:scale-105' : 'opacity-0'}`}
        loading="lazy"
        onLoad={() => onPhotoLoad(photo.id)}
      />

      {/* Чекбокс для режима выбора */}
      {isSelectionMode && isLoaded && (
        <div className="absolute top-3 left-3 z-10">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleSelectPhoto(photo.id);
              }}
              className="p-2 bg-white/90 dark:bg-neutral-900/90 backdrop-blur-sm rounded-lg hover:bg-white dark:hover:bg-neutral-800 transition-colors"
            >
            {isSelected ? (
              <CheckSquare className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            ) : (
              <Square className="w-5 h-5 text-neutral-500 dark:text-neutral-400" />
            )}
          </button>
        </div>
      )}

      {/* Оверлей при наведении - скрыт в режиме выбора */}
      {isLoaded && !isSelectionMode && (
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/0 to-black/30 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-between p-4 sm:p-6">
          <div className="flex justify-end gap-2 transform -translate-y-4 group-hover:translate-y-0 transition-transform duration-300">
            <button onClick={(e) => { e.stopPropagation(); onDownloadPhoto(photo); }} className="p-2.5 bg-white/20 hover:bg-white/40 backdrop-blur-md text-white rounded-full transition-colors" title="Скачать">
              <Download className="w-4 h-4" />
            </button>
            <button onClick={(e) => { e.stopPropagation(); onSharePhoto(photo); }} className="p-2.5 bg-white/20 hover:bg-white/40 backdrop-blur-md text-white rounded-full transition-colors" title="Поделиться">
              <Share2 className="w-4 h-4" />
            </button>
            <button onClick={(e) => { e.stopPropagation(); onDeletePhoto(photo); }} className="p-2.5 bg-white/20 hover:bg-red-500/80 backdrop-blur-md text-white rounded-full transition-colors" title="Удалить">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>

          <div className="transform translate-y-4 group-hover:translate-y-0 transition-transform duration-300">
            <p className="text-white font-medium text-lg drop-shadow-md">{photo.caption}</p>
            <p className="text-white/80 text-sm mt-1">{formatRuDate(photo.created_at)}</p>
          </div>
        </div>
      )}
    </div>
  );
});

// --- Модальные окна (z-[70] чтобы быть поверх Лайтбокса z-[60]) ---
const ModalWrapper = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-white/40 dark:bg-black/60 backdrop-blur-md transition-opacity">
      <div className="bg-white dark:bg-neutral-900 rounded-3xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-300 border border-neutral-200 dark:border-neutral-800 flex flex-col max-h-[90vh]">
        <div className="flex justify-between items-center p-6 pb-4 shrink-0">
          <h3 className="text-xl font-medium tracking-tight text-neutral-900 dark:text-white">{title}</h3>
          <button onClick={onClose} className="p-2 text-neutral-400 hover:text-neutral-900 dark:hover:text-white bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 rounded-full transition-all">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-6 pt-2 overflow-y-auto hide-scrollbar">{children}</div>
      </div>
    </div>
  );
};

const ShareModal = ({ isOpen, onClose, title, type, shareTarget }) => {
  const [accessType, setAccessType] = useState('public');
  const [password, setPassword] = useState('');
  const [generatedLink, setGeneratedLink] = useState(null);
  const [isCopied, setIsCopied] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (isOpen) {
      setAccessType('public');
      setPassword('');
      setGeneratedLink(null);
      setIsCopied(false);
      setIsGenerating(false);
      setErrorMessage('');
    }
  }, [isOpen]);

  const handleGenerateLink = async () => {
    if (!shareTarget) {
      setErrorMessage('Не удалось подготовить данные для шаринга.');
      return;
    }

    setIsGenerating(true);
    setErrorMessage('');
    const token = Math.random().toString(36).substring(2, 15);
    const origin = typeof window !== 'undefined' && window.location.origin !== 'null' ? window.location.origin : 'https://gallery.app';
    const pathname = typeof window !== 'undefined' ? getAppBasePath(window.location.pathname) : '/';
    const payload = {
      version: 1,
      token,
      type,
      title,
      accessType,
      album: shareTarget.album ? serializeAlbum(shareTarget.album) : null,
      photo: shareTarget.photo ? serializePhoto(shareTarget.photo) : null,
      photos: (shareTarget.photos || []).map(serializePhoto),
      passwordHash: accessType === 'password' ? await hashPasswordValue(password.trim()) : null,
    };
    const encodedPayload = encodeSharePayload(payload);
    setGeneratedLink(`${origin}${pathname}#/share/${type}/${token}?data=${encodedPayload}`);
    setIsCopied(false);
    setIsGenerating(false);
  };

  const copyToClipboard = () => {
    if (!generatedLink) return;
    try {
      if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(generatedLink);
      else {
        const textArea = document.createElement("textarea"); textArea.value = generatedLink;
        textArea.style.position = "absolute"; textArea.style.left = "-999999px"; document.body.prepend(textArea);
        textArea.select(); document.execCommand('copy'); textArea.remove();
      }
      setIsCopied(true); setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {}
  };

  return (
    <ModalWrapper isOpen={isOpen} onClose={onClose} title="Поделиться">
      <div className="space-y-6">
        {!generatedLink ? (
          <>
            <div className="flex bg-neutral-100 dark:bg-neutral-800 p-1 rounded-2xl">
              <button onClick={() => setAccessType('public')} className={`flex-1 py-2.5 rounded-xl text-sm font-medium transition-all ${accessType === 'public' ? 'bg-white dark:bg-neutral-700 text-neutral-900 dark:text-white shadow-sm' : 'text-neutral-500 dark:text-neutral-400'}`}>
                Публично
              </button>
              <button onClick={() => setAccessType('password')} className={`flex-1 py-2.5 rounded-xl text-sm font-medium transition-all ${accessType === 'password' ? 'bg-white dark:bg-neutral-700 text-neutral-900 dark:text-white shadow-sm' : 'text-neutral-500 dark:text-neutral-400'}`}>
                С паролем
              </button>
            </div>

            {accessType === 'password' && (
              <div className="animate-in fade-in slide-in-from-top-2">
                <input 
                  type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Введите пароль"
                  className="w-full px-4 py-3 bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 text-neutral-900 dark:text-white rounded-2xl focus:border-neutral-900 dark:focus:border-white outline-none transition-all"
                />
              </div>
            )}

            {errorMessage && (
              <p className="text-sm text-red-600 dark:text-red-400">{errorMessage}</p>
            )}

            <button onClick={handleGenerateLink} disabled={isGenerating || (accessType === 'password' && password.trim().length === 0)}
              className="w-full py-3.5 flex items-center justify-center gap-2 bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-200 text-white dark:text-neutral-900 disabled:opacity-50 rounded-2xl font-medium transition-all"
            >
              {isGenerating ? 'Создаем...' : 'Создать ссылку'}
            </button>
          </>
        ) : (
          <div className="space-y-5 animate-in fade-in">
            <div className="flex flex-col items-center justify-center py-4">
              <div className="w-12 h-12 bg-neutral-100 dark:bg-neutral-800 rounded-full flex items-center justify-center mb-3">
                <CheckCircle className="w-6 h-6 text-neutral-900 dark:text-white" />
              </div>
              <h4 className="font-medium text-neutral-900 dark:text-white">Ссылка скопирована</h4>
              <p className="text-sm text-neutral-500 mt-1 text-center">
                {accessType === 'password' ? 'Доступ защищен паролем.' : 'Отправьте ее друзьям.'}
              </p>
            </div>

            <div className="flex items-center gap-2 bg-neutral-50 dark:bg-neutral-950 p-2 rounded-2xl border border-neutral-200 dark:border-neutral-800">
              <input type="text" readOnly value={generatedLink} className="flex-1 bg-transparent px-2 text-neutral-600 dark:text-neutral-300 outline-none text-sm font-mono truncate" />
              <button onClick={copyToClipboard} className="p-2.5 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 rounded-xl hover:opacity-80 transition-all">
                {isCopied ? <CheckCircle className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
              </button>
            </div>
          </div>
        )}
      </div>
    </ModalWrapper>
  );
};

const SharedContentView = ({
  shareData,
  isDarkMode,
  onToggleTheme,
  passwordValue,
  onPasswordChange,
  onUnlock,
  isUnlocking,
  passwordError,
  onOpenPhoto,
  onBack,
}) => {
  const sharedPhotos = shareData.type === 'album' ? shareData.photos : shareData.photo ? [shareData.photo] : [];
  const isLocked = shareData.accessType === 'password';

  return (
    <div className={`min-h-screen font-sans transition-colors duration-500 ${isDarkMode ? 'dark' : ''}`}>
      <div className="min-h-screen bg-white dark:bg-neutral-950 text-neutral-900 dark:text-neutral-100 transition-colors duration-500">
        <nav className="sticky top-0 z-40 bg-white/80 dark:bg-neutral-950/80 backdrop-blur-xl border-b border-neutral-200 dark:border-neutral-900 py-4">
          <div className="max-w-6xl mx-auto px-4 sm:px-8 flex items-center justify-between gap-4">
            <div>
              <p className="text-sm text-neutral-500 dark:text-neutral-400">
                {shareData.type === 'album' ? 'Общий альбом' : 'Общее фото'}
              </p>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight">{shareData.title}</h1>
            </div>

            <div className="flex items-center gap-3">
              <button onClick={onToggleTheme} className="p-2.5 text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white rounded-full hover:bg-neutral-100 dark:hover:bg-neutral-900 transition-colors">
                {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
              <button onClick={onBack} className="px-4 py-2.5 bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-200 text-white dark:text-neutral-900 rounded-full font-medium transition-all">
                В галерею
              </button>
            </div>
          </div>
        </nav>

        <main className="max-w-6xl mx-auto px-4 sm:px-8 py-10">
          {isLocked ? (
            <div className="max-w-md mx-auto">
              <div className="bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-3xl p-6 sm:p-8 shadow-sm">
                <div className="w-14 h-14 rounded-full bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 flex items-center justify-center mb-5">
                  <Lock className="w-6 h-6" />
                </div>
                <h2 className="text-2xl font-semibold mb-2">Нужен пароль</h2>
                <p className="text-neutral-500 dark:text-neutral-400 mb-6">
                  Эта ссылка защищена паролем. Введите пароль, чтобы открыть {shareData.type === 'album' ? 'альбом' : 'фото'}.
                </p>

                <div className="space-y-4">
                  <input
                    autoFocus
                    type="password"
                    value={passwordValue}
                    onChange={(event) => onPasswordChange(event.target.value)}
                    placeholder="Введите пароль"
                    className="w-full px-4 py-3 bg-white dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 text-neutral-900 dark:text-white rounded-2xl focus:border-neutral-900 dark:focus:border-white outline-none transition-all"
                  />
                  {passwordError && (
                    <p className="text-sm text-red-600 dark:text-red-400">{passwordError}</p>
                  )}
                  <button
                    onClick={onUnlock}
                    disabled={isUnlocking || passwordValue.trim().length === 0}
                    className="w-full py-3.5 bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-200 disabled:opacity-50 text-white dark:text-neutral-900 rounded-2xl font-medium transition-all"
                  >
                    {isUnlocking ? 'Проверяем...' : 'Открыть доступ'}
                  </button>
                </div>
              </div>
            </div>
          ) : shareData.type === 'photo' && shareData.photo ? (
            <div className="max-w-4xl mx-auto">
              <div className="overflow-hidden rounded-[2rem] bg-neutral-100 dark:bg-neutral-900 shadow-xl border border-neutral-200 dark:border-neutral-800">
                <img
                  src={shareData.photo.fullUrl}
                  alt={shareData.photo.caption}
                  className="w-full max-h-[75vh] object-cover cursor-zoom-in"
                  onClick={() => onOpenPhoto(0)}
                />
                <div className="p-6 sm:p-8">
                  <h2 className="text-2xl font-semibold">{shareData.photo.caption}</h2>
                    <p className="text-neutral-500 dark:text-neutral-400 mt-2">
                      {formatRuDate(shareData.photo.created_at)}
                    </p>
                </div>
              </div>
            </div>
          ) : sharedPhotos.length > 0 ? (
            <div className="space-y-6">
              <p className="text-neutral-500 dark:text-neutral-400">
                {sharedPhotos.length} {sharedPhotos.length === 1 ? 'фотография' : sharedPhotos.length < 5 ? 'фотографии' : 'фотографий'}
              </p>

              <div className="columns-1 sm:columns-2 lg:columns-3 gap-6 space-y-6">
                {sharedPhotos.map((photo, index) => (
                  <div
                    key={photo.id}
                    onClick={() => onOpenPhoto(index)}
                    className="break-inside-avoid relative group rounded-2xl sm:rounded-3xl overflow-hidden bg-neutral-100 dark:bg-neutral-900 cursor-zoom-in"
                  >
                    <img src={photo.thumbnailUrl} alt={photo.caption} className="w-full h-auto object-cover transition-transform duration-700 group-hover:scale-105" />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/0 to-black/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-5">
                      <div>
                        <p className="text-white font-medium text-lg drop-shadow-md">{photo.caption}</p>
                        <p className="text-white/80 text-sm mt-1">{formatRuDate(photo.created_at)}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="py-24 text-center text-neutral-500 dark:text-neutral-400">
              <ImageIcon className="w-14 h-14 mx-auto mb-4 opacity-50" />
              <p>В этой ссылке не найдено данных для отображения.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

const CreateAlbumModal = ({ isOpen, onClose, onCreate }) => {
  const [name, setName] = useState('');
  useEffect(() => { if (isOpen) setName(''); }, [isOpen]);

  return (
    <ModalWrapper isOpen={isOpen} onClose={onClose} title="Новый альбом">
      <div className="space-y-6">
        <input 
          autoFocus type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Название альбома"
          className="w-full px-4 py-3 bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 text-neutral-900 dark:text-white rounded-2xl focus:border-neutral-900 dark:focus:border-white outline-none transition-all text-lg"
        />
        <button onClick={() => onCreate(name)} disabled={!name.trim()}
          className="w-full py-3.5 bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-200 disabled:opacity-50 text-white dark:text-neutral-900 rounded-2xl font-medium transition-all"
        >
          Создать
        </button>
      </div>
    </ModalWrapper>
  );
};

const UploadPhotoModal = ({ isOpen, onClose, onUpload }) => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [caption, setCaption] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);
  const previewUrlsRef = useRef([]);

  useEffect(() => {
    if (isOpen) {
      setSelectedFiles([]);
      setCaption('');
      setIsUploading(false);
      previewUrlsRef.current = [];
    }
    return () => {
      previewUrlsRef.current.forEach((preview) => URL.revokeObjectURL(preview));
      previewUrlsRef.current = [];
    };
  }, [isOpen]);

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      const newFiles = files.map(file => ({ file, preview: URL.createObjectURL(file), id: Math.random().toString(36).substring(7) }));
      previewUrlsRef.current.push(...newFiles.map((file) => file.preview));
      setSelectedFiles(prev => [...prev, ...newFiles]);
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeFile = (idToRemove) => {
    setSelectedFiles(prev => {
      const fileToRemove = prev.find(f => f.id === idToRemove);
      if (fileToRemove) {
        URL.revokeObjectURL(fileToRemove.preview);
        previewUrlsRef.current = previewUrlsRef.current.filter((preview) => preview !== fileToRemove.preview);
      }
      return prev.filter(f => f.id !== idToRemove);
    });
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0 || isUploading) return;
    setIsUploading(true);
    try {
      await onUpload(selectedFiles.map(f => f.file), caption);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <ModalWrapper isOpen={isOpen} onClose={onClose} title="Добавить фото">
      <div className="space-y-5">
        <input type="file" accept="image/*" multiple ref={fileInputRef} onChange={handleFileChange} className="hidden" />

        {selectedFiles.length === 0 ? (
          <div onClick={() => fileInputRef.current?.click()} className="aspect-video w-full border-2 border-dashed border-neutral-200 dark:border-neutral-800 rounded-3xl flex flex-col items-center justify-center text-neutral-500 hover:text-neutral-900 dark:hover:text-white hover:border-neutral-400 dark:hover:border-neutral-600 hover:bg-neutral-50 dark:hover:bg-neutral-800/50 cursor-pointer transition-all">
            <Camera className="w-10 h-10 mb-3 opacity-50" />
            <p className="font-medium">Выбрать файлы</p>
            <p className="text-sm mt-1 text-neutral-400">Можно выбрать несколько</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between text-sm text-neutral-500 dark:text-neutral-400 px-1">
              <span>Выбрано: {selectedFiles.length}</span>
              <button onClick={() => fileInputRef.current?.click()} className="text-neutral-900 dark:text-white hover:underline font-medium">
                + Добавить еще
              </button>
            </div>
            <div className="grid grid-cols-3 gap-3 max-h-[30vh] overflow-y-auto hide-scrollbar rounded-2xl">
              {selectedFiles.map((fileObj) => (
                <div key={fileObj.id} className="relative aspect-square rounded-2xl overflow-hidden bg-neutral-100 dark:bg-neutral-900 group">
                  <img src={fileObj.preview} alt="Preview" className="w-full h-full object-cover" />
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <button onClick={() => removeFile(fileObj.id)} className="p-2 bg-red-600 text-white rounded-full hover:bg-red-700 transition-colors shadow-lg transform scale-90 group-hover:scale-100 duration-200">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div className="space-y-3 pt-2">
          <input type="text" value={caption} onChange={(e) => setCaption(e.target.value)} placeholder="Общая подпись (необязательно)"
            className="w-full px-4 py-3 bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 text-neutral-900 dark:text-white rounded-2xl focus:border-neutral-900 dark:focus:border-white outline-none transition-all" />
        </div>

        <button onClick={handleUpload} disabled={selectedFiles.length === 0 || isUploading}
          className="w-full py-3.5 mt-2 bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-200 disabled:opacity-50 disabled:cursor-not-allowed text-white dark:text-neutral-900 rounded-2xl font-medium transition-all flex items-center justify-center gap-2"
        >
          {isUploading ? (
            <>
              <div className="w-5 h-5 border-2 border-white/30 dark:border-neutral-900/30 border-t-white dark:border-t-neutral-900 rounded-full animate-spin" />
              <span>Загрузка...</span>
            </>
          ) : (
            <>Загрузить {selectedFiles.length > 0 ? selectedFiles.length : ''} {selectedFiles.length === 1 ? 'фото' : selectedFiles.length > 1 ? 'фото' : ''}</>
          )}
        </button>
      </div>
    </ModalWrapper>
  );
};

const DeleteConfirmModal = ({ isOpen, onClose, onConfirm, title, type }) => (
  <ModalWrapper isOpen={isOpen} onClose={onClose} title="Удалить?">
    <p className="text-neutral-600 dark:text-neutral-400 mb-6 text-sm">
      Вы уверены, что хотите удалить <strong>{title}</strong>? 
      {type === 'album' && " Все фотографии внутри будут удалены."}
    </p>
    <div className="flex gap-3">
      <button onClick={onClose} className="flex-1 py-3 bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-900 dark:text-white rounded-2xl font-medium transition-colors">
        Отмена
      </button>
      <button onClick={onConfirm} className="flex-1 py-3 bg-red-600 hover:bg-red-700 text-white rounded-2xl font-medium transition-colors">
        Удалить
      </button>
    </div>
  </ModalWrapper>
);

// --- Лайтбокс (z-[60]) ---
const Lightbox = ({ photo, photosLength, onClose, onNext, onPrev, onShare, onDelete, onDownload, showActions = true }) => {
  if (!photo) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-white/95 dark:bg-black/95 backdrop-blur-xl animate-in fade-in duration-300">
      <div className="absolute top-0 inset-x-0 p-6 flex justify-between items-center z-10">
        <div className="text-neutral-900 dark:text-white">
          <h3 className="font-medium text-lg">{photo.caption}</h3>
          <p className="text-neutral-500 dark:text-neutral-400 text-sm mt-0.5">{formatRuDate(photo.created_at)}</p>
        </div>
        <div className="flex gap-3">
          {showActions && (
            <>
              <button onClick={onDownload} className="p-3 bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-900 dark:hover:bg-neutral-800 text-neutral-900 dark:text-white rounded-full transition-all">
                <Download className="w-5 h-5" />
              </button>
              <button onClick={onShare} className="p-3 bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-900 dark:hover:bg-neutral-800 text-neutral-900 dark:text-white rounded-full transition-all">
                <Share2 className="w-5 h-5" />
              </button>
              <button onClick={onDelete} className="p-3 bg-red-50 hover:bg-red-100 dark:bg-red-900/20 dark:hover:bg-red-900/40 text-red-600 dark:text-red-400 rounded-full transition-all">
                <Trash2 className="w-5 h-5" />
              </button>
            </>
          )}
          <button onClick={onClose} className="p-3 bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-900 dark:hover:bg-neutral-800 text-neutral-900 dark:text-white rounded-full transition-all ml-2">
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>
      
      {photosLength > 1 && (
        <>
          <button onClick={onPrev} className="absolute left-4 sm:left-8 p-4 bg-white/50 hover:bg-white dark:bg-black/50 dark:hover:bg-black text-neutral-900 dark:text-white rounded-full transition-all z-10 backdrop-blur-md hidden sm:block">
            <ChevronLeft className="w-6 h-6" />
          </button>
          <button onClick={onNext} className="absolute right-4 sm:right-8 p-4 bg-white/50 hover:bg-white dark:bg-black/50 dark:hover:bg-black text-neutral-900 dark:text-white rounded-full transition-all z-10 backdrop-blur-md hidden sm:block">
            <ChevronRight className="w-6 h-6" />
          </button>
        </>
      )}

      <div className="relative w-full h-full flex items-center justify-center p-4 sm:p-16" onClick={onClose}>
        <img src={photo.fullUrl || getPhotoFullUrl(photo.id)} alt={photo.caption} className="max-w-full max-h-full object-contain rounded-md shadow-2xl" onClick={(e) => e.stopPropagation()} />
      </div>
    </div>
  );
};


// --- Главный компонент ---
export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('auth_token'));
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    if (savedTheme === 'light') return false;
    if (savedTheme === 'dark') return true;
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  const [albums, setAlbums] = useState([]);
  const [photos, setPhotos] = useState([]);
  const [selectedAlbumId, setSelectedAlbumId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingPhotos, setLoadingPhotos] = useState(false);
  const [loadedPhotoIds, setLoadedPhotoIds] = useState<Set<number>>(new Set());

  // Состояние для множественного выбора
  const [isSelectionMode, setIsSelectionMode] = useState(false);
  const [selectedPhotoIds, setSelectedPhotoIds] = useState<Set<number>>(new Set());

  const [isCreateAlbumModalOpen, setIsCreateAlbumModalOpen] = useState(false);
  const [isUploadPhotoModalOpen, setIsUploadPhotoModalOpen] = useState(false);

  const [lightboxPhotoIndex, setLightboxPhotoIndex] = useState(null);
  const [sharedLightboxPhotoIndex, setSharedLightboxPhotoIndex] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState({ isOpen: false, type: null, id: null, title: '' });
  const [shareModal, setShareModal] = useState({ isOpen: false, type: null, id: null, title: '' });
  const [activeShare, setActiveShare] = useState(null);
  const [sharePasswordInput, setSharePasswordInput] = useState('');
  const [sharePasswordError, setSharePasswordError] = useState('');
  const [isUnlockingShare, setIsUnlockingShare] = useState(false);

  const currentAlbum = useMemo(() => albums.find(a => a.id === selectedAlbumId) || albums[0], [albums, selectedAlbumId]);
  const currentPhotos = useMemo(() => sortPhotosByDateDesc(photos.filter(p => p.album_id === selectedAlbumId)), [photos, selectedAlbumId]);
  const shareTarget = useMemo(() => {
    if (shareModal.type === 'album') {
      const album = albums.find((item) => item.id === shareModal.id);
      if (!album) return null;
      return {
        album,
        photos: sortPhotosByDateDesc(currentPhotos),
      };
    }

    const photo = currentPhotos.find((item) => item.id === shareModal.id) || photos.find((item) => item.id === shareModal.id);
    if (!photo) return null;
    return {
      album: albums.find((item) => item.id === photo.album_id) || null,
      photo,
      photos: [photo],
    };
  }, [albums, currentPhotos, photos, shareModal.id, shareModal.type]);
  const sharedPhotos = useMemo(() => (
    activeShare ? (activeShare.type === 'album' ? activeShare.photos : activeShare.photo ? [activeShare.photo] : []) : []
  ), [activeShare]);

  // Apply dark mode class to html element
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem(THEME_STORAGE_KEY, isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  // Load albums on mount
  useEffect(() => {
    if (isAuthenticated) {
      loadAlbums();
    }
  }, [isAuthenticated]);

  // Load photos when album changes
  useEffect(() => {
    if (selectedAlbumId) {
      loadPhotos(selectedAlbumId);
    }
  }, [selectedAlbumId]);

  useEffect(() => {
    const syncShareState = () => {
      const parsedShare = parseShareFromLocation(window.location);
      setActiveShare(parsedShare);
      setSharePasswordInput('');
      setSharePasswordError('');
      setIsUnlockingShare(false);
      setSharedLightboxPhotoIndex(null);
    };

    syncShareState();
    window.addEventListener('hashchange', syncShareState);
    window.addEventListener('popstate', syncShareState);

    return () => {
      window.removeEventListener('hashchange', syncShareState);
      window.removeEventListener('popstate', syncShareState);
    };
  }, []);

  const loadAlbums = async () => {
    try {
      setLoading(true);
      const albumsData = await api.getAlbums();
      setAlbums(albumsData);
      if (albumsData.length > 0 && !selectedAlbumId) {
        setSelectedAlbumId(albumsData[0].id);
      }
    } catch (error) {
      console.error('Failed to load albums:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPhotos = async (albumId: number) => {
    setLoadingPhotos(true);
    setLoadedPhotoIds(new Set()); // Сбрасываем загруженные фото
    try {
      const photosData = await api.getPhotos(albumId);
      setPhotos(photosData);
      setLoadingPhotos(false);
      // Фото будут загружаться через <img> с событием onLoad
    } catch (error) {
      console.error('Failed to load photos:', error);
      setLoadingPhotos(false);
    }
  };

  const handleLogin = async (email: string, password: string) => {
    await api.login(email, password);
    setIsAuthenticated(true);
  };

  const handleRegister = async (email: string, password: string) => {
    await api.register(email, password);
    await api.login(email, password);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    api.clearAuthToken();
    setIsAuthenticated(false);
    setAlbums([]);
    setPhotos([]);
    setSelectedAlbumId(null);
  };

  const toggleTheme = useCallback(() => setIsDarkMode((prev) => !prev), []);

  const handleCreateAlbum = async (name) => {
    if (!name.trim()) return;
    try {
      await api.createAlbum(name.trim());
      await loadAlbums();
      setIsCreateAlbumModalOpen(false);
    } catch (error) {
      console.error('Failed to create album:', error);
    }
  };

  const handleDeleteAlbum = async (id) => {
    try {
      await api.deleteAlbum(id);
      await loadAlbums();
      if (selectedAlbumId === id) setSelectedAlbumId(albums[0]?.id || null);
    } catch (error) {
      console.error('Failed to delete album:', error);
    }
  };

  const handleUploadPhotos = async (files, caption) => {
    if (!selectedAlbumId) return;
    try {
      await api.uploadPhotos(selectedAlbumId, files, caption);
      await loadPhotos(selectedAlbumId);
      setIsUploadPhotoModalOpen(false);
    } catch (error) {
      console.error('Failed to upload photos:', error);
    }
  };

  const handleDeletePhoto = async (id) => {
    try {
      await api.deletePhoto(id);
      await loadPhotos(selectedAlbumId);
      if (lightboxPhotoIndex !== null) setLightboxPhotoIndex(null);
    } catch (error) {
      console.error('Failed to delete photo:', error);
    }
  };

  const handleDownloadPhoto = useCallback(async (photo) => {
    try {
      const fallbackName = photo?.filename || `${photo?.caption || 'photo'}.jpg`;
      await api.downloadPhoto(photo.id, fallbackName);
    } catch (error) {
      console.error('Failed to download photo:', error);
    }
  }, []);

  const handleDownloadAlbum = useCallback(async (album) => {
    try {
      await api.downloadAlbum(album.id, `${album.title || 'album'}.zip`);
    } catch (error) {
      console.error('Failed to download album:', error);
    }
  }, []);

  const handleBatchDeletePhotos = async () => {
    if (selectedPhotoIds.size === 0) return;
    try {
      await api.batchDeletePhotos(Array.from(selectedPhotoIds));
      await loadPhotos(selectedAlbumId);
      setSelectedPhotoIds(new Set());
      setIsSelectionMode(false);
    } catch (error) {
      console.error('Failed to batch delete photos:', error);
    }
  };

  const selectAllPhotos = () => {
    const allPhotoIds = new Set(currentPhotos.map(p => p.id));
    setSelectedPhotoIds(allPhotoIds);
  };

  const deselectAllPhotos = () => {
    setSelectedPhotoIds(new Set());
  };

  const handlePhotoLoad = useCallback((photoId: number) => {
    setLoadedPhotoIds(prev => new Set(prev).add(photoId));
  }, []);

  const handleOpenPhoto = useCallback((index) => {
    setLightboxPhotoIndex(index);
  }, []);

  const handleOpenSharedPhoto = useCallback((index) => {
    setSharedLightboxPhotoIndex(index);
  }, []);

  const handleSharePhoto = useCallback((photo) => {
    setShareModal({ isOpen: true, type: 'photo', id: photo.id, title: photo.caption });
  }, []);

  const handleDeletePhotoPrompt = useCallback((photo) => {
    setDeleteConfirm({ isOpen: true, type: 'photo', id: photo.id, title: 'это фото' });
  }, []);

  const handleToggleSelectPhoto = useCallback((photoId: number) => {
    setSelectedPhotoIds((prev) => {
      const next = new Set(prev);
      if (next.has(photoId)) {
        next.delete(photoId);
      } else {
        next.add(photoId);
      }
      return next;
    });
  }, []);

  const handleUnlockShare = async () => {
    if (!activeShare?.passwordHash) return;
    setIsUnlockingShare(true);
    const passwordHash = await hashPasswordValue(sharePasswordInput.trim());

    if (passwordHash === activeShare.passwordHash) {
      setActiveShare({ ...activeShare, accessType: 'public', passwordHash: null });
      setSharePasswordError('');
      setIsUnlockingShare(false);
      return;
    }

    setSharePasswordError('Неверный пароль. Попробуйте еще раз.');
    setIsUnlockingShare(false);
  };

  const handleExitShare = () => {
    const pathname = getAppBasePath(window.location.pathname);
    window.history.pushState({}, '', pathname);
    setActiveShare(null);
    setSharedLightboxPhotoIndex(null);
    setSharePasswordInput('');
    setSharePasswordError('');
  };

  if (activeShare) {
    return (
      <>
        <SharedContentView
          shareData={activeShare}
          isDarkMode={isDarkMode}
          onToggleTheme={toggleTheme}
          passwordValue={sharePasswordInput}
          onPasswordChange={setSharePasswordInput}
          onUnlock={handleUnlockShare}
          isUnlocking={isUnlockingShare}
          passwordError={sharePasswordError}
          onOpenPhoto={handleOpenSharedPhoto}
          onBack={handleExitShare}
        />
        <Lightbox 
          photo={sharedLightboxPhotoIndex !== null ? sharedPhotos[sharedLightboxPhotoIndex] : null}
          photosLength={sharedPhotos.length}
          onClose={() => setSharedLightboxPhotoIndex(null)}
          onNext={() => setSharedLightboxPhotoIndex((prev) => (prev + 1) % sharedPhotos.length)}
          onPrev={() => setSharedLightboxPhotoIndex((prev) => (prev - 1 + sharedPhotos.length) % sharedPhotos.length)}
          onDownload={() => {
            const photo = sharedLightboxPhotoIndex !== null ? sharedPhotos[sharedLightboxPhotoIndex] : null;
            if (photo?.id) handleDownloadPhoto(photo);
          }}
          onShare={() => {}}
          onDelete={() => {}}
          showActions={false}
        />
      </>
    );
  }

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} onRegister={handleRegister} />;
  }

  return (
    <div className={`min-h-screen font-sans transition-colors duration-500 ${isDarkMode ? 'dark' : ''}`}>
      <div className="min-h-screen bg-white dark:bg-neutral-950 text-neutral-900 dark:text-neutral-100 transition-colors duration-500 relative">
        
        {/* Модальные окна */}
        <CreateAlbumModal isOpen={isCreateAlbumModalOpen} onClose={() => setIsCreateAlbumModalOpen(false)} onCreate={handleCreateAlbum} />
        <UploadPhotoModal isOpen={isUploadPhotoModalOpen} onClose={() => setIsUploadPhotoModalOpen(false)} onUpload={handleUploadPhotos} />
        
        <DeleteConfirmModal 
          isOpen={deleteConfirm.isOpen} 
          onClose={() => setDeleteConfirm({ isOpen: false, type: null, id: null, title: '' })} 
          onConfirm={() => {
            if (deleteConfirm.type === 'album') handleDeleteAlbum(deleteConfirm.id);
            if (deleteConfirm.type === 'photo') handleDeletePhoto(deleteConfirm.id);
            setDeleteConfirm({ isOpen: false, type: null, id: null, title: '' });
          }} 
          title={deleteConfirm.title} 
          type={deleteConfirm.type} 
        />
        
        <ShareModal 
          isOpen={shareModal.isOpen} 
          onClose={() => setShareModal({ ...shareModal, isOpen: false })} 
          title={shareModal.title} 
          type={shareModal.type} 
          shareTarget={shareTarget}
        />
        
        <Lightbox 
          photo={lightboxPhotoIndex !== null ? currentPhotos[lightboxPhotoIndex] : null} 
          photosLength={currentPhotos.length} 
          onClose={() => setLightboxPhotoIndex(null)}
          onNext={() => setLightboxPhotoIndex((prev) => (prev + 1) % currentPhotos.length)} 
          onPrev={() => setLightboxPhotoIndex((prev) => (prev - 1 + currentPhotos.length) % currentPhotos.length)}
          onDownload={() => {
            const photo = lightboxPhotoIndex !== null ? currentPhotos[lightboxPhotoIndex] : null;
            if (photo) handleDownloadPhoto(photo);
          }}
          onShare={() => {
            const photo = lightboxPhotoIndex !== null ? currentPhotos[lightboxPhotoIndex] : null;
            if (photo) handleSharePhoto(photo);
          }}
          onDelete={() => {
            const photo = lightboxPhotoIndex !== null ? currentPhotos[lightboxPhotoIndex] : null;
            if (photo) handleDeletePhotoPrompt(photo);
          }} 
        />

        {/* --- Верхняя панель навигации --- */}
        <nav className="sticky top-0 z-40 bg-white/80 dark:bg-neutral-950/80 backdrop-blur-xl border-b border-neutral-200 dark:border-neutral-900 py-4">
          <div className="max-w-7xl mx-auto px-4 sm:px-8 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-neutral-900 dark:bg-white rounded-full flex items-center justify-center">
                <LayoutGrid className="w-5 h-5 text-white dark:text-neutral-900" />
              </div>
              <h1 className="text-xl font-bold tracking-tight">Gallery.</h1>
            </div>
            
            <div className="flex items-center gap-3 sm:gap-4">
              {currentAlbum && (
                <button onClick={() => setIsUploadPhotoModalOpen(true)} className="flex items-center gap-2 px-5 py-2.5 bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-200 text-white dark:text-neutral-900 rounded-full font-medium transition-all active:scale-95 shadow-sm">
                  <Plus className="w-4 h-4" /> <span className="hidden sm:inline">Фото</span>
                </button>
              )}
              <button
                onClick={toggleTheme}
                className="p-2.5 text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white rounded-full hover:bg-neutral-100 dark:hover:bg-neutral-900 transition-colors"
                title={isDarkMode ? 'Светлая тема' : 'Темная тема'}
                aria-label={isDarkMode ? 'Переключить на светлую тему' : 'Переключить на темную тему'}
              >
                {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
              <button
                onClick={handleLogout}
                className="p-2.5 text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white rounded-full hover:bg-neutral-100 dark:hover:bg-neutral-900 transition-colors"
                title="Выход"
                aria-label="Выход"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-4 sm:px-8 py-8">
          
          {/* --- Навигация по альбомам (Чипсы - исправленные) --- */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex-1 flex items-center overflow-x-auto hide-scrollbar gap-3 pb-2 -mb-2">
              <button onClick={() => setIsCreateAlbumModalOpen(true)} className="flex-shrink-0 flex items-center justify-center w-12 h-12 rounded-full border-2 border-dashed border-neutral-300 dark:border-neutral-800 text-neutral-500 hover:text-neutral-900 dark:hover:text-white hover:border-neutral-400 dark:hover:border-neutral-600 transition-colors">
                <Plus className="w-5 h-5" />
              </button>
              
              {albums.map(album => (
                <div 
                  key={album.id} 
                  className={`flex-shrink-0 flex items-center rounded-full transition-all duration-300 border ${
                    selectedAlbumId === album.id 
                      ? 'bg-neutral-900 border-neutral-900 text-white dark:bg-white dark:border-white dark:text-neutral-900 shadow-md p-1 pl-5' 
                      : 'bg-transparent border-neutral-200 dark:border-neutral-800 text-neutral-600 dark:text-neutral-400 hover:border-neutral-400 dark:hover:border-neutral-600 px-6 py-3'
                  }`}
                >
                  <span
                    onClick={() => setSelectedAlbumId(album.id)}
                    className="font-medium cursor-pointer"
                  >
                    {album.title}
                  </span>

                  {/* Кнопки управления появляются ВНУТРИ активного альбома - надежно для мобильных */}
                  {selectedAlbumId === album.id && (
                    <div className="flex items-center gap-1 ml-3 bg-white/20 dark:bg-black/10 rounded-full p-1">
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDownloadAlbum(album); }}
                        className="p-1.5 text-white dark:text-neutral-900 hover:bg-white/30 dark:hover:bg-black/20 rounded-full transition-colors"
                        title="Скачать альбом"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); setShareModal({ isOpen: true, type: 'album', id: album.id, title: album.title }); }}
                        className="p-1.5 text-white dark:text-neutral-900 hover:bg-white/30 dark:hover:bg-black/20 rounded-full transition-colors"
                        title="Поделиться"
                      >
                        <Share2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); setDeleteConfirm({ isOpen: true, type: 'album', id: album.id, title: album.title }); }} 
                        className="p-1.5 text-red-400 dark:text-red-500 hover:bg-white/30 dark:hover:bg-black/20 rounded-full transition-colors"
                        title="Удалить"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* --- Сетка фотографий --- */}
          {!currentAlbum ? (
            <div className="py-20 text-center text-neutral-400 dark:text-neutral-600">
              <ImageIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-xl">Выберите альбом или создайте новый</p>
            </div>
          ) : currentPhotos.length === 0 ? (
            <div className="py-32 flex flex-col items-center justify-center text-center">
              <div className="w-24 h-24 rounded-full bg-neutral-100 dark:bg-neutral-900 flex items-center justify-center mb-6">
                <ImageIcon className="w-10 h-10 text-neutral-400 dark:text-neutral-600" />
              </div>
              <h3 className="text-2xl font-medium text-neutral-900 dark:text-white mb-2">Пустой альбом</h3>
              <p className="text-neutral-500 mb-8 max-w-sm">Добавьте свои первые фотографии в этот альбом, чтобы начать собирать коллекцию.</p>
              <button onClick={() => setIsUploadPhotoModalOpen(true)} className="px-8 py-3.5 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 rounded-full font-medium hover:scale-105 transition-transform shadow-lg">
                Загрузить фото
              </button>
            </div>
          ) : (
            <>
              {/* Панель управления выбором */}
              <div className="mb-6 flex items-center justify-between">
                {!isSelectionMode ? (
                  <button
                    onClick={() => setIsSelectionMode(true)}
                    className="flex items-center gap-2 px-4 py-2 text-sm text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-900 rounded-full transition-colors"
                  >
                    <CheckSquare className="w-4 h-4" />
                    Выбрать
                  </button>
                ) : (
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => {
                        setIsSelectionMode(false);
                        setSelectedPhotoIds(new Set());
                      }}
                      className="px-4 py-2 text-sm text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition-colors"
                    >
                      Отмена
                    </button>
                    <button
                      onClick={selectAllPhotos}
                      className="px-4 py-2 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
                    >
                      Выбрать все
                    </button>
                    {selectedPhotoIds.size > 0 && (
                      <>
                        <button
                          onClick={deselectAllPhotos}
                          className="px-4 py-2 text-sm text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition-colors"
                        >
                          Снять выделение
                        </button>
                        <div className="h-6 w-px bg-neutral-300 dark:bg-neutral-700" />
                        <span className="text-sm text-neutral-600 dark:text-neutral-400">
                          Выбрано: {selectedPhotoIds.size}
                        </span>
                        <button
                          onClick={handleBatchDeletePhotos}
                          className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-full text-sm font-medium transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                          Удалить ({selectedPhotoIds.size})
                        </button>
                      </>
                    )}
                  </div>
                )}
              </div>

              <div className="columns-1 sm:columns-2 lg:columns-3 xl:columns-4 gap-6 space-y-6">
              {loadingPhotos ? (
                // Показываем скелетоны во время начальной загрузки
                Array.from({ length: 6 }).map((_, i) => <PhotoSkeleton key={`skeleton-${i}`} />)
              ) : (
                currentPhotos.map((photo, index) => (
                  <PhotoCard
                    key={photo.id}
                    photo={photo}
                    index={index}
                    isLoaded={loadedPhotoIds.has(photo.id)}
                    onPhotoLoad={handlePhotoLoad}
                    onOpenIndex={handleOpenPhoto}
                    onDownloadPhoto={handleDownloadPhoto}
                    onSharePhoto={handleSharePhoto}
                    onDeletePhoto={handleDeletePhotoPrompt}
                    isSelectionMode={isSelectionMode}
                    isSelected={selectedPhotoIds.has(photo.id)}
                    onToggleSelectPhoto={handleToggleSelectPhoto}
                  />
                ))
              )}
            </div>
            </>
          )}
        </main>
      </div>

      <style dangerouslySetInnerHTML={{__html: `
        .hide-scrollbar::-webkit-scrollbar { display: none; }
        .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
      `}} />
    </div>
  );
}
