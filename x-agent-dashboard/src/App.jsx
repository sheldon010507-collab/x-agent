import React, { useState, useEffect } from 'react'
import axios from 'axios'
import Dashboard from './pages/Dashboard'
import './App.css'

const API_BASE = process.env.VITE_API_BASE_URL || 'http://localhost:8000'

function App() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [apiReady, setApiReady] = useState(false)

  useEffect(() => {
    // 检查 API 是否就绪
    const checkAPI = async () => {
      try {
        const response = await axios.get(`${API_BASE}/health`, { timeout: 5000 })
        if (response.data.status === 'ok') {
          setApiReady(true)
          setError(null)
        }
      } catch (err) {
        setError(`无法连接到 API: ${err.message}`)
        console.error('API 连接失败:', err)
      } finally {
        setLoading(false)
      }
    }

    checkAPI()
  }, [])

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>正在加载仪表板...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>⚠️ 错误</h2>
        <p>{error}</p>
        <p className="hint">请确保 X-Agent API 正在运行 (http://localhost:8000)</p>
      </div>
    )
  }

  if (!apiReady) {
    return (
      <div className="error-container">
        <h2>API 未就绪</h2>
        <p>仪表板需要连接到 X-Agent API</p>
      </div>
    )
  }

  return <Dashboard />
}

export default App
