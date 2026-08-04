import { FileText, FilePdf, FileMd, UploadSimple } from '@phosphor-icons/react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'

const DOCUMENTS = [
  { id: 1, name: 'budget_report.txt', type: 'txt', uploaded: '2026-07-28' },
  { id: 2, name: 'research_notes.md', type: 'markdown', uploaded: '2026-07-30' },
  { id: 3, name: 'onboarding_guide.pdf', type: 'pdf', uploaded: '2026-08-01' },
]

const TYPE_ICON = { txt: FileText, markdown: FileMd, pdf: FilePdf }

export default function DocumentsPage() {
  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <p className="text-sm text-ink-soft">3 documents · placeholder data, upload wired up later</p>
        <Button>
          <UploadSimple size={16} />
          Upload document
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {DOCUMENTS.map((doc) => {
          const Icon = TYPE_ICON[doc.type]
          return (
            <Card key={doc.id} tab="brass">
              <div className="flex items-start gap-3">
                <Icon size={22} weight="duotone" className="mt-0.5 text-brass" />
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-ink">{doc.name}</p>
                  <p className="mt-1 font-mono text-[11px] text-ink-soft">
                    {doc.type} · uploaded {doc.uploaded}
                  </p>
                </div>
              </div>
            </Card>
          )
        })}
      </div>
    </div>
  )
}