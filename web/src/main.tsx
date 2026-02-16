import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import { StatusProvider } from './contexts/StatusContext'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <StatusProvider>
      <App />
    </StatusProvider>
  </React.StrictMode>,
)
