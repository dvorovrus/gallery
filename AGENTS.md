# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

This is a single-file React photo gallery application (`gallery_app.tsx`) with album management, photo uploads, lightbox viewing, and sharing capabilities. The UI supports dark mode and uses Tailwind CSS for styling with Lucid React icons.

## Tech Stack

- **React 18+** with hooks (useState, useRef, useEffect)
- **Tailwind CSS** for styling
- **Lucid React** for icons
- **TypeScript/TSX** (single file component)
- No build system configured in repository (appears to be a standalone component)

## Architecture

### State Management
All state is managed locally with React hooks in the main `App` component:
- `albums` and `photos` arrays with initial data from `INITIAL_ALBUMS` and `INITIAL_PHOTOS`
- `selectedAlbumId` tracks current album view
- Modal states control visibility of create/upload/delete/share dialogs
- `lightboxPhotoIndex` manages photo viewer state

### Component Structure
- **App** (lines 285-499): Main component with all state and handlers
- **ModalWrapper** (lines 25-40): Reusable modal container with backdrop and close button
- **ShareModal** (lines 42-122): Generates shareable links (public or password-protected)
- **CreateAlbumModal** (lines 124-143): Album creation form
- **UploadPhotoModal** (lines 145-222): Multi-file upload with preview grid
- **DeleteConfirmModal** (lines 224-239): Confirmation dialog for deletions
- **Lightbox** (lines 242-281): Full-screen photo viewer with navigation

### Z-Index Layers
The app uses careful z-index management:
- Lightbox: `z-[60]`
- Modals: `z-[70]` (above lightbox)
- Top nav: `z-40`

### Data Flow
Photos are filtered by `selectedAlbumId` and sorted by date (newest first) at line 299. Uploaded photos use `URL.createObjectURL()` for local preview. The app maintains referential links between photos and albums via `albumId` foreign key.

## Key Features

### Album Management
- Create albums via `handleCreateAlbum` (line 303)
- Delete albums (cascade deletes all photos) via `handleDeleteAlbum` (line 311)
- Album chips show share/delete buttons only when active

### Photo Management
- Multi-file upload with live preview grid
- Each photo has: url, caption, date, albumId
- Photos sorted by date descending
- Lightbox navigation with keyboard support potential

### Sharing System
- Generates random token-based URLs
- Two access modes: public or password-protected
- Copy-to-clipboard with fallback for non-secure contexts (lines 59-68)

### Theme System
Dark mode toggle in nav bar (line 301), controlled by `isDarkMode` state and Tailwind's `dark:` classes.

## UI/UX Patterns

- **Masonry Grid**: Photos display in responsive columns layout (line 462)
- **Hover Effects**: Photo cards show overlay with actions on hover
- **Modal Animations**: Uses Tailwind's `animate-in` utilities
- **Mobile-First**: Responsive breakpoints (sm:, lg:, xl:)
- **Russian Language**: All UI text is in Russian

## Development Notes

### File Upload Handling
The `UploadPhotoModal` component:
- Accepts multiple files via hidden input (line 176)
- Creates object URLs for preview (line 159)
- Cleans up URLs on unmount (line 153)
- Resets file input after selection (line 162)

### Clipboard Copy Strategy
ShareModal implements dual clipboard strategies (lines 59-68):
1. Modern: `navigator.clipboard.writeText()` for secure contexts
2. Fallback: `document.execCommand('copy')` for older browsers

### State Reset Pattern
All modals reset their internal state when opened via `useEffect` with `isOpen` dependency, ensuring clean state on each open.

## Common Modifications

When working on this codebase:

- **Adding new modals**: Follow the ModalWrapper pattern and add z-index above existing modals
- **Adding fields to photos/albums**: Update the data interfaces and initial data constants
- **Modifying the grid**: The masonry layout is at line 462 using Tailwind's `columns-*` classes
- **Adjusting theme colors**: Look for `dark:` prefixed classes and neutral-* color values
- **Adding persistence**: Currently uses in-memory state; would need localStorage or backend API integration

## Component Communication

Parent-child communication uses callback props:
- `onClose`: Close modal
- `onCreate`: Create new item
- `onUpload`: Handle file upload
- `onConfirm`: Confirm deletion
- `onNext/onPrev`: Lightbox navigation

All event handlers are defined in the main App component and passed down.
