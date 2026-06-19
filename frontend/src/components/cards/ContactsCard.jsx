export default function ContactsCard({ data }) {
  const { emails = [], phones = [], socials = {} } = data
  const socialEntries = Object.entries(socials)

  return (
    <div className="card accent-top">
      <div className="card-header">
        <div className="card-icon">📧</div>
        <span className="card-title">Contact Intelligence</span>
        <span className="card-badge">
          {emails.length + phones.length} contacts found
        </span>
      </div>
      <div className="card-body">
        <div className="two-col">
          {/* Emails */}
          <div>
            <div className="sec-label">Email Addresses ({emails.length})</div>
            {emails.length > 0 ? emails.map(e => (
              <div className="contact-item" key={e}>
                <span className="contact-icon">✉</span>
                <a href={`mailto:${e}`} style={{ color: 'var(--navy)', textDecoration: 'none' }}>
                  {e}
                </a>
              </div>
            )) : (
              <div className="empty">No emails detected</div>
            )}
          </div>

          {/* Phones */}
          <div>
            <div className="sec-label">Phone Numbers ({phones.length})</div>
            {phones.length > 0 ? phones.map(p => (
              <div className="contact-item" key={p}>
                <span className="contact-icon">📞</span>
                <a href={`tel:${p}`} style={{ color: 'var(--navy)', textDecoration: 'none' }}>
                  {p}
                </a>
              </div>
            )) : (
              <div className="empty">No phones detected</div>
            )}
          </div>
        </div>

        {/* Socials */}
        {socialEntries.length > 0 && (
          <>
            <div className="divider" />
            <div className="sec-label">Social Media Profiles ({socialEntries.length})</div>
            <div className="social-grid">
              {socialEntries.map(([platform, url]) => (
                <a
                  key={platform}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="social-badge"
                >
                  {PLATFORM_ICON[platform] || '🔗'} {platform.charAt(0).toUpperCase() + platform.slice(1)}
                </a>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

const PLATFORM_ICON = {
  facebook: '📘', instagram: '📸', twitter: '🐦', linkedin: '💼',
  youtube: '▶️', tiktok: '🎵', github: '🐙', discord: '💬',
  telegram: '✈️', whatsapp: '💬', pinterest: '📌', threads: '🧵',
  bluesky: '🦋', snapchat: '👻',
}
