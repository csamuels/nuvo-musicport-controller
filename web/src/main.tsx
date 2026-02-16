import React from 'react'
import ReactDOM from 'react-dom/client'
import AppTabs from './AppTabs.tsx'
import { StatusProvider } from './contexts/StatusContext'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <StatusProvider>
      <AppTabs />
    </StatusProvider>
  </React.StrictMode>,
)
