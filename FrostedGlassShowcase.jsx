/**
 * 高级磨砂玻璃效果演示 - SmartMold 工业设计
 * 
 * 特性展示：
 * - 工业注塑机背景（低饱和度）
 * - 真实玻璃厚度感
 * - 边缘反光效果
 * - 多层背景模糊透视
 */

import React, { useState } from 'react';
import FrostedGlassPanel from './FrostedGlassPanel';

const FrostedGlassShowcase = () => {
  const [isDarkMode, setIsDarkMode] = useState(false);

  const features = [
    {
      icon: '🔬',
      title: '真实厚度感',
      description: '多层阴影模拟真实玻璃厚度，边缘有明显的立体感',
      opacity: 'standard',
    },
    {
      icon: '✨',
      title: '高光反射',
      description: '顶部边缘高光模拟光线反射，增强真实感',
      opacity: 'light',
    },
    {
      icon: '🎯',
      title: '背景透视',
      description: '玻璃内背景清晰可见，外部背景完全模糊',
      opacity: 'standard',
    },
    {
      icon: '🏭',
      title: '工业设计',
      description: '注塑机背景低调处理，不抢内容风头',
      opacity: 'dark',
    },
  ];

  const examples = [
    {
      title: '数据监控面板',
      content: '实时注塑参数\n温度: 220°C\n压力: 85 MPa\n速度: 60 mm/s',
      opacity: 'standard',
      size: 'medium',
    },
    {
      title: '设备状态',
      content: '✓ 设备运行中\n✓ 温度正常\n⚠ 油压偏低\n✗ 报警计数: 2',
      opacity: 'dark',
      size: 'small',
    },
    {
      title: '工艺配方',
      content: '配方名称: ABS-主色\n温度曲线: 已应用\n冷却时间: 25s\n压力保压: 启用',
      opacity: 'opaque',
      size: 'medium',
    },
  ];

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
            repeating-linear-gradient(90deg, transparent, transparent 60px, ${
              isDarkMode
                ? 'rgba(150, 150, 200, 0.02)'
                : 'rgba(200, 200, 200, 0.02)'
            } 60px, ${isDarkMode ? 'rgba(150, 150, 200, 0.02)' : 'rgba(200, 200, 200, 0.02)'} 70px),
            repeating-linear-gradient(0deg, transparent, transparent 40px, ${
              isDarkMode
                ? 'rgba(100, 100, 150, 0.02)'
                : 'rgba(150, 150, 150, 0.02)'
            } 40px, ${isDarkMode ? 'rgba(100, 100, 150, 0.02)' : 'rgba(150, 150, 150, 0.02)'} 45px),
            radial-gradient(circle at 30% 50%, ${
              isDarkMode
                ? 'rgba(100, 120, 180, 0.1)'
                : 'rgba(100, 150, 200, 0.15)'
            }, transparent 60%)
          `,
          filter: 'blur(30px)',
          opacity: 0.6,
        }}
      ></div>

      {/* 工业设备形状 - 不显眼 */}
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

      {/* 主容器 */}
      <div
        style={{
          position: 'relative',
          zIndex: 10,
          maxWidth: '1200px',
          margin: '0 auto',
          padding: '60px 20px',
        }}
      >
        {/* 标题 */}
        <div style={{ textAlign: 'center', marginBottom: '80px' }}>
          <h1
            style={{
              fontSize: '48px',
              fontWeight: 'bold',
              color: isDarkMode ? '#ffffff' : '#ffffff',
              marginBottom: '16px',
              textShadow: isDarkMode
                ? '0 2px 10px rgba(0, 0, 0, 0.5)'
                : '0 2px 10px rgba(0, 0, 0, 0.3)',
            }}
          >
            高级磨砂玻璃效果
          </h1>
          <p
            style={{
              fontSize: '18px',
              color: isDarkMode
                ? 'rgba(255, 255, 255, 0.7)'
                : 'rgba(255, 255, 255, 0.8)',
            }}
          >
            工业设计 · 真实厚度感 · 背景透视 · 完美反光
          </p>
        </div>

        {/* 特性展示 */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '24px',
            marginBottom: '80px',
          }}
        >
          {features.map((feature, idx) => (
            <FrostedGlassPanel
              key={idx}
              opacity={feature.opacity}
              size="medium"
              label={feature.title}
            >
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '40px', marginBottom: '12px' }}>
                  {feature.icon}
                </div>
                <h3
                  style={{
                    fontSize: '18px',
                    fontWeight: '600',
                    marginBottom: '12px',
                    color: isDarkMode ? '#2d5f8f' : '#1a4d7a',
                  }}
                >
                  {feature.title}
                </h3>
                <p
                  style={{
                    fontSize: '14px',
                    lineHeight: '1.6',
                    color: isDarkMode
                      ? 'rgba(200, 200, 200, 0.7)'
                      : 'rgba(30, 40, 70, 0.8)',
                  }}
                >
                  {feature.description}
                </p>
              </div>
            </FrostedGlassPanel>
          ))}
        </div>

        {/* 实际应用示例 */}
        <div style={{ marginBottom: '60px' }}>
          <h2
            style={{
              fontSize: '32px',
              fontWeight: 'bold',
              marginBottom: '30px',
              color: isDarkMode ? '#ffffff' : '#ffffff',
              textShadow: isDarkMode
                ? '0 2px 8px rgba(0, 0, 0, 0.5)'
                : '0 2px 8px rgba(0, 0, 0, 0.3)',
            }}
          >
            💡 工业应用场景
          </h2>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '24px',
            }}
          >
            {examples.map((example, idx) => (
              <FrostedGlassPanel
                key={idx}
                opacity={example.opacity}
                size={example.size}
                label={example.title}
              >
                <div
                  style={{
                    color: isDarkMode
                      ? 'rgba(200, 200, 200, 0.85)'
                      : 'rgba(30, 40, 70, 0.85)',
                    lineHeight: '1.8',
                    fontSize: '14px',
                    fontFamily: 'monospace',
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {example.content}
                </div>
              </FrostedGlassPanel>
            ))}
          </div>
        </div>

        {/* 技术对比表 */}
        <FrostedGlassPanel opacity="standard" size="fullWidth">
          <h2
            style={{
              fontSize: '24px',
              fontWeight: '600',
              marginBottom: '20px',
              color: isDarkMode ? '#2d5f8f' : '#1a4d7a',
            }}
          >
            📊 透明度对比
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
                <tr
                  style={{
                    borderBottom: `2px solid ${
                      isDarkMode
                        ? 'rgba(255, 255, 255, 0.15)'
                        : 'rgba(0, 0, 0, 0.1)'
                    }`,
                  }}
                >
                  <th
                    style={{
                      padding: '12px',
                      textAlign: 'left',
                      fontWeight: '600',
                      color: isDarkMode
                        ? 'rgba(255, 255, 255, 0.8)'
                        : 'rgba(30, 40, 70, 0.85)',
                    }}
                  >
                    透明度等级
                  </th>
                  <th
                    style={{
                      padding: '12px',
                      textAlign: 'left',
                      fontWeight: '600',
                      color: isDarkMode
                        ? 'rgba(255, 255, 255, 0.8)'
                        : 'rgba(30, 40, 70, 0.85)',
                    }}
                  >
                    透明度
                  </th>
                  <th
                    style={{
                      padding: '12px',
                      textAlign: 'left',
                      fontWeight: '600',
                      color: isDarkMode
                        ? 'rgba(255, 255, 255, 0.8)'
                        : 'rgba(30, 40, 70, 0.85)',
                    }}
                  >
                    最佳使用场景
                  </th>
                  <th
                    style={{
                      padding: '12px',
                      textAlign: 'left',
                      fontWeight: '600',
                      color: isDarkMode
                        ? 'rgba(255, 255, 255, 0.8)'
                        : 'rgba(30, 40, 70, 0.85)',
                    }}
                  >
                    特点
                  </th>
                </tr>
              </thead>
              <tbody>
                {[
                  {
                    level: 'Light 超透明',
                    opacity: '15%',
                    scene: '导航栏、背景容器',
                    feature: '最高透视感',
                  },
                  {
                    level: 'Standard 标准',
                    opacity: '25%',
                    scene: '普通卡片、对话框',
                    feature: '最平衡',
                  },
                  {
                    level: 'Dark 低透明',
                    opacity: '35%',
                    scene: '强调内容、重要信息',
                    feature: '高对比度',
                  },
                  {
                    level: 'Opaque 超低透明',
                    opacity: '45%',
                    scene: '核心操作、表单',
                    feature: '最清晰',
                  },
                ].map((row, idx) => (
                  <tr
                    key={idx}
                    style={{
                      borderBottom: `1px solid ${
                        isDarkMode
                          ? 'rgba(255, 255, 255, 0.05)'
                          : 'rgba(0, 0, 0, 0.05)'
                      }`,
                      backgroundColor: idx % 2 === 0 ? 'transparent' : undefined,
                    }}
                  >
                    <td
                      style={{
                        padding: '12px',
                        color: isDarkMode
                          ? 'rgba(200, 200, 200, 0.85)'
                          : 'rgba(30, 40, 70, 0.85)',
                      }}
                    >
                      {row.level}
                    </td>
                    <td
                      style={{
                        padding: '12px',
                        fontFamily: 'monospace',
                        color: '#4CAF50',
                        fontWeight: '600',
                      }}
                    >
                      {row.opacity}
                    </td>
                    <td
                      style={{
                        padding: '12px',
                        color: isDarkMode
                          ? 'rgba(200, 200, 200, 0.85)'
                          : 'rgba(30, 40, 70, 0.85)',
                      }}
                    >
                      {row.scene}
                    </td>
                    <td
                      style={{
                        padding: '12px',
                        color: isDarkMode
                          ? 'rgba(200, 200, 200, 0.85)'
                          : 'rgba(30, 40, 70, 0.85)',
                      }}
                    >
                      {row.feature}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </FrostedGlassPanel>
      </div>

      {/* 主题切换按钮 */}
      <button
        onClick={() => setIsDarkMode(!isDarkMode)}
        style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          padding: '12px 20px',
          background: 'rgba(255, 255, 255, 0.2)',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          borderRadius: '20px',
          color: 'white',
          fontWeight: '600',
          cursor: 'pointer',
          backdropFilter: 'blur(10px)',
          zIndex: 200,
          transition: 'all 0.3s',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = 'rgba(255, 255, 255, 0.3)';
          e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.5)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
          e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.3)';
        }}
      >
        {isDarkMode ? '☀️ 浅色' : '🌙 深色'}
      </button>
    </div>
  );
};

export default FrostedGlassShowcase;
