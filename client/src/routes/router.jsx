import { createBrowserRouter } from 'react-router-dom'
import AppShell from '../components/layout/AppShell'
import ChatPage from '../pages/ChatPage'
import DocumentsPage from '../pages/DocumentsPage'
import NotesPage from '../pages/NotesPage'
import MemoryPage from '../pages/MemoryPage'
import SearchPage from '../pages/SearchPage'
import FlashcardsPage from '../pages/FlashcardsPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <ChatPage />, handle: { title: 'Chat' } },
      { path: 'documents', element: <DocumentsPage />, handle: { title: 'Documents' } },
      { path: 'notes', element: <NotesPage />, handle: { title: 'Notes' } },
      { path: 'memory', element: <MemoryPage />, handle: { title: 'Memory' } },
      { path: 'search', element: <SearchPage />, handle: { title: 'Search' } },
      { path: 'flashcards', element: <FlashcardsPage />, handle: { title: 'Flashcards' } },
    ],
  },
])