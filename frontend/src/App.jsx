import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import Home from './pages/Home'
import Generator from './pages/Generator'

export default function App() {
  return (
    <BrowserRouter>
      <Header />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/generate" element={<Generator />} />
      </Routes>
      <footer className="footer">
        <div className="container">
          <p>AI Cheatsheet Generator &bull; Powered by Gemini &bull; Built with ❤️</p>
        </div>
      </footer>
    </BrowserRouter>
  )
}
