/**
 * 分层磨砂玻璃演示 - SmartMold Pro
 * 
 * 设计思想：
 * - 导航栏、按钮 → 磨砂质感强（variant='nav'）
 * - 正文内容 → 清晰易读（variant='content'）
 * - 平衡玻璃美感和可读性
 */

import React, { useState } from 'react';
import FrostedGlassPanel from './FrostedGlassPanel';

const StratifiedGlassDemo = () => {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');

  const TabButton = ({ id, label, icon }) => (
    <button
      onClick={() => setActiveTab(id)}
      style={{
        padding: '8px 16px',
        background: activeTab === id ? 'rgba(76, 175, 80, 0.5)' : 'rgba(255, 255, 255, 0.1)',
        border: 'none',
        borderRadius: '8px',
        color: 'white',
        cursor: 'pointer',
        fontWeight: '600',
        transition: 'all 0.3s',
        marginRight: '8px',
      }}
      onMouseEnter={(e) => {
        if (activeTab !== id) {
          e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
        }
      }}
      onMouseLeave={(e) => {
        if (activeTab !== id) {
          e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
        }
      }}
    >
      {icon} {label}
    </button>
  );

  return (
    <div
      style={{
        minHeight: '100vh',
        background: isDarkMode
          ? 'linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 50%, #0f1f3f 100%)'
          : 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        position: 'relative',
        overflow: 'hidden',
        transition: 'background 0.3s',
      }}
    >
      {/* 背景工业纹理 */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          zIndex: 0,
          background: `
            repeating-linear-gradient(90deg, transparent, transparent 60px, ${isDarkMode ? 'rgba(150, 150, 200, 0.02)' : 'rgba(200, 200, 200, 0.02)'} 60px, ${isDarkMode ? 'rgba(150, 150, 200, 0.02)' : 'rgba(200, 200, 200, 0.02)'} 70px),
            repeating-linear-gradient(0deg, transparent, transparent 40px, ${isDarkMode ? 'rgba(100, 100, 150, 0.02)' : 'rgba(150, 150, 150, 0.02)'} 40px, ${isDarkMode ? 'rgba(100, 100, 150, 0.02)' : 'rgba(150, 150, 150, 0.02)'} 45px)
          `,
          filter: 'blur(30px)',
          opacity: 0.6,
        }}
      ></div>

      {/* 工业设备背景形状 */}
      <div
        style={{
          position: 'fixed',
          top: '10%',
          left: '5%',
          width: '250px',
          height: '350px',
          background: isDarkMode
            ? 'linear-gradient(45deg, rgba(80, 100, 150, 0.15), rgba(100, 120, 180, 0.08))'
            : 'linear-gradient(45deg, rgba(100, 120, 170, 0.2), rgba(120, 150, 200, 0.1))',
          borderRadius: '20px',
          filter: 'blur(20px)',
          opacity: 0.3,
          zIndex: 1,
        }}
      ></div>

      <div
        style={{
          position: 'fixed',
          bottom: '10%',
          right: '8%',
          width: '300px',
          height: '300px',
          background: isDarkMode
            ? 'linear-gradient(-45deg, rgba(70, 100, 160, 0.12), rgba(90, 120, 170, 0.06))'
            : 'linear-gradient(-45deg, rgba(90, 120, 170, 0.15), rgba(110, 140, 190, 0.08))',
          borderRadius: '25px',
          filter: 'blur(25px)',
          opacity: 0.2,
          zIndex: 1,
        }}
      ></div>

      {/* 顶部导航栏 - 强磨砂质感 */}
      <FrostedGlassPanel
        variant="nav"
        opacity="standard"
        className="sticky top-0 z-50 rounded-none border-0 border-b"
        interactive={false}
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 50,
          width: '100%',
          borderRadius: 0,
          padding: '16px 40px',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '24px' }}>🏭</span>
            <h1 style={{ margin: 0, color: 'white', fontSize: '20px', fontWeight: 'bold' }}>
              SmartMold Pro
            </h1>
          </div>
          <button
            onClick={() => setIsDarkMode(!isDarkMode)}
            style={{
              padding: '8px 16px',
              background: 'rgba(255, 255, 255, 0.2)',
              border: 'none',
              borderRadius: '8px',
              color: 'white',
              cursor: 'pointer',
              fontWeight: '600',
            }}
          >
            {isDarkMode ? '☀️' : '🌙'}
          </button>
        </div>
      </FrostedGlassPanel>

      {/* 主容器 */}
      <div
        style={{
          position: 'relative',
          zIndex: 10,
          maxWidth: '1400px',
          margin: '0 auto',
          padding: '40px 20px',
        }}
      >
        {/* 页面标题 */}
        <div style={{ marginBottom: '40px' }}>
          <h1
            style={{
              fontSize: '40px',
              fontWeight: 'bold',
              color: 'white',
              marginBottom: '8px',
              textShadow: '0 2px 10px rgba(0, 0, 0, 0.3)',
            }}
          >
            分层玻璃效果演示
          </h1>
          <p
            style={{
              fontSize: '16px',
              color: 'rgba(255, 255, 255, 0.7)',
            }}
          >
            导航/按钮使用强磨砂质感 | 正文内容清晰易读
          </p>
        </div>

        {/* 标签栏 - 磨砂质感强 */}
        <FrostedGlassPanel
          variant="nav"
          opacity="light"
          size="fullWidth"
          label="交互面板"
          style={{
            marginBottom: '30px',
          }}
        >
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <TabButton id="dashboard" label="仪表盘" icon="📊" />
            <TabButton id="params" label="参数设置" icon="⚙️" />
            <TabButton id="alarms" label="报警管理" icon="⚠️" />
            <TabButton id="analytics" label="数据分析" icon="📈" />
          </div>
        </FrostedGlassPanel>

        {/* 内容区域 - 正文清晰 */}
        {activeTab === 'dashboard' && (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '24px',
              marginBottom: '40px',
            }}
          >
            <FrostedGlassPanel variant="content" opacity="standard" label="实时温度">
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '48px', fontWeight: 'bold', color: '#4CAF50', marginBottom: '8px' }}>
                  220°C
                </div>
                <p style={{ fontSize: '14px', opacity: 0.8, margin: 0 }}>
                  设定值: 220°C
                  <br />
                  状态: 正常
                </p>
              </div>
            </FrostedGlassPanel>

            <FrostedGlassPanel variant="content" opacity="standard" label="注射压力">
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '48px', fontWeight: 'bold', color: '#2196F3', marginBottom: '8px' }}>
                  85 MPa
                </div>
                <p style={{ fontSize: '14px', opacity: 0.8, margin: 0 }}>
                  最大压力: 100 MPa
                  <br />
                  状态: 良好
                </p>
              </div>
            </FrostedGlassPanel>

            <FrostedGlassPanel variant="content" opacity="standard" label="注射速度">
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '48px', fontWeight: 'bold', color: '#FF9800', marginBottom: '8px' }}>
                  60 mm/s
                </div>
                <p style={{ fontSize: '14px', opacity: 0.8, margin: 0 }}>
                  设定值: 60 mm/s
                  <br />
                  状态: 正常
                </p>
              </div>
            </FrostedGlassPanel>
          </div>
        )}

        {activeTab === 'params' && (
          <FrostedGlassPanel variant="content" opacity="standard" size="fullWidth">
            <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '20px', color: '#1a4d7a' }}>
              ⚙️ 工艺参数配置
            </h2>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '24px',
              }}
            >
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
                  料筒温度 (℃)
                </label>
                <input
                  type="number"
                  defaultValue={220}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid rgba(0, 0, 0, 0.2)',
                    borderRadius: '8px',
                    fontSize: '14px',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
                  注射压力 (MPa)
                </label>
                <input
                  type="number"
                  defaultValue={85}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid rgba(0, 0, 0, 0.2)',
                    borderRadius: '8px',
                    fontSize: '14px',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
                  冷却时间 (s)
                </label>
                <input
                  type="number"
                  defaultValue={25}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid rgba(0, 0, 0, 0.2)',
                    borderRadius: '8px',
                    fontSize: '14px',
                  }}
                />
              </div>
            </div>

            <div style={{ marginTop: '24px', paddingTop: '20px', borderTop: '1px solid rgba(0, 0, 0, 0.1)' }}>
              <button
                style={{
                  padding: '10px 24px',
                  background: 'linear-gradient(135deg, #4CAF50, #45a049)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  marginRight: '12px',
                }}
              >
                💾 保存
              </button>
              <button
                style={{
                  padding: '10px 24px',
                  background: 'rgba(0, 0, 0, 0.1)',
                  color: 'inherit',
                  border: '1px solid rgba(0, 0, 0, 0.2)',
                  borderRadius: '8px',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                ↺ 重置
              </button>
            </div>
          </FrostedGlassPanel>
        )}

        {activeTab === 'alarms' && (
          <FrostedGlassPanel variant="content" opacity="standard" size="fullWidth">
            <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '20px', color: '#1a4d7a' }}>
              ⚠️ 报警历史
            </h2>
            <div style={{ overflowX: 'auto' }}>
              <table
                style={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  fontSize: '14px',
                }}
              >
                <thead>
                  <tr style={{ borderBottom: '2px solid rgba(0, 0, 0, 0.1)' }}>
                    <th style={{ textAlign: 'left', padding: '12px', fontWeight: '600' }}>时间</th>
                    <th style={{ textAlign: 'left', padding: '12px', fontWeight: '600' }}>报警类型</th>
                    <th style={{ textAlign: 'left', padding: '12px', fontWeight: '600' }}>信息</th>
                    <th style={{ textAlign: 'left', padding: '12px', fontWeight: '600' }}>状态</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { time: '14:30', type: '温度过高', msg: '料筒温度超过上限', status: '已处理' },
                    { time: '13:45', type: '压力异常', msg: '注射压力波动', status: '已处理' },
                    { time: '12:15', type: '冷却超时', msg: '冷却时间过长', status: '已处理' },
                  ].map((item, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid rgba(0, 0, 0, 0.05)' }}>
                      <td style={{ padding: '12px' }}>{item.time}</td>
                      <td style={{ padding: '12px' }}>{item.type}</td>
                      <td style={{ padding: '12px', fontSize: '13px', opacity: 0.8 }}>{item.msg}</td>
                      <td style={{ padding: '12px' }}>
                        <span
                          style={{
                            background: '#e8f5e9',
                            color: '#2e7d32',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            fontSize: '12px',
                          }}
                        >
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </FrostedGlassPanel>
        )}

        {activeTab === 'analytics' && (
          <FrostedGlassPanel variant="content" opacity="standard" size="fullWidth">
            <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '20px', color: '#1a4d7a' }}>
              📈 生产统计
            </h2>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '20px',
              }}
            >
              <div
                style={{
                  padding: '16px',
                  background: 'rgba(76, 175, 80, 0.1)',
                  borderRadius: '8px',
                  border: '1px solid rgba(76, 175, 80, 0.3)',
                }}
              >
                <div style={{ fontSize: '12px', opacity: 0.7, marginBottom: '8px' }}>今日产量</div>
                <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#4CAF50' }}>2,480</div>
                <div style={{ fontSize: '12px', opacity: 0.7, marginTop: '4px' }}>件 ↑ 5% 环比</div>
              </div>

              <div
                style={{
                  padding: '16px',
                  background: 'rgba(33, 150, 243, 0.1)',
                  borderRadius: '8px',
                  border: '1px solid rgba(33, 150, 243, 0.3)',
                }}
              >
                <div style={{ fontSize: '12px', opacity: 0.7, marginBottom: '8px' }}>良品率</div>
                <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#2196F3' }}>98.7%</div>
                <div style={{ fontSize: '12px', opacity: 0.7, marginTop: '4px' }}>↑ 0.3% 环比</div>
              </div>

              <div
                style={{
                  padding: '16px',
                  background: 'rgba(255, 152, 0, 0.1)',
                  borderRadius: '8px',
                  border: '1px solid rgba(255, 152, 0, 0.3)',
                }}
              >
                <div style={{ fontSize: '12px', opacity: 0.7, marginBottom: '8px' }}>运行时长</div>
                <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#FF9800' }}>22.5h</div>
                <div style={{ fontSize: '12px', opacity: 0.7, marginTop: '4px' }}>周期 ↓ 0.2h</div>
              </div>
            </div>
          </FrostedGlassPanel>
        )}

        {/* 对比说明 */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '24px',
            marginTop: '60px',
          }}
        >
          <FrostedGlassPanel variant="nav" opacity="light" label="导航栏风格">
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px', color: '#1a4d7a' }}>
              🎯 强磨砂质感
            </h3>
            <ul style={{ fontSize: '14px', lineHeight: '1.8', paddingLeft: '20px' }}>
              <li>使用位置：导航栏、标签栏</li>
              <li>透明度：15-25%（低透明）</li>
              <li>模糊度：10-12px（高模糊）</li>
              <li>效果：突出品牌形象</li>
            </ul>
          </FrostedGlassPanel>

          <FrostedGlassPanel variant="content" opacity="standard" label="正文风格">
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px', color: '#1a4d7a' }}>
              📝 清晰易读
            </h3>
            <ul style={{ fontSize: '14px', lineHeight: '1.8', paddingLeft: '20px' }}>
              <li>使用位置：内容卡片、数据展示</li>
              <li>透明度：8-18%（高透明）</li>
              <li>模糊度：4-8px（低模糊）</li>
              <li>效果：确保文字清晰</li>
            </ul>
          </FrostedGlassPanel>

          <FrostedGlassPanel variant="content" opacity="dark" label="强调风格">
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px', color: '#1a4d7a' }}>
              ⭐ 平衡方案
            </h3>
            <ul style={{ fontSize: '14px', lineHeight: '1.8', paddingLeft: '20px' }}>
              <li>使用位置：重要信息、关键指标</li>
              <li>透明度：18%（中等透明）</li>
              <li>模糊度：8px（中等模糊）</li>
              <li>效果：兼顾美感和可读性</li>
            </ul>
          </FrostedGlassPanel>
        </div>
      </div>
    </div>
  );
};

export default StratifiedGlassDemo;
