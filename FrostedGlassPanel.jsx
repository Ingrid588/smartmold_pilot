/**
 * 高级磨砂玻璃组件 - FrostedGlassPanel
 * 
 * 特性：
 * - 真实的玻璃厚度感（多层阴影）
 * - 边缘反光效果
 * - 背景模糊透视
 * - 工业设计支持
 */

import React from 'react';
import PropTypes from 'prop-types';

const FrostedGlassPanel = React.forwardRef(
  (
    {
      children,
      className = '',
      opacity = 'standard',
      variant = 'content',
      size = 'medium',
      showLabel = true,
      label = '',
      interactive = true,
      ...props
    },
    ref
  ) => {
    // 透明度配置 - 分为内容展示和导航/按钮两类
    const opacityConfig = {
      // 内容展示类 - 高透明度，低模糊，文字清晰
      contentLight: {
        bg: 'rgba(255, 255, 255, 0.08)',
        border: 'rgba(255, 255, 255, 0.15)',
        blur: '4px',
        shadow: '0 8px 20px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.4), inset 0 -1px 0 rgba(0, 0, 0, 0.08), inset -1px -1px 4px rgba(255, 255, 255, 0.1), inset 1px 1px 4px rgba(0, 0, 0, 0.04)',
      },
      contentStandard: {
        bg: 'rgba(255, 255, 255, 0.12)',
        border: 'rgba(255, 255, 255, 0.2)',
        blur: '6px',
        shadow: '0 10px 30px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.5), inset 0 -1px 0 rgba(0, 0, 0, 0.1), inset -1px -1px 5px rgba(255, 255, 255, 0.12), inset 1px 1px 5px rgba(0, 0, 0, 0.05)',
      },
      contentDark: {
        bg: 'rgba(255, 255, 255, 0.18)',
        border: 'rgba(255, 255, 255, 0.25)',
        blur: '8px',
        shadow: '0 12px 35px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.6), inset 0 -1px 0 rgba(0, 0, 0, 0.12), inset -1px -1px 6px rgba(255, 255, 255, 0.15), inset 1px 1px 6px rgba(0, 0, 0, 0.06)',
      },
      // 导航栏/按钮类 - 低透明度，高模糊，磨砂质感强
      navLight: {
        bg: 'rgba(255, 255, 255, 0.15)',
        border: 'rgba(255, 255, 255, 0.25)',
        blur: '10px',
        shadow: '0 15px 40px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.5), inset 0 -1px 0 rgba(0, 0, 0, 0.15), inset -2px -2px 8px rgba(255, 255, 255, 0.15), inset 2px 2px 8px rgba(0, 0, 0, 0.08)',
      },
      navStandard: {
        bg: 'rgba(255, 255, 255, 0.25)',
        border: 'rgba(255, 255, 255, 0.3)',
        blur: '12px',
        shadow: '0 20px 60px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.6), inset 0 -1px 0 rgba(0, 0, 0, 0.2), inset -2px -2px 8px rgba(255, 255, 255, 0.2), inset 2px 2px 8px rgba(0, 0, 0, 0.1)',
      },
      navDark: {
        bg: 'rgba(255, 255, 255, 0.35)',
        border: 'rgba(255, 255, 255, 0.4)',
        blur: '14px',
        shadow: '0 25px 70px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.7), inset 0 -1px 0 rgba(0, 0, 0, 0.25), inset -2px -2px 10px rgba(255, 255, 255, 0.25), inset 2px 2px 10px rgba(0, 0, 0, 0.12)',
      },
      // 兼容旧API
      light: {
        bg: 'rgba(255, 255, 255, 0.15)',
        border: 'rgba(255, 255, 255, 0.25)',
        blur: '10px',
        shadow: '0 15px 40px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.5), inset 0 -1px 0 rgba(0, 0, 0, 0.15), inset -2px -2px 8px rgba(255, 255, 255, 0.15), inset 2px 2px 8px rgba(0, 0, 0, 0.08)',
      },
      standard: {
        bg: 'rgba(255, 255, 255, 0.25)',
        border: 'rgba(255, 255, 255, 0.3)',
        blur: '12px',
        shadow: '0 20px 60px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.6), inset 0 -1px 0 rgba(0, 0, 0, 0.2), inset -2px -2px 8px rgba(255, 255, 255, 0.2), inset 2px 2px 8px rgba(0, 0, 0, 0.1)',
      },
      dark: {
        bg: 'rgba(255, 255, 255, 0.35)',
        border: 'rgba(255, 255, 255, 0.4)',
        blur: '14px',
        shadow: '0 25px 70px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.7), inset 0 -1px 0 rgba(0, 0, 0, 0.25), inset -2px -2px 10px rgba(255, 255, 255, 0.25), inset 2px 2px 10px rgba(0, 0, 0, 0.12)',
      },
      opaque: {
        bg: 'rgba(255, 255, 255, 0.45)',
        border: 'rgba(255, 255, 255, 0.5)',
        blur: '16px',
        shadow: '0 30px 80px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.8), inset 0 -1px 0 rgba(0, 0, 0, 0.3), inset -2px -2px 12px rgba(255, 255, 255, 0.3), inset 2px 2px 12px rgba(0, 0, 0, 0.15)',
      },
    };

    const sizeConfig = {
      small: {
        width: '280px',
        padding: '20px',
        borderRadius: '20px',
      },
      medium: {
        width: '400px',
        padding: '30px',
        borderRadius: '25px',
      },
      large: {
        width: '600px',
        padding: '40px',
        borderRadius: '30px',
      },
      fullWidth: {
        width: '100%',
        padding: '40px',
        borderRadius: '25px',
      },
    };

    const configKey = variant === 'nav' ? `nav${opacity.charAt(0).toUpperCase() + opacity.slice(1)}` : `content${opacity.charAt(0).toUpperCase() + opacity.slice(1)}`;
    const config = opacityConfig[configKey] || opacityConfig[opacity] || opacityConfig.standard;
    const sizeStyle = sizeConfig[size] || sizeConfig.medium;

    const style = {
      position: 'relative',
      width: sizeStyle.width,
      padding: sizeStyle.padding,
      background: config.bg,
      backdropFilter: `blur(${config.blur})`,
      WebkitBackdropFilter: `blur(${config.blur})`,
      border: `1px solid ${config.border}`,
      borderRadius: sizeStyle.borderRadius,
      boxShadow: config.shadow,
      overflow: 'hidden',
      ...((interactive && {
        cursor: 'pointer',
        transition: 'all 0.3s ease',
      }) || {}),
    };

    const handleHover = (e) => {
      if (interactive) {
        e.currentTarget.style.transform = 'translateY(-5px)';
        e.currentTarget.style.boxShadow = config.shadow.replace(
          /rgba\(0, 0, 0, [0-9.]+\)/g,
          'rgba(0, 0, 0, 0.5)'
        );
      }
    };

    const handleHoverEnd = (e) => {
      if (interactive) {
        e.currentTarget.style.transform = 'none';
        e.currentTarget.style.boxShadow = config.shadow;
      }
    };

    return (
      <div
        ref={ref}
        style={style}
        className={className}
        onMouseEnter={handleHover}
        onMouseLeave={handleHoverEnd}
        {...props}
      >
        {/* 高光边缘 */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '1.5px',
            background: `linear-gradient(90deg, transparent, rgba(255, 255, 255, ${
              opacity === 'opaque' ? 0.7 : opacity === 'dark' ? 0.6 : 0.5
            }), transparent)`,
            borderRadius: sizeStyle.borderRadius,
          }}
        ></div>

        {/* 标签 */}
        {showLabel && label && (
          <div
            style={{
              position: 'absolute',
              top: '12px',
              right: '15px',
              background: 'rgba(100, 150, 200, 0.6)',
              color: 'white',
              padding: '4px 10px',
              borderRadius: '10px',
              fontSize: '11px',
              fontWeight: '600',
              backdropFilter: 'blur(8px)',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              zIndex: 10,
            }}
          >
            {label}
          </div>
        )}

        {/* 内容 */}
        <div style={{ position: 'relative', zIndex: 5 }}>
          {children}
        </div>
      </div>
    );
  }
);

FrostedGlassPanel.displayName = 'FrostedGlassPanel';

FrostedGlassPanel.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  opacity: PropTypes.oneOf(['light', 'standard', 'dark', 'opaque']),
  variant: PropTypes.oneOf(['content', 'nav']),
  size: PropTypes.oneOf(['small', 'medium', 'large', 'fullWidth']),
  showLabel: PropTypes.bool,
  label: PropTypes.string,
  interactive: PropTypes.bool,
};

export default FrostedGlassPanel;
