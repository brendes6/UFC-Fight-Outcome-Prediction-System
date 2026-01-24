import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { getRoot } from './components/Call.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App getRoot={getRoot} />
  </StrictMode>,
)
