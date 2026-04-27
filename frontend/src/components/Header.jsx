import { Link, useLocation } from 'react-router-dom'

export default function Header() {
  const location = useLocation()

  return (
    <header className="header">
      <div className="header-inner">
        <Link to="/" className="logo">
          <span className="logo-icon">⚡</span>
          <span>CheatSheet AI</span>
        </Link>
        <nav className="nav">
          <Link
            to="/"
            className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
          >
            Home
          </Link>
          <Link
            to="/generate"
            className={`nav-link ${location.pathname === '/generate' ? 'active' : ''}`}
          >
            Generate
          </Link>
          <a
            href="/api/health"
            target="_blank"
            rel="noopener"
            className="nav-link"
          >
            API
          </a>
        </nav>
      </div>
    </header>
  )
}
