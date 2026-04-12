import React from 'react'
import '../styles/overview.css'

function Overview({ data }) {
  const formatEngagement = (rate) => {
    return (rate * 100).toFixed(2)
  }

  return (
    <div className="overview-section">
      <h2>📊 概览</h2>
      <div className="overview-cards">
        {/* Total Posts Card */}
        <div className="card post-card">
          <div className="card-icon">📝</div>
          <div className="card-content">
            <div className="card-label">发布推文</div>
            <div className="card-value">{data.total_posts}</div>
            <div className="card-period">过去 {data.period_days} 天</div>
          </div>
        </div>

        {/* Engagement Rate Card */}
        <div className="card engagement-card">
          <div className="card-icon">📈</div>
          <div className="card-content">
            <div className="card-label">平均互动率</div>
            <div className="card-value">{formatEngagement(data.avg_engagement_rate)}%</div>
            <div className="card-status">
              {data.avg_engagement_rate > 0.15
                ? '🎯 表现优秀'
                : data.avg_engagement_rate > 0.08
                ? '👍 良好'
                : '⚠️ 需要改进'}
            </div>
          </div>
        </div>

        {/* Top Niche Card */}
        <div className="card niche-card">
          <div className="card-icon">🎨</div>
          <div className="card-content">
            <div className="card-label">表现最佳Niche</div>
            <div className="card-value">{data.top_niche}</div>
            <div className="card-hint">互动率最高</div>
          </div>
        </div>

        {/* Status Card */}
        <div className="card status-card">
          <div className="card-icon">✨</div>
          <div className="card-content">
            <div className="card-label">系统状态</div>
            <div className="card-value">正常</div>
            <div className="card-status">🟢 实时同步中</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Overview
