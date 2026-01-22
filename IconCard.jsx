/**
 * IconCard 组件 - 图标卡片
 * 
 * 用于展示功能图标和标签的小型磨砂玻璃卡片
 * 支持完整的无障碍性
 * 
 * @component
 * @example
 * <IconCard icon="📁" label="Files" />
 */

import React from 'react';
import PropTypes from 'prop-types';
import GlassCard from './GlassCard';

/**
 * 图标卡片
 * 
 * @param {Object} props - 组件 props
 * @param {string} props.icon - 图标（Emoji 或 Unicode）
 * @param {string} props.label - 卡片标签
 * @param {string} [props.description] - 无障碍性描述
 * @param {Function} [props.onClick] - 点击回调
 * @returns {React.ReactElement} 图标卡片
 */
const IconCard = React.forwardRef(
  (
    {
      icon,
      label,
      description,
      onClick,
      ...rest
    },
    ref
  ) => {
    const iconBoxId = `icon-card-description-${Math.random().toString(36).slice(2, 9)}`;

    return (
      <GlassCard
        ref={ref}
        variant="small"
        className="flex flex-col items-center justify-center gap-3"
        ariaLabel={label}
        ariaDescribedBy={description ? iconBoxId : undefined}
        role="button"
        tabIndex={onClick ? 0 : -1}
        onClick={onClick}
        onKeyDown={(e) => {
          if (onClick && (e.code === 'Space' || e.code === 'Enter')) {
            e.preventDefault();
            onClick(e);
          }
        }}
        {...rest}
      >
        {/* 图标盒子 */}
        <div
          className="w-12 h-12 rounded-2xl bg-gradient-to-br from-white/90 to-white/40 flex items-center justify-center text-2xl shadow-sm"
          aria-hidden="true"
        >
          {icon}
        </div>

        {/* 标签 */}
        <p className="font-semibold text-sm text-slate-900">
          {label}
        </p>

        {/* 可选的无障碍性描述 */}
        {description && (
          <p id={iconBoxId} className="sr-only">
            {description}
          </p>
        )}
      </GlassCard>
    );
  }
);

IconCard.displayName = 'IconCard';

IconCard.propTypes = {
  icon: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  description: PropTypes.string,
  onClick: PropTypes.func,
};

export default IconCard;
