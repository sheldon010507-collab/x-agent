import React from 'react'
import {
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

function NicheComparison({ data, days }) {
  // 格式化数据用于 Recharts
  const chartData = data.niches.map((niche, idx) => ({
    name: niche,
    engagement: (data.avg_engagement_rates[idx] * 100).toFixed(2),
    likes: data.avg_likes[idx].toFixed(0),
    posts: data.post_counts[idx],
  }))

  // 找出最佳和最差的 Niche
  const sortedByEngagement = [...chartData].sort(
    (a, b) => parseFloat(b.engagement) - parseFloat(a.engagement)
  )

  const best = sortedByEngagement[0]
  const worst = sortedByEngagement[sortedByEngagement.length - 1]

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>🎨 Niche 语气对标</h3>
        <div className="chart-stats">
          <span>📊 {data.niches.length} 种语气</span>
          <span>📈 过去 {days} 天</span>
        </div>
      </div>

      {/* Bar Chart */}
      <div className="chart-container">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis label={{ value: '互动率 (%)', angle: -90, position: 'insideLeft' }} />
            <Tooltip
              formatter={(value) => {
                if (typeof value === 'string') return value + '%'
                return value
              }}
            />
            <Legend />
            <Bar dataKey="engagement" name="互动率(%)" fill="#8b5cf6" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Rankings */}
      <div className="niche-rankings">
        <div className="ranking-column">
          <h4>🏆 表现最好</h4>
          {best && (
            <div className="ranking-item best">
              <div className="ranking-name">{best.name}</div>
              <div className="ranking-value">{best.engagement}%</div>
              <div className="ranking-posts">{best.posts} 条推文</div>
            </div>
          )}
        </div>

        <div className="ranking-column">
          <h4>⚠️ 需要改进</h4>
          {worst && (
            <div className="ranking-item worst">
              <div className="ranking-name">{worst.name}</div>
              <div className="ranking-value">{worst.engagement}%</div>
              <div className="ranking-posts">{worst.posts} 条推文</div>
            </div>
          )}
        </div>

        <div className="ranking-column">
          <h4>📊 详细数据</h4>
          <div className="ranking-table">
            <table>
              <thead>
                <tr>
                  <th>Niche</th>
                  <th>互动率</th>
                  <th>平均赞</th>
                </tr>
              </thead>
              <tbody>
                {chartData.slice(0, 5).map((item) => (
                  <tr key={item.name}>
                    <td>{item.name}</td>
                    <td className="highlight">{item.engagement}%</td>
                    <td>{item.likes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="chart-insights">
        <h4>💡 建议</h4>
        <ul>
          <li>✅ 下次优先使用 <strong>{best?.name}</strong> 语气</li>
          <li>❌ 减少使用 <strong>{worst?.name}</strong> 语气</li>
          <li>🧪 考虑对低互动率的Niche进行A/B测试</li>
        </ul>
      </div>
    </div>
  )
}

export default NicheComparison
