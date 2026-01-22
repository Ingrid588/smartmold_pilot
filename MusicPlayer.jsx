/**
 * MusicPlayer 组件 - 交互式音乐播放卡片
 * 
 * 功能特点：
 * - 播放/暂停状态管理（useState）
 * - 进度条可视化
 * - 完整的无障碍性支持（ARIA）
 * - 键盘导航支持（Space/Enter 控制播放）
 * 
 * @component
 * @example
 * <MusicPlayer 
 *   title="Glass Animals - Heat Waves"
 *   progress={60}
 * />
 */

import React, { useState, useRef } from 'react';
import PropTypes from 'prop-types';
import GlassCard from './GlassCard';

/**
 * 音乐播放卡片
 * 
 * @param {Object} props - 组件 props
 * @param {string} [props.title='Now Playing'] - 卡片标题
 * @param {string} [props.artist='Glass Animals - Heat Waves'] - 艺术家和曲名
 * @param {number} [props.progress=60] - 初始进度百分比 (0-100)
 * @param {Function} [props.onPlayChange] - 播放状态变化回调
 * @returns {React.ReactElement} 音乐播放卡片
 */
const MusicPlayer = React.forwardRef(
  (
    {
      title = 'Now Playing',
      artist = 'Glass Animals - Heat Waves',
      progress = 60,
      onPlayChange,
    },
    ref
  ) => {
    // 状态管理
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentProgress, setCurrentProgress] = useState(progress);
    const buttonRef = useRef(null);

    /**
     * 处理播放/暂停按钮点击
     */
    const handlePlayToggle = () => {
      setIsPlaying(!isPlaying);
      onPlayChange?.(!isPlaying);
      
      // 无障碍性：获取焦点以便键盘用户知道状态已更改
      buttonRef.current?.focus();
    };

    /**
     * 处理键盘事件（Space/Enter 控制播放）
     */
    const handleKeyDown = (e) => {
      if (e.code === 'Space' || e.code === 'Enter') {
        e.preventDefault();
        handlePlayToggle();
      }
    };

    /**
     * 处理进度条点击
     */
    const handleProgressClick = (e) => {
      const progressBar = e.currentTarget;
      const rect = progressBar.getBoundingClientRect();
      const newProgress = Math.round(
        ((e.clientX - rect.left) / rect.width) * 100
      );
      setCurrentProgress(Math.max(0, Math.min(100, newProgress)));
    };

    return (
      <GlassCard
        ref={ref}
        variant="large"
        className="w-80"
        ariaLabel="音乐播放控制面板"
        role="region"
      >
        {/* 音乐图标 */}
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-white/90 to-white/40 flex items-center justify-center text-2xl mb-4 shadow-sm">
          🎵
        </div>

        {/* 标题和艺术家信息 */}
        <h2 className="text-lg font-semibold text-slate-900 mb-2">
          {title}
        </h2>
        <p className="text-sm text-slate-700 opacity-80 mb-4 leading-relaxed">
          {artist}
        </p>

        {/* 进度条 - 无障碍性支持 */}
        <div
          className="relative h-1 bg-slate-200/50 rounded-full mb-6 overflow-hidden cursor-pointer group"
          onClick={handleProgressClick}
          role="progressbar"
          aria-label="音乐进度"
          aria-valuenow={currentProgress}
          aria-valuemin="0"
          aria-valuemax="100"
          tabIndex="0"
          onKeyDown={handleKeyDown}
        >
          {/* 进度填充 */}
          <div
            className="absolute h-full bg-gradient-to-r from-blue-400 to-blue-500 rounded-full transition-all duration-200 ease-out"
            style={{ width: `${currentProgress}%` }}
            aria-hidden="true"
          />

          {/* 进度条上的滑块（增强可访问性） */}
          <div
            className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-blue-500 rounded-full shadow-md opacity-0 group-hover:opacity-100 transition-opacity duration-200"
            style={{ left: `${currentProgress}%`, transform: 'translate(-50%, -50%)' }}
            aria-hidden="true"
          />
        </div>

        {/* 播放/暂停按钮 - 完整无障碍性 */}
        <button
          ref={buttonRef}
          onClick={handlePlayToggle}
          onKeyDown={handleKeyDown}
          className={`
            w-full py-2.5 px-5 mt-5 border-none rounded-xl font-semibold
            text-white cursor-pointer transition-all duration-200 ease-in-out
            focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-400
            active:scale-95
            ${
              isPlaying
                ? 'bg-gradient-to-r from-green-400 to-green-500 shadow-lg shadow-green-400/30 hover:shadow-xl hover:shadow-green-400/40'
                : 'bg-gradient-to-r from-blue-400 to-blue-600 shadow-lg shadow-blue-400/30 hover:shadow-xl hover:shadow-blue-400/40'
            }
          `}
          aria-pressed={isPlaying}
          aria-label={isPlaying ? '暂停播放' : '开始播放'}
        >
          {isPlaying ? (
            <>
              <span className="mr-2">⏸</span>
              暂停
            </>
          ) : (
            <>
              <span className="mr-2">▶</span>
              播放
            </>
          )}
        </button>

        {/* 隐藏的状态指示器（用于屏幕阅读器） */}
        <div className="sr-only" aria-live="polite" aria-atomic="true">
          {isPlaying ? '正在播放' : '已暂停'}
        </div>
      </GlassCard>
    );
  }
);

MusicPlayer.displayName = 'MusicPlayer';

MusicPlayer.propTypes = {
  title: PropTypes.string,
  artist: PropTypes.string,
  progress: PropTypes.number,
  onPlayChange: PropTypes.func,
};

export default MusicPlayer;
