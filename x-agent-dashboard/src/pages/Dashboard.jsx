import React, { useState, useEffect } from 'react'
import axios from 'axios'
import Overview from '../components/Overview'
import EngagementChart from '../components/EngagementChart'
import NicheComparison from '../components/NicheComparison'
import LearningFeedback from '../components/LearningFeedback'
import '../styles/dashboard.css'

const API_BASE = process.env.VITE_API_BASE_URL || 'http://localhost:8000'

function Dashboard() {
  const [days, setDays] = useState(7)
  const [overview, setOverview] = useState(null)
  const [timeline, setTimeline] = useState(null)
  const [niche, setNiche] = useState(null)
  const [feedback, setFeedback] = useState(null)
  const [loading, setLoading] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)

  const loadData = async () => {
    setLoading(true)
    try {
      const [ov, tl, n, fb] = await Promise.all([
        axios.get(`${API_BASE}/dashboard/overview?days=${days}`),
        axios.get(`${API_BASE}/dashboard/engagement-timeline?days=${days}`),
        axios.get(`${API_BASE}/dashboard/niche-comparison?days=${days}`),
        axios.get(`${API_BASE}/dashboard/learning-feedback?limit=5`),
      ])

      setOverview(ov.data)
      setTimeline(tl.data)
      setNiche(n.data)
      setFeedback(fb.data)
      setLastUpdate(new Date().toLocaleTimeString('zh-CN'))
    } catch (error) {
      console.error('数据加载失败:', error)
      alert(`加载失败: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [days])

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <h1>🚀 X-Agent 运营仪表板</h1>
        <div className="header-controls">
          <select
            value={days}
            onChange={(e) => setDays(parseInt(e.target.value))}
            className="period-selector"
          >
            <option value={7}>过去 7 天</option>
            <option value={14}>过去 14 天</option>
            <option value={30}>过去 30 天</option>
            <option value={60}>过去 60 天</option>
            <option value={90}>过去 90 天</option>
          </select>

          <button
            onClick={loadData}
            disabled={loading}
            className="refresh-btn"
          >
            {loading ? '⏳ 加载中...' : '🔄 刷新'}
          </button>

          {lastUpdate && (
            <span className="last-update">最后更新: {lastUpdate}</span>
          )}
        </div>
      </header>

      {/* Loading State */}
      {loading && (
        <div className="loading-overlay">
          <div className="spinner"></div>
        </div>
      )}

      {/* Main Content */}
      <main className="dashboard-content">
        {/* Overview Cards */}
        {overview && <Overview data={overview} />}

        {/* Charts Grid */}
        <div className="charts-grid">
          {timeline && <EngagementChart data={timeline} days={days} />}
          {niche && <NicheComparison data={niche} days={days} />}
        </div>

        {/* Learning Feedback */}
        {feedback && <LearningFeedback data={feedback} />}
      </main>

      {/* Footer */}
      <footer className="dashboard-footer">
        <p>X-Agent v2.0 | Phase 2: Web Dashboard & Feedback Loop</p>
      </footer>
    </div>
  )
}

export default Dashboard
