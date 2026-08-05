export default function Field({ label, error, ...inputProps }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-ink">{label}</span>
      <input
        className={`w-full rounded-tab border bg-paper px-3 py-2 text-sm text-ink placeholder:text-ink-soft focus:outline-none focus:ring-1 ${
          error ? 'border-crimson focus:ring-crimson' : 'border-mist focus:ring-ledger'
        }`}
        {...inputProps}
      />
      {error && <span className="mt-1 block text-xs text-crimson">{error}</span>}
    </label>
  )
}