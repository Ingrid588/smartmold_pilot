/**
 * GlassCard 组件 - 可复用的磨砂玻璃卡片
 * 
 * 功能特点：
 * - 支持自定义 className 和 children
 * - 完整的无障碍性支持（ARIA 属性）
 * - Tailwind CSS 样式，确保样式隔离
 * - 响应式设计
 * 
 * @component
 * @example
 * <GlassCard className="w-80">
 *   <h2>标题</h2>
 *   <p>内容</p>
 * </GlassCard>
 */

import React from 'react';
import PropTypes from 'prop-types';

/**
 * 磨砂玻璃卡片组件
 * 
 * @param {Object} props - 组件 props
 * @param {React.ReactNode} props.children - 卡片内容
 * @param {string} [props.className=''] - 额外的 CSS 类名
 * @param {string} [props.variant='default'] - 卡片变体：'default' | 'small' | 'large'
 * @param {string} [props.opacity='standard'] - 透明度：'light' (45%) | 'standard' (65%) | 'dark' (85%) | 'opaque' (95%)
 * @param {boolean} [props.interactive=true] - 是否启用悬停交互效果
 * @param {string} [props.role='article'] - 语义 ARIA role
 * @param {string} [props.ariaLabel] - 卡片的无障碍标签
 * @param {string} [props.ariaDescribedBy] - 关联的描述元素 ID
 * @returns {React.ReactElement} 玻璃卡片元素
 */
const GlassCard = React.forwardRef(
  (
    {
      children,
      className = '',
      variant = 'default',
      opacity = 'standard',
      interactive = true,
      role = 'article',
      ariaLabel,
      ariaDescribedBy,
      ...rest
    },
    ref
  ) => {
    // 透明度映射
    const opacityMap = {
      light: {
        bg: 'bg-white/45',
        border: 'border-white/60',
        borderB: 'border-b-white/30',
        borderR: 'border-r-white/30',
        shadow: 'shadow-[0_8px_32px_0_rgba(31,38,135,0.04)]',
        hover: {
          bg: 'hover:bg-white/55',
          shadow: 'hover:shadow-[0_12px_40px_0_rgba(31,38,135,0.08)]',
        },
      },
      standard: {
        bg: 'bg-white/65',
        border: 'border-white/80',
        borderB: 'border-b-white/40',
        borderR: 'border-r-white/40',
        shadow: 'shadow-[0_8px_32px_0_rgba(31,38,135,0.07)]',
        hover: {
          bg: 'hover:bg-white/75',
          shadow: 'hover:shadow-[0_12px_40px_0_rgba(31,38,135,0.12)]',
        },
      },
      dark: {
        bg: 'bg-white/85',
        border: 'border-white/95',
        borderB: 'border-b-white/70',
        borderR: 'border-r-white/70',
        shadow: 'shadow-[0_8px_32px_0_rgba(31,38,135,0.1)]',
        hover: {
          bg: 'hover:bg-white/90',
          shadow: 'hover:shadow-[0_12px_40px_0_rgba(31,38,135,0.14)]',
        },
      },
      opaque: {
        bg: 'bg-white/95',
        border: 'border-white/100',
        borderB: 'border-b-white/80',
        borderR: 'border-r-white/80',
        shadow: 'shadow-[0_8px_32px_0_rgba(31,38,135,0.12)]',
        hover: {
          bg: 'hover:bg-white/98',
          shadow: 'hover:shadow-[0_12px_40px_0_rgba(31,38,135,0.15)]',
        },
      },
    };

    const currentOpacity = opacityMap[opacity] || opacityMap.standard;

    // 基础玻璃效果样式
    const baseClasses = [
      // 背景和玻璃效果
      currentOpacity.bg,
      'backdrop-blur-[16px]',                 // 16px 模糊效果
      '-webkit-backdrop-filter-blur-[16px]',  // iOS Safari 支持
      
      // 边框
      'border',
      currentOpacity.border,
      currentOpacity.borderB,
      currentOpacity.borderR,
      
      // 阴影
      currentOpacity.shadow,
      
      // 圆角和内边距
      'rounded-3xl',
      'p-6',
      
      // 过渡效果
      'transition-all',
      'duration-300',
      'ease-in-out',
    ];

    // 根据变体添加尺寸类
    const variantClasses = {
      default: ['w-full', 'sm:w-80'],
      small: ['w-36', 'h-36'],
      large: ['w-full', 'sm:w-96'],
    };

    // 交互效果（悬停）
    const interactiveClasses = interactive
      ? [
          currentOpacity.hover.shadow,
          'hover:-translate-y-1',                               // 上浮效果
          currentOpacity.hover.bg,
          'cursor-pointer',
        ]
      : [];

    const allClasses = [
      ...baseClasses,
      ...(variantClasses[variant] || variantClasses.default),
      ...interactiveClasses,
      className,
    ].join(' ');

    return (
      <article
        ref={ref}
        className={allClasses}
        role={role}
        aria-label={ariaLabel}
        aria-describedby={ariaDescribedBy}
        {...rest}
      >
        {children}
      </article>
    );
  }
);

GlassCard.displayName = 'GlassCard';

GlassCard.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  variant: PropTypes.oneOf(['default', 'small', 'large']),
  opacity: PropTypes.oneOf(['light', 'standard', 'dark', 'opaque']),
  interactive: PropTypes.bool,
  role: PropTypes.string,
  ariaLabel: PropTypes.string,
  ariaDescribedBy: PropTypes.string,
};

export default GlassCard;
