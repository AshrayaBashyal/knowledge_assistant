import { useCallback, useRef, useState } from 'react'
import { FileText, FilePdf, UploadSimple, Trash, DownloadSimple, WarningCircle } from '@phosphor-icons/react'
import { FileMd } from '@phosphor-icons/react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Spinner from '../components/ui/Spinner'
import Alert from '../components/ui/Alert'
import EmptyState from '../components/ui/EmptyState'
import ConfirmDialog from '../components/ui/ConfirmDialog'
import SkeletonCards from '../components/ui/SkeletonCards'
import IndexButton from '../components/ui/IndexButton'
import { useResourceList } from '../hooks/useResourceList'
import { useToast } from '../lib/ToastContext'
import { getErrorMessage } from '../lib/errors'
import { fetchDocuments, uploadDocument, deleteDocument, downloadDocument } from '../services/documentsService'
import { triggerDocumentIndex, fetchDocumentIndexStatus } from '../services/retrievalService'
import { ALLOWED_DOCUMENT_EXTENSIONS, MAX_DOCUMENT_UPLOAD_MB } from '../lib/env'

const TYPE_ICON = {
  pdf: FilePdf,
  markdown: FileMd,
  txt: FileText,
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function DocumentsPage() {
  const { items: docs, setItems: setDocs, loading, error, reload } = useResourceList(
    useCallback(() => fetchDocuments(), [])
  )
  const { notify } = useToast()
  const fileInputRef = useRef(null)

  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [toDelete, setToDelete] = useState(null) // the document pending deletion
  const [deleting, setDeleting] = useState(false)

  async function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (!fileInputRef.current) return
    fileInputRef.current.value = ''
    if (!file) return

    // Validate extension client-side before even hitting the network.
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!ALLOWED_DOCUMENT_EXTENSIONS.includes(ext)) {
      setUploadError(`Unsupported file type. Allowed: ${ALLOWED_DOCUMENT_EXTENSIONS.join(', ')}`)
      return
    }
    if (file.size > MAX_DOCUMENT_UPLOAD_MB * 1024 * 1024) {
      setUploadError(`File too large. Maximum size is ${MAX_DOCUMENT_UPLOAD_MB} MB.`)
      return
    }

    setUploadError(null)
    setUploading(true)
    try {
      const newDoc = await uploadDocument(file)
      setDocs((prev) => [newDoc, ...prev])
      notify(`"${file.name}" uploaded.`, { variant: 'success' })
    } catch (err) {
      setUploadError(getErrorMessage(err))
    } finally {
      setUploading(false)
    }
  }

  async function handleDelete() {
    if (!toDelete) return
    setDeleting(true)
    try {
      await deleteDocument(toDelete.id)
      setDocs((prev) => prev.filter((d) => d.id !== toDelete.id))
      notify(`"${toDelete.original_filename}" deleted.`, { variant: 'success' })
      setToDelete(null)
    } catch (err) {
      notify(getErrorMessage(err), { variant: 'error' })
    } finally {
      setDeleting(false)
    }
  }

  async function handleDownload(doc) {
    try {
      const response = await downloadDocument(doc.id)
      if (!response.ok) throw new Error('Download failed')
      const blob = await response.blob()
      // Trigger the browser's save dialog by creating a temporary <a>.
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = doc.original_filename
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      notify(getErrorMessage(err), { variant: 'error' })
    }
  }

  return (
    <div>
      {/* hidden file input, triggered by the Upload button */}
      <input
        ref={fileInputRef}
        type="file"
        accept={ALLOWED_DOCUMENT_EXTENSIONS.join(',')}
        className="hidden"
        onChange={handleFileChange}
      />

      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-ink-soft">
          {loading ? 'Loading…' : `${docs.length} document${docs.length !== 1 ? 's' : ''}`}
        </p>
        <Button onClick={() => fileInputRef.current?.click()} disabled={uploading}>
          {uploading ? <Spinner size={15} /> : <UploadSimple size={16} />}
          {uploading ? 'Uploading…' : 'Upload document'}
        </Button>
      </div>

      {uploadError && (
        <Alert variant="error" className="mb-4">{uploadError}</Alert>
      )}

      {error && !loading && (
        <Alert variant="error" className="mb-4">
          Could not load documents. <button onClick={reload} className="underline">Retry</button>
        </Alert>
      )}

      {loading && <SkeletonCards count={3} />}

      {!loading && !error && docs.length === 0 && (
        <EmptyState
          icon={<FileText size={40} />}
          title="No documents yet"
          hint={`Upload a .pdf, .md, or .txt file (up to ${MAX_DOCUMENT_UPLOAD_MB} MB) to get started.`}
          action={
            <Button onClick={() => fileInputRef.current?.click()}>
              <UploadSimple size={16} /> Upload document
            </Button>
          }
        />
      )}

      {!loading && docs.length > 0 && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {docs.map((doc) => {
            const Icon = TYPE_ICON[doc.file_type] ?? FileText
            return (
              <Card key={doc.id} tab="brass" className="group">
                <div className="flex items-start gap-3">
                  <Icon size={22} weight="duotone" className="mt-0.5 shrink-0 text-brass" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-ink">{doc.original_filename}</p>
                    <p className="mt-1 font-mono text-[11px] text-ink-soft">
                      {doc.file_type} · {formatDate(doc.uploaded_at)}
                    </p>
                    <div className="mt-2">
                      <IndexButton
                        onTrigger={() => triggerDocumentIndex(doc.id)}
                        onPoll={() => fetchDocumentIndexStatus(doc.id)}
                        initialStatus={null}
                      />
                    </div>
                  </div>
                  <div className="flex shrink-0 gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                    <button
                      onClick={() => handleDownload(doc)}
                      className="rounded-tab p-1.5 text-ink-soft hover:text-ink"
                      title="Download"
                    >
                      <DownloadSimple size={16} />
                    </button>
                    <button
                      onClick={() => setToDelete(doc)}
                      className="rounded-tab p-1.5 text-ink-soft hover:text-crimson"
                      title="Delete"
                    >
                      <Trash size={16} />
                    </button>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      )}

      {toDelete && (
        <ConfirmDialog
          title="Delete document"
          message={`"${toDelete.original_filename}" will be permanently deleted. This cannot be undone.`}
          onConfirm={handleDelete}
          onCancel={() => setToDelete(null)}
          busy={deleting}
        />
      )}
    </div>
  )
}