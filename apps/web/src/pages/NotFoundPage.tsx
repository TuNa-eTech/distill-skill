export function NotFoundPage() {
  return (
    <div className="empty-state">
      <div className="empty-state__card">
        <span className="micro-badge">Not found</span>
        <h2>This route is outside the current dashboard surface.</h2>
        <p>
          Start from Overview, Pipeline, or Review while the internal operator
          shell is still being built out.
        </p>
      </div>
    </div>
  )
}
