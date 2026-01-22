/**
 * Glassmorphism 透明度变体演示组件
 * 
 * 展示所有支持的透明度变体及其应用场景
 * - light (45%) - 导航栏、背景容器
 * - standard (65%) - 普通卡片（默认）
 * - dark (85%) - 强调卡片
 * - opaque (95%) - 核心操作、表单
 */

import React, { useState } from 'react';
import GlassCard from './GlassCard';

const GlassTransparencyDemo = () => {
  const [isDarkMode, setIsDarkMode] = useState(false);

  const opacityVariants = [
    {
      name: '超透明度',
      value: 'light',
      percentage: '45%',
      emoji: '🌫️',
      useCase: '导航栏、背景容器、浮层',
      description: '最高的透视感，允许背景完全可见',
      color: 'from-blue-400 to-cyan-300',
    },
    {
      name: '标准透明度',
      value: 'standard',
      percentage: '65%',
      emoji: '📊',
      useCase: '内容卡片、主要内容块',
      description: '最平衡的选择，兼顾透视感和可读性',
      color: 'from-green-400 to-emerald-300',
    },
    {
      name: '低透明度',
      value: 'dark',
      percentage: '85%',
      emoji: '🔒',
      useCase: '强调卡片、重要内容',
      description: '较低的透视感，提供更好的对比度',
      color: 'from-purple-400 to-pink-300',
    },
    {
      name: '超低透明度',
      value: 'opaque',
      percentage: '95%',
      emoji: '⭐',
      useCase: '核心操作、表单、CTA',
      description: '接近不透明，确保内容清晰易读',
      color: 'from-orange-400 to-red-300',
    },
  ];

  const sceneCards = [
    {
      icon: '🧭',
      title: '导航栏',
      opacity: 'light',
      description: '超透明度让用户看到背景内容',
    },
    {
      icon: '📂',
      title: '侧边栏',
      opacity: 'light',
      description: '浮在内容上方，不抢焦点',
    },
    {
      icon: '📱',
      title: '产品卡片',
      opacity: 'standard',
      description: '标准选择，最平衡的效果',
    },
    {
      icon: '🎪',
      title: '弹出菜单',
      opacity: 'standard',
      description: '清晰的玻璃感和可读性',
    },
    {
      icon: '📌',
      title: '强调区域',
      opacity: 'dark',
      description: '低透明度突显内容',
    },
    {
      icon: '⚡',
      title: '关键信息',
      opacity: 'dark',
      description: '提升深度感和优雅度',
    },
    {
      icon: '🎯',
      title: '操作按钮',
      opacity: 'opaque',
      description: '需要立即关注的核心内容',
    },
    {
      icon: '📋',
      title: '表单页面',
      opacity: 'opaque',
      description: '数据输入需要高对比度',
    },
  ];

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
  };

  return (
    <div className={isDarkMode ? 'dark' : ''}>
      {/* 背景 */}
      <div
        className={`min-h-screen transition-colors duration-300 ${
          isDarkMode
            ? 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900'
            : 'bg-gradient-to-br from-sky-100 via-blue-50 to-indigo-100'
        }`}
      >
        {/* 装饰形状 */}
        <div
          className={`fixed inset-0 overflow-hidden pointer-events-none ${
            isDarkMode ? 'opacity-20' : 'opacity-30'
          }`}
        >
          <div className="absolute top-10 left-20 w-72 h-72 rounded-full blur-3xl bg-blue-400"></div>
          <div className="absolute bottom-10 right-20 w-96 h-96 rounded-full blur-3xl bg-purple-400 animate-float"></div>
        </div>

        {/* 导航栏 */}
        <GlassCard
          opacity="light"
          className={`sticky top-0 z-50 flex justify-between items-center rounded-none border-0 border-b ${
            isDarkMode
              ? 'border-white/10 bg-slate-900/35'
              : 'border-white/20 bg-white/35'
          }`}
          interactive={false}
        >
          <div className="flex items-center gap-4">
            <span className="text-2xl">🎨</span>
            <h1
              className={`text-xl font-bold ${
                isDarkMode ? 'text-white' : 'text-slate-900'
              }`}
            >
              Glassmorphism 透明度变体
            </h1>
          </div>
          <button
            onClick={toggleTheme}
            className={`px-4 py-2 rounded-lg font-semibold transition-all ${
              isDarkMode
                ? 'bg-white/20 text-white hover:bg-white/30'
                : 'bg-white/40 text-slate-900 hover:bg-white/60'
            }`}
          >
            {isDarkMode ? '☀️ 浅色' : '🌙 深色'}
          </button>
        </GlassCard>

        {/* 主容器 */}
        <div className="relative z-10 max-w-6xl mx-auto px-6 py-20">
          {/* 标题区域 */}
          <div className="text-center mb-20">
            <h2
              className={`text-5xl font-bold mb-6 ${
                isDarkMode ? 'text-white' : 'text-slate-900'
              }`}
            >
              透明度变体演示
            </h2>
            <p
              className={`text-xl ${
                isDarkMode ? 'text-slate-300' : 'text-slate-600'
              }`}
            >
              根据不同场景选择合适的透明度，打造完美的视觉层级
            </p>
          </div>

          {/* 四种透明度演示 */}
          <div className="mb-20">
            <h3
              className={`text-3xl font-bold mb-12 ${
                isDarkMode ? 'text-white' : 'text-slate-900'
              }`}
            >
              四种透明度等级
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {opacityVariants.map((variant) => (
                <GlassCard
                  key={variant.value}
                  opacity={variant.value}
                  className="relative overflow-hidden group"
                >
                  {/* 透明度标签 */}
                  <div className="absolute top-3 right-3 bg-gradient-to-r from-green-400 to-emerald-300 text-white px-3 py-1 rounded-lg text-xs font-bold">
                    {variant.percentage}
                  </div>

                  {/* 内容 */}
                  <div className="pt-4">
                    <div className="text-4xl mb-4">{variant.emoji}</div>
                    <h4
                      className={`text-lg font-bold mb-2 ${
                        isDarkMode ? 'text-white' : 'text-slate-900'
                      }`}
                    >
                      {variant.name}
                    </h4>
                    <p
                      className={`text-sm mb-3 ${
                        isDarkMode ? 'text-slate-300' : 'text-slate-600'
                      }`}
                    >
                      {variant.description}
                    </p>
                    <p
                      className={`text-xs font-semibold uppercase tracking-wide ${
                        isDarkMode ? 'text-slate-400' : 'text-slate-500'
                      }`}
                    >
                      💡 使用场景: {variant.useCase}
                    </p>
                  </div>
                </GlassCard>
              ))}
            </div>
          </div>

          {/* 应用场景 */}
          <div className="mb-20">
            <h3
              className={`text-3xl font-bold mb-12 ${
                isDarkMode ? 'text-white' : 'text-slate-900'
              }`}
            >
              实际应用场景
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {sceneCards.map((card, idx) => (
                <GlassCard
                  key={idx}
                  opacity={card.opacity}
                  className="text-center"
                >
                  <div className="text-3xl mb-3">{card.icon}</div>
                  <h4
                    className={`text-base font-bold mb-2 ${
                      isDarkMode ? 'text-white' : 'text-slate-900'
                    }`}
                  >
                    {card.title}
                  </h4>
                  <p
                    className={`text-sm ${
                      isDarkMode ? 'text-slate-300' : 'text-slate-600'
                    }`}
                  >
                    {card.description}
                  </p>
                </GlassCard>
              ))}
            </div>
          </div>

          {/* 对比表格 */}
          <div>
            <h3
              className={`text-3xl font-bold mb-8 ${
                isDarkMode ? 'text-white' : 'text-slate-900'
              }`}
            >
              详细对比
            </h3>
            <GlassCard opacity="standard" className="overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr
                      className={`border-b ${
                        isDarkMode
                          ? 'border-white/20 bg-white/5'
                          : 'border-white/40 bg-white/30'
                      }`}
                    >
                      <th className="text-left py-4 px-4 font-bold">透明度</th>
                      <th className="text-left py-4 px-4 font-bold">百分比</th>
                      <th className="text-left py-4 px-4 font-bold">适用场景</th>
                      <th className="text-left py-4 px-4 font-bold">特点</th>
                    </tr>
                  </thead>
                  <tbody>
                    {opacityVariants.map((variant, idx) => (
                      <tr
                        key={variant.value}
                        className={`border-b ${
                          isDarkMode
                            ? 'border-white/10 hover:bg-white/5'
                            : 'border-white/20 hover:bg-white/20'
                        } transition-colors`}
                      >
                        <td className="py-4 px-4 font-semibold">
                          {variant.emoji} {variant.name}
                        </td>
                        <td className="py-4 px-4 font-mono text-green-500">
                          {variant.percentage}
                        </td>
                        <td className="py-4 px-4">{variant.useCase}</td>
                        <td className="py-4 px-4 text-sm opacity-80">
                          {variant.description}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </GlassCard>
          </div>

          {/* 使用建议 */}
          <div className="mt-20">
            <h3
              className={`text-3xl font-bold mb-8 ${
                isDarkMode ? 'text-white' : 'text-slate-900'
              }`}
            >
              💡 使用建议
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <GlassCard opacity="light">
                <h4 className={`text-lg font-bold mb-3 ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>
                  何时选择超透明 (45%)
                </h4>
                <ul className={`text-sm space-y-2 ${isDarkMode ? 'text-slate-300' : 'text-slate-600'}`}>
                  <li>✓ 导航栏和顶部菜单</li>
                  <li>✓ 背景容器和布局框架</li>
                  <li>✓ 浮动效果元素</li>
                  <li>✓ 需要高透视感的场景</li>
                </ul>
              </GlassCard>

              <GlassCard opacity="standard">
                <h4 className={`text-lg font-bold mb-3 ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>
                  何时选择标准 (65%)
                </h4>
                <ul className={`text-sm space-y-2 ${isDarkMode ? 'text-slate-300' : 'text-slate-600'}`}>
                  <li>✓ 内容卡片和容器</li>
                  <li>✓ 产品展示和介绍</li>
                  <li>✓ 弹出菜单和对话框</li>
                  <li>✓ 大多数常规UI元素</li>
                </ul>
              </GlassCard>

              <GlassCard opacity="dark">
                <h4 className={`text-lg font-bold mb-3 ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>
                  何时选择低透明 (85%)
                </h4>
                <ul className={`text-sm space-y-2 ${isDarkMode ? 'text-slate-300' : 'text-slate-600'}`}>
                  <li>✓ 强调和突显内容</li>
                  <li>✓ 特殊功能说明</li>
                  <li>✓ 重要信息展示</li>
                  <li>✓ 需要更好对比度的场景</li>
                </ul>
              </GlassCard>

              <GlassCard opacity="opaque">
                <h4 className={`text-lg font-bold mb-3 ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>
                  何时选择超低透明 (95%)
                </h4>
                <ul className={`text-sm space-y-2 ${isDarkMode ? 'text-slate-300' : 'text-slate-600'}`}>
                  <li>✓ 核心操作和CTA按钮</li>
                  <li>✓ 表单和数据输入</li>
                  <li>✓ 关键信息展示</li>
                  <li>✓ 需要最高可读性的内容</li>
                </ul>
              </GlassCard>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GlassTransparencyDemo;
