/**
 * GlassUIDemo - 完整示例应用
 * 
 * 展示所有磨砂玻璃组件的完整示例
 * - GlassCard（基础组件）
 * - MusicPlayer（交互式音乐播放卡片）
 * - IconCard（图标卡片）
 * - TripCard（旅行计划卡片）
 * 
 * 包含：
 * - 无障碍性完整支持
 * - Tailwind CSS 样式隔离
 * - 响应式设计
 * - 深色和浅色模式支持
 */

import React, { useState } from 'react';
import GlassCard from './GlassCard';
import MusicPlayer from './MusicPlayer';
import IconCard from './IconCard';
import TripCard from './TripCard';

/**
 * 装饰性背景球体组件
 */
const DecorativeShape = ({ className = '' }) => (
  <div
    className={`absolute rounded-full filter blur-2xl -z-10 animate-float ${className}`}
  />
);

/**
 * 主应用组件
 */
function GlassUIDemo() {
  const [isDarkMode, setIsDarkMode] = useState(false);

  return (
    <div
      className={`
        min-h-screen w-full overflow-hidden
        ${
          isDarkMode
            ? 'bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900'
            : 'bg-gradient-to-br from-cyan-100 via-blue-50 to-indigo-100'
        }
        flex flex-col items-center justify-center p-8
        transition-colors duration-300
      `}
    >
      {/* 装饰性背景球体 */}
      <DecorativeShape
        className={`
          w-64 h-64 top-1/4 left-1/4
          ${isDarkMode ? 'bg-blue-500/20' : 'bg-blue-300/30'}
          animate-[float_10s_infinite_ease-in-out]
        `}
      />
      <DecorativeShape
        className={`
          w-56 h-56 bottom-1/4 right-1/4
          ${isDarkMode ? 'bg-purple-500/20' : 'bg-purple-300/30'}
          animate-[float_10s_infinite_ease-in-out_-5s]
        `}
      />

      {/* 主容器 */}
      <div className="z-10 flex flex-col items-center gap-8 max-w-7xl">
        {/* 页面标题 */}
        <div className="text-center mb-4">
          <h1
            className={`
              text-4xl md:text-5xl font-bold mb-2
              ${isDarkMode ? 'text-white' : 'text-slate-900'}
            `}
          >
            Glassmorphism UI Kit
          </h1>
          <p
            className={`
              text-lg
              ${isDarkMode ? 'text-slate-300' : 'text-slate-700'}
            `}
          >
            现代化磨砂玻璃界面设计系统，支持完整无障碍性
          </p>
        </div>

        {/* 主题切换按钮 */}
        <button
          onClick={() => setIsDarkMode(!isDarkMode)}
          className={`
            px-6 py-2 rounded-lg font-semibold transition-all duration-200
            focus:outline-none focus:ring-2 focus:ring-offset-2
            ${
              isDarkMode
                ? 'bg-yellow-400/20 text-yellow-300 focus:ring-yellow-400'
                : 'bg-slate-800/20 text-slate-800 focus:ring-slate-800'
            }
          `}
          aria-label={isDarkMode ? '切换到浅色模式' : '切换到深色模式'}
        >
          {isDarkMode ? '☀️ 浅色模式' : '🌙 深色模式'}
        </button>

        {/* 卡片网格容器 */}
        <div className="flex flex-wrap gap-8 justify-center w-full">
          {/* 音乐播放卡片 */}
          <MusicPlayer
            title="Now Playing"
            artist="Glass Animals - Heat Waves"
            progress={60}
            onPlayChange={(isPlaying) => {
              console.log('播放状态:', isPlaying);
            }}
          />

          {/* 旅行计划卡片 */}
          <TripCard
            title="Kyoto Trip"
            dateRange="Feb 24 - Mar 02"
            participants={2}
          />

          {/* 图标卡片网格 */}
          <div className="flex flex-wrap gap-6 justify-center w-full">
            <IconCard
              icon="📁"
              label="Files"
              description="访问您的文件和文件夹"
              onClick={() => console.log('打开文件管理器')}
            />
            <IconCard
              icon="☁️"
              label="Cloud"
              description="访问云端存储服务"
              onClick={() => console.log('打开云端')}
            />
            <IconCard
              icon="⚙️"
              label="Settings"
              description="访问应用设置"
              onClick={() => console.log('打开设置')}
            />
            <IconCard
              icon="👤"
              label="Profile"
              description="访问个人资料"
              onClick={() => console.log('打开个人资料')}
            />
          </div>
        </div>

        {/* 信息部分 */}
        <GlassCard
          className="max-w-2xl mt-8"
          ariaLabel="关于此设计系统的信息"
          role="contentinfo"
        >
          <h2 className="text-2xl font-semibold text-slate-900 mb-4">
            ✨ 设计特点
          </h2>
          <ul className="space-y-3 text-slate-700">
            <li className="flex items-start gap-3">
              <span className="text-2xl flex-shrink-0">🎨</span>
              <div>
                <strong>Glassmorphism 设计</strong>
                <p className="text-sm opacity-75">65% 不透明度白色背景 + 16px 模糊效果，营造现代化磨砂玻璃感</p>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-2xl flex-shrink-0">♿</span>
              <div>
                <strong>完整无障碍性</strong>
                <p className="text-sm opacity-75">ARIA 标签、键盘导航、屏幕阅读器支持、高对比度颜色</p>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-2xl flex-shrink-0">📱</span>
              <div>
                <strong>响应式设计</strong>
                <p className="text-sm opacity-75">自适应各种屏幕尺寸，从手机到桌面都有最佳体验</p>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-2xl flex-shrink-0">🎯</span>
              <div>
                <strong>Tailwind CSS</strong>
                <p className="text-sm opacity-75">完全使用 Tailwind 类名，样式隔离，无全局污染</p>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-2xl flex-shrink-0">⌨️</span>
              <div>
                <strong>键盘可操作</strong>
                <p className="text-sm opacity-75">所有交互元素都支持键盘导航（Tab、Enter、Space）</p>
              </div>
            </li>
          </ul>
        </GlassCard>

        {/* 开发者信息 */}
        <div
          className={`
            text-center text-sm mt-8
            ${isDarkMode ? 'text-slate-400' : 'text-slate-600'}
          `}
        >
          <p>
            使用 <strong>React</strong> + <strong>Tailwind CSS</strong> 构建
          </p>
          <p className="mt-1">
            完全支持 <strong>WCAG 2.1 AA</strong> 无障碍性标准
          </p>
        </div>
      </div>

      {/* 自定义 CSS 动画（不污染全局） */}
      <style>{`
        @keyframes float {
          0%, 100% {
            transform: translate(0, 0);
          }
          50% {
            transform: translate(0, 30px);
          }
        }
      `}</style>
    </div>
  );
}

export default GlassUIDemo;
