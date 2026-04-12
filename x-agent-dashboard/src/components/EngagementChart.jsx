import React from 'react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import '../styles/charts.css'

function EngagementChart({ data, days }) {
  // 格式化数据用于 Recharts
  const chartData = data.dates.map((date, idx) => ({
    date: formatDate(date),
    engagement: (data.engagement_rates[idx] * 100).toFixed(2),
    posts: data.post_counts[idx],
  }))

  function formatDate(isoDate) {
    const date = new Date(isoDate)
    return `${date.getMonth() + 1}/${date.getDate()}`
  }

  const avgEngagement = (
    (data.engagement_rates.reduce((a, b) => a + b, 0) / data.engagement_rates.length) * 100
  ).toFixed(2)

  const totalPosts = data.post_counts.reduce((a, b) => a + b, 0)

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>📈 互动趋势</h3>
        <div className="chart-stats">
          <span>平均互动率: {avgEngagement}%</span>
          <span>总推文数: {totalPosts}</span>
        </div>
      </div>

      {/* Combined Chart View */}
      <div className="chart-container">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis yAxisId="left" label={{ value: '互动率 (%)', angle: -90, position: 'insideLeft' }} />
            <YAxis yAxisId="right" orientation="right" label={{ value: '推文数', angle: 90, position: 'insideRight' }} />
            <Tooltip />
            <Legend />
            <Bar yAxisId="left" dataKey="engagement" name="互动率(%)" fill="#3b82f6" />
            <Bar yAxisId="right" dataKey="posts" name="推文数" fill="#10b981" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-insights">
        <h4>💡 数据洞察</h4>
        <ul>
          <li>📊 过去 {days} 天发布了 {totalPosts} 条推文</li>
          <li>📈 平均互动率: {avgEngagement}%</li>
          <li>🎯 最高互动日期: {findPeakDay(chartData)}</li>
          <li>💭 建议: {generateInsight(avgEngagement)}</li>
        </ul>
      </div>
    </div>
  )
}

function findPeakDay(data) {
  if (!data || data.length === 0) return '无数据'
  const peak = data.reduce((max, curr) =>
    parseFloat(curr.engagement) > parseFloat(max.engagement) ? curr : max
  )
  return peak.date
}

function generateInsight(avgEngagement) {
  const rate = parseFloat(avgEngagement)
  if (rate > 15) return '表现优秀！继续保持当前策略'
  if (rate > 8) return '互动率良好，可以尝试更多高互动率的Niche'
  if (rate > 5) return '互动率一般，建议优化发布时间和内容风格'
  return '互动率较低，需要大幅调整策略'
}

export default EngagementChart
