import { useState, useEffect } from 'react'
import {
  Users,
  FileText,
  ChatCircleDots,
  Lightning,
  WarningCircle,
  Database,
  ArrowClockwise,
  MagnifyingGlass,
  CheckCircle,
  ShieldCheck,
  Funnel,
  CaretDown,
  Cards,
  NotePencil,
  Brain,
} from '@phosphor-icons/react'
import { fetchAdminMetrics, fetchAdminLogs } from '../services/adminService'

export default function AdminDashboardPage() {
  const [metrics, setMetrics] = useState(null)
  const [logs, setLogs] = useState([])
  const [loadingMetrics, setLoadingMetrics] = useState(true)
  const [loadingLogs, setLoadingLogs] = useState(true)
  const [error, setError] = useState(null)

  // Log filters
  const [logLevel, setLogLevel] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedLogIdx, setExpandedLogIdx] = useState(null)
  const [activeTab, setActiveTab] = useState('overview') // 'overview' | 'logs'

  useEffect(() => {
    loadAll()
  }, [])

  useEffect(() => {
    if (activeTab === 'logs') {
      loadLogs()
    }
  }, [logLevel, activeTab])

  async function loadAll() {
    setError(null)
    await Promise.all([loadMetrics(), loadLogs()])
  }

  async function loadMetrics() {
    setLoadingMetrics(true)
    try {
      const data = await fetchAdminMetrics()
      setMetrics(data)
    } catch (err) {
      setError(err.message || 'Failed to load metrics.')
    } finally {
      setLoadingMetrics(false)
    }
  }

  async function loadLogs() {
    setLoadingLogs(true)
    try {
      const res = await fetchAdminLogs({ level: logLevel, search: searchQuery })
      setLogs(res.logs || [])
    } catch (err) {
      console.error('Failed to load logs', err)
    } finally {
      setLoadingLogs(false)
    }
  }

  function handleSearchSubmit(e) {
    e.preventDefault()
    loadLogs()
  }

  const kpis = metrics?.kpis
  const activity = metrics?.activity_chart || []
  const toolDist = metrics?.tool_distribution || []
  const latencyList = metrics?.latency_breakdown || []
  const statusDist = metrics?.status_distribution || { '2xx': 0, '4xx': 0, '5xx': 0 }

  const totalStatusCalls = (statusDist['2xx'] || 0) + (statusDist['4xx'] || 0) + (statusDist['5xx'] || 0)
  const maxDayRequests = Math.max(...activity.map((d) => d.requests || 0), 1)
  const totalToolCalls = toolDist.reduce((acc, t) => acc + (t.count || 0), 0)

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-mist pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <h1 className="font-display italic text-2xl text-ink">System Observability & Admin</h1>
          </div>
          <p className="font-mono text-xs text-ink-soft mt-0.5">
            Production health metrics, AI agent latency, vector store, and structured execution logs
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex rounded-tab border border-mist bg-paper-dim p-0.5">
            <button
              onClick={() => setActiveTab('overview')}
              className={`rounded-tab-sm px-3 py-1 font-mono text-xs transition-colors ${
                activeTab === 'overview' ? 'bg-paper text-ink shadow-xs font-medium' : 'text-ink-soft hover:text-ink'
              }`}
            >
              Overview & Charts
            </button>
            <button
              onClick={() => setActiveTab('logs')}
              className={`rounded-tab-sm px-3 py-1 font-mono text-xs transition-colors ${
                activeTab === 'logs' ? 'bg-paper text-ink shadow-xs font-medium' : 'text-ink-soft hover:text-ink'
              }`}
            >
              System Logs ({logs.length})
            </button>
          </div>

          <button
            onClick={loadAll}
            disabled={loadingMetrics || loadingLogs}
            className="flex items-center gap-1.5 rounded-tab border border-mist bg-paper px-3 py-1.5 font-mono text-xs text-ink hover:bg-paper-dim transition-colors"
            title="Refresh metrics and logs"
          >
            <ArrowClockwise size={14} className={loadingMetrics || loadingLogs ? 'animate-spin' : ''} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-tab border border-rose-200 bg-rose-50 p-4 text-xs font-mono text-rose-800 flex items-center gap-2">
          <WarningCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Cards Row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Total Users */}
        <div className="rounded-tab border border-mist bg-paper-dim p-3.5 space-y-1">
          <div className="flex items-center justify-between text-ink-soft">
            <span className="font-mono text-[11px] uppercase tracking-wider">Users</span>
            <Users size={16} />
          </div>
          <div className="font-display italic text-2xl text-ink">{kpis?.total_users ?? '—'}</div>
          <div className="font-mono text-[10px] text-ink-soft">Active accounts</div>
        </div>

        {/* Documents & Vectors */}
        <div className="rounded-tab border border-mist bg-paper-dim p-3.5 space-y-1">
          <div className="flex items-center justify-between text-ink-soft">
            <span className="font-mono text-[11px] uppercase tracking-wider">Documents</span>
            <FileText size={16} />
          </div>
          <div className="font-display italic text-2xl text-ink">{kpis?.total_documents ?? '—'}</div>
          <div className="font-mono text-[10px] text-emerald-700 flex items-center gap-1">
            <Database size={12} />
            <span>{kpis?.total_indexed_chunks ?? 0} vectors</span>
          </div>
        </div>

        {/* Notes & Memories */}
        <div className="rounded-tab border border-mist bg-paper-dim p-3.5 space-y-1">
          <div className="flex items-center justify-between text-ink-soft">
            <span className="font-mono text-[11px] uppercase tracking-wider">Notes & Facts</span>
            <NotePencil size={16} />
          </div>
          <div className="font-display italic text-2xl text-ink">{kpis?.total_notes ?? '—'}</div>
          <div className="font-mono text-[10px] text-ink-soft">{kpis?.total_memories ?? 0} facts learned</div>
        </div>

        {/* Flashcards */}
        <div className="rounded-tab border border-mist bg-paper-dim p-3.5 space-y-1">
          <div className="flex items-center justify-between text-ink-soft">
            <span className="font-mono text-[11px] uppercase tracking-wider">Flashcards</span>
            <Cards size={16} />
          </div>
          <div className="font-display italic text-2xl text-ink">{kpis?.total_flashcards ?? '—'}</div>
          <div className="font-mono text-[10px] text-ink-soft">{kpis?.total_flashcard_sets ?? 0} generated sets</div>
        </div>

        {/* Messages */}
        <div className="rounded-tab border border-mist bg-paper-dim p-3.5 space-y-1">
          <div className="flex items-center justify-between text-ink-soft">
            <span className="font-mono text-[11px] uppercase tracking-wider">Messages</span>
            <ChatCircleDots size={16} />
          </div>
          <div className="font-display italic text-2xl text-ink">{kpis?.total_messages ?? '—'}</div>
          <div className="font-mono text-[10px] text-ink-soft">{kpis?.total_conversations ?? 0} chat threads</div>
        </div>

        {/* Average Latency */}
        <div className="rounded-tab border border-mist bg-paper-dim p-3.5 space-y-1">
          <div className="flex items-center justify-between text-ink-soft">
            <span className="font-mono text-[11px] uppercase tracking-wider">Avg Latency</span>
            <Lightning size={16} className="text-brass" />
          </div>
          <div className="font-display italic text-2xl text-ink">{kpis?.avg_latency_ms ? `${kpis.avg_latency_ms}ms` : '—'}</div>
          <div className="font-mono text-[10px] text-ink-soft">Error: {kpis?.error_rate_percent ?? 0}%</div>
        </div>
      </div>

      {/* TAB 1: OVERVIEW & CHARTS */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Main 2-column Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left 2 Cols: Activity Volume Trend */}
            <div className="lg:col-span-2 rounded-tab border border-mist bg-paper-dim p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-mono text-xs font-semibold text-ink uppercase tracking-wider">
                    Activity & Request Volume (Last 7 Days)
                  </h3>
                  <p className="font-mono text-[11px] text-ink-soft">Total API requests and chat interactions</p>
                </div>
                <div className="flex items-center gap-3 font-mono text-[10px]">
                  <span className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-brass" /> Requests
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-ledger" /> Messages
                  </span>
                </div>
              </div>

              {/* Bar visualization */}
              <div className="h-44 flex items-end gap-3 pt-6 border-b border-mist">
                {activity.map((item, idx) => {
                  const reqHeight = Math.max(Math.round((item.requests / maxDayRequests) * 100), 6)
                  return (
                    <div key={idx} className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end group">
                      <div className="w-full flex items-end justify-center gap-1 h-32">
                        {/* Requests Bar */}
                        <div
                          style={{ height: `${reqHeight}%` }}
                          className="w-1/2 bg-brass/80 hover:bg-brass rounded-t-xs transition-all relative"
                          title={`${item.requests} requests`}
                        >
                          <span className="absolute -top-6 left-1/2 -translate-x-1/2 font-mono text-[9px] bg-ink text-paper px-1 py-0.5 rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity">
                            {item.requests}
                          </span>
                        </div>
                        {/* Messages Bar */}
                        <div
                          style={{ height: `${Math.max(Math.min(item.messages * 8, 100), item.messages ? 8 : 0)}%` }}
                          className="w-1/2 bg-ledger/70 hover:bg-ledger rounded-t-xs transition-all"
                          title={`${item.messages} messages`}
                        />
                      </div>
                      <span className="font-mono text-[10px] text-ink-soft">{item.date}</span>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Right 1 Col: Tool Usage Distribution */}
            <div className="rounded-tab border border-mist bg-paper-dim p-5 space-y-4">
              <div>
                <h3 className="font-mono text-xs font-semibold text-ink uppercase tracking-wider">
                  AI Agent Tool Invocations
                </h3>
                <p className="font-mono text-[11px] text-ink-soft">Tools triggered by LangGraph autonomous agent</p>
              </div>

              <div className="space-y-3 pt-2">
                {toolDist.map((t, idx) => {
                  const pct = totalToolCalls > 0 ? Math.round((t.count / totalToolCalls) * 100) : 0
                  return (
                    <div key={idx} className="space-y-1">
                      <div className="flex items-center justify-between font-mono text-xs">
                        <span className="text-ink truncate max-w-[160px]">{t.tool}</span>
                        <span className="text-ink-soft">{t.count} ({pct}%)</span>
                      </div>
                      <div className="h-1.5 w-full bg-mist rounded-full overflow-hidden">
                        <div
                          style={{ width: `${Math.max(pct, t.count > 0 ? 5 : 0)}%` }}
                          className="h-full bg-brass rounded-full transition-all"
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Lower 2-column Grid: Endpoints Latency & Infrastructure Specs */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Latency by Endpoint */}
            <div className="rounded-tab border border-mist bg-paper-dim p-5 space-y-3">
              <h3 className="font-mono text-xs font-semibold text-ink uppercase tracking-wider">
                Endpoint Latency Breakdown
              </h3>
              <div className="divide-y divide-mist text-xs font-mono">
                {latencyList.map((ep, i) => (
                  <div key={i} className="flex items-center justify-between py-2">
                    <span className="text-ink truncate max-w-[280px]">{ep.path}</span>
                    <div className="flex items-center gap-3 text-ink-soft">
                      <span>{ep.count} reqs</span>
                      <span className={`font-semibold ${ep.avg_ms > 1000 ? 'text-amber-700' : 'text-emerald-700'}`}>
                        {ep.avg_ms}ms
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Architecture & Cloud Health */}
            <div className="rounded-tab border border-mist bg-paper-dim p-5 space-y-3">
              <h3 className="font-mono text-xs font-semibold text-ink uppercase tracking-wider">
                Cloud Architecture & Free Tier Status
              </h3>
              <div className="space-y-2.5 font-mono text-xs">
                <div className="flex items-center justify-between border-b border-mist pb-2">
                  <span className="text-ink-soft">Vector Database</span>
                  <span className="font-semibold text-ink flex items-center gap-1">
                    <CheckCircle size={14} className="text-emerald-600" />
                    {kpis?.vector_db ?? 'Pinecone Serverless'}
                  </span>
                </div>
                <div className="flex items-center justify-between border-b border-mist pb-2">
                  <span className="text-ink-soft">Hosted Embeddings</span>
                  <span className="font-semibold text-ink">Google text-embedding-004 (0 MB RAM)</span>
                </div>
                <div className="flex items-center justify-between border-b border-mist pb-2">
                  <span className="text-ink-soft">Background Worker</span>
                  <span className="font-semibold text-ink">Celery + Upstash Redis (Dual-mode)</span>
                </div>
                <div className="flex items-center justify-between border-b border-mist pb-2">
                  <span className="text-ink-soft">PostgreSQL Storage</span>
                  <span className="font-semibold text-ink">Neon Serverless (0.5 GB Free)</span>
                </div>
                <div className="flex items-center justify-between pt-1">
                  <span className="text-ink-soft">HTTP Status Codes</span>
                  <div className="flex items-center gap-2">
                    <span className="text-emerald-700 font-semibold">{statusDist['2xx']} (2xx)</span>
                    <span className="text-amber-700 font-semibold">{statusDist['4xx']} (4xx)</span>
                    <span className="text-rose-700 font-semibold">{statusDist['5xx']} (5xx)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: SYSTEM LOGS VIEWER */}
      {activeTab === 'logs' && (
        <div className="rounded-tab border border-mist bg-paper-dim p-5 space-y-4">
          {/* Controls Bar */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
            {/* Level Filter Pills */}
            <div className="flex items-center gap-1.5">
              <span className="font-mono text-xs text-ink-soft mr-1 flex items-center gap-1">
                <Funnel size={14} /> Level:
              </span>
              {['', 'INFO', 'WARNING', 'ERROR'].map((lvl) => (
                <button
                  key={lvl}
                  onClick={() => setLogLevel(lvl)}
                  className={`rounded-tab-sm px-2.5 py-1 font-mono text-xs transition-colors ${
                    logLevel === lvl
                      ? 'bg-ink text-paper font-medium'
                      : 'border border-mist bg-paper text-ink-soft hover:text-ink'
                  }`}
                >
                  {lvl || 'ALL'}
                </button>
              ))}
            </div>

            {/* Search Input */}
            <form onSubmit={handleSearchSubmit} className="flex items-center gap-2">
              <div className="relative flex-1 sm:w-64">
                <MagnifyingGlass size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-soft" />
                <input
                  type="text"
                  placeholder="Search log messages…"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-tab border border-mist bg-paper pl-8 pr-3 py-1 font-mono text-xs text-ink placeholder:text-ink-soft/50 focus:border-brass focus:outline-hidden"
                />
              </div>
              <button
                type="submit"
                className="rounded-tab border border-mist bg-paper px-3 py-1 font-mono text-xs text-ink hover:bg-paper-dim"
              >
                Filter
              </button>
            </form>
          </div>

          {/* Log Table / List */}
          {loadingLogs ? (
            <div className="flex items-center justify-center py-12 font-mono text-xs text-ink-soft gap-2">
              <ArrowClockwise size={16} className="animate-spin" />
              Loading system logs…
            </div>
          ) : logs.length === 0 ? (
            <div className="py-12 text-center font-mono text-xs text-ink-soft">
              No log records found matching the current filter.
            </div>
          ) : (
            <div className="divide-y divide-mist border border-mist rounded-tab bg-paper overflow-hidden font-mono text-xs">
              {logs.map((record, index) => {
                const isExpanded = expandedLogIdx === index
                const lvl = (record.level || 'INFO').toUpperCase()
                const badgeColor =
                  lvl === 'ERROR'
                    ? 'bg-rose-100 text-rose-800 border-rose-200'
                    : lvl === 'WARNING'
                    ? 'bg-amber-100 text-amber-800 border-amber-200'
                    : 'bg-paper-dim text-ink-soft border-mist'

                return (
                  <div key={index} className="hover:bg-paper-dim/40 transition-colors">
                    <div
                      onClick={() => setExpandedLogIdx(isExpanded ? null : index)}
                      className="p-3 flex items-start sm:items-center justify-between gap-3 cursor-pointer"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center gap-2 min-w-0 flex-1">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border ${badgeColor}`}>
                          {lvl}
                        </span>
                        <span className="text-[11px] text-ink-soft shrink-0">
                          {record.timestamp ? new Date(record.timestamp).toLocaleTimeString() : '—'}
                        </span>
                        <span className="text-ink-soft shrink-0 max-w-[140px] truncate text-[11px]">
                          [{record.logger || 'app'}]
                        </span>
                        <span className="text-ink truncate flex-1 font-medium">
                          {record.message || 'Log event'}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        {record.duration_ms && (
                          <span className="text-ink-soft text-[11px]">{record.duration_ms}ms</span>
                        )}
                        <CaretDown size={14} className={`text-ink-soft transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="px-4 pb-4 pt-1 bg-paper-dim/60 border-t border-mist/50 space-y-2 text-[11px]">
                        {record.exception && (
                          <div>
                            <span className="font-semibold text-rose-800">Stack Trace:</span>
                            <pre className="mt-1 p-2.5 rounded bg-paper border border-rose-200 text-rose-900 overflow-x-auto whitespace-pre-wrap font-mono text-[10px]">
                              {record.exception}
                            </pre>
                          </div>
                        )}
                        <div>
                          <span className="font-semibold text-ink">Structured Metadata:</span>
                          <pre className="mt-1 p-2.5 rounded bg-paper border border-mist text-ink-soft overflow-x-auto font-mono text-[10px]">
                            {JSON.stringify(record, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
