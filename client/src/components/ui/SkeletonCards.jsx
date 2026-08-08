// Pulse-animated placeholder cards. Used instead of a centered spinner so
// the page layout doesn't shift when real content arrives - the skeleton
// occupies roughly the same space as the cards it's standing in for.
export default function SkeletonCards({ count = 3, className = '' }) {
  return (
    <div className={`grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 ${className}`}>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="animate-pulse rounded-card border border-mist bg-paper pl-5 pr-4 py-4"
        >
          <div className="flex items-start gap-3">
            <div className="mt-0.5 h-5 w-5 rounded bg-mist" />
            <div className="flex-1 space-y-2">
              <div className="h-3.5 w-3/4 rounded bg-mist" />
              <div className="h-3 w-1/2 rounded bg-mist" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}