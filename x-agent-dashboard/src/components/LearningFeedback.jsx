import React, { useState } from 'react'
import '../styles/feedback.css'

function LearningFeedback({ data }) {
  const [expandedId, setExpandedId] = useState(null)

  if (!data || !data.feedbacks || data.feedbacks.length === 0) {
    return (
      <div className="feedback-card">
        <h3>🧠 学习反馈</h3>
        <div className="no-feedback">
          <p>✨ 暂无学习反馈，您的策略已优化！</p>
        </div>
      </div>
    )
  }

  const highEngagement = data.feedbacks.filter((f) => f.feedback_type === 'high_engagement')
  const lowEngagement = data.feedbacks.filter((f) => f.feedback_type === 'low_engagement')
  const pending = data.feedbacks.filter((f) => !f.applied)

  return (
    <div className="feedback-card">
      <div className="feedback-header">
        <h3>🧠 学习反馈与优化建议</h3>
        <div className="feedback-stats">
          <span className="badge pending">{data.total_pending} 条待应用</span>
          <span className="badge high">↑ {highEngagement.length} 高互动</span>
          <span className="badge low">↓ {lowEngagement.length} 低互动</span>
        </div>
      </div>

      {/* Pending Feedbacks (Priority) */}
      {pending.length > 0 && (
        <div className="feedback-section">
          <h4>📌 需要关注</h4>
          <div className="feedback-list">
            {pending.slice(0, 3).map((feedback) => (
              <FeedbackItem
                key={feedback.id}
                feedback={feedback}
                isExpanded={expandedId === feedback.id}
                onToggle={() =>
                  setExpandedId(expandedId === feedback.id ? null : feedback.id)
                }
              />
            ))}
          </div>
        </div>
      )}

      {/* High Engagement Feedbacks */}
      {highEngagement.length > 0 && (
        <div className="feedback-section">
          <h4>🎯 高互动内容</h4>
          <div className="feedback-list">
            {highEngagement.slice(0, 3).map((feedback) => (
              <FeedbackItem
                key={feedback.id}
                feedback={feedback}
                variant="success"
                isExpanded={expandedId === feedback.id}
                onToggle={() =>
                  setExpandedId(expandedId === feedback.id ? null : feedback.id)
                }
              />
            ))}
          </div>
        </div>
      )}

      {/* Low Engagement Feedbacks */}
      {lowEngagement.length > 0 && (
        <div className="feedback-section">
          <h4>⚠️ 低互动内容</h4>
          <div className="feedback-list">
            {lowEngagement.slice(0, 3).map((feedback) => (
              <FeedbackItem
                key={feedback.id}
                feedback={feedback}
                variant="warning"
                isExpanded={expandedId === feedback.id}
                onToggle={() =>
                  setExpandedId(expandedId === feedback.id ? null : feedback.id)
                }
              />
            ))}
          </div>
        </div>
      )}

      <div className="feedback-actions">
        <button className="btn btn-primary">📋 应用所有建议</button>
        <button className="btn btn-secondary">📊 查看完整报告</button>
      </div>
    </div>
  )
}

function FeedbackItem({ feedback, variant = 'default', isExpanded, onToggle }) {
  const getIcon = (type) => {
    switch (type) {
      case 'high_engagement':
        return '🎯'
      case 'low_engagement':
        return '⚠️'
      default:
        return '💡'
    }
  }

  const getTypeLabel = (type) => {
    switch (type) {
      case 'high_engagement':
        return '高互动'
      case 'low_engagement':
        return '低互动'
      default:
        return '建议'
    }
  }

  return (
    <div className={`feedback-item feedback-${variant}`}>
      <div className="feedback-header-item" onClick={onToggle}>
        <div className="feedback-icon">{getIcon(feedback.feedback_type)}</div>
        <div className="feedback-content">
          <div className="feedback-niche">
            <strong>{feedback.niche}</strong>
            <span className="feedback-type">{getTypeLabel(feedback.feedback_type)}</span>
            <span className="feedback-rate">
              互动率: {(feedback.engagement_rate * 100).toFixed(2)}%
            </span>
          </div>
          <div className="feedback-reason">{feedback.adjustment_reason}</div>
        </div>
        <div className="feedback-toggle">{isExpanded ? '▼' : '▶'}</div>
      </div>

      {isExpanded && (
        <div className="feedback-details">
          <div className="detail-row">
            <span className="label">Niche:</span>
            <span className="value">{feedback.niche}</span>
          </div>
          <div className="detail-row">
            <span className="label">互动率:</span>
            <span className="value">{(feedback.engagement_rate * 100).toFixed(2)}%</span>
          </div>
          <div className="detail-row">
            <span className="label">状态:</span>
            <span className="value">{feedback.applied ? '✅ 已应用' : '⏳ 待应用'}</span>
          </div>
          <div className="detail-row">
            <span className="label">详情:</span>
            <span className="value">{feedback.adjustment_reason}</span>
          </div>
          <div className="detail-actions">
            {!feedback.applied && (
              <button className="btn btn-sm btn-primary">✅ 应用此建议</button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default LearningFeedback
