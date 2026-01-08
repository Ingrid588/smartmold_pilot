/**
 * TripCard 组件 - 旅行计划卡片
 * 
 * 展示旅行信息的磨砂玻璃卡片，包含日期、图片占位符和参与者头像
 * 
 * @component
 * @example
 * <TripCard 
 *   title="Kyoto Trip"
 *   dateRange="Feb 24 - Mar 02"
 *   participants={2}
 * />
 */

import React from 'react';
import PropTypes from 'prop-types';
import GlassCard from './GlassCard';

/**
 * 旅行计划卡片
 * 
 * @param {Object} props - 组件 props
 * @param {string} [props.title='Kyoto Trip'] - 旅行名称
 * @param {string} [props.dateRange='Feb 24 - Mar 02'] - 日期范围
 * @param {number} [props.participants=2] - 参与人数（用于显示头像数量）
 * @returns {React.ReactElement} 旅行计划卡片
 */
const TripCard = React.forwardRef(
  (
    {
      title = 'Kyoto Trip',
      dateRange = 'Feb 24 - Mar 02',
      participants = 2,
    },
    ref
  ) => {
    return (
      <GlassCard
        ref={ref}
        variant="large"
        className="w-80"
        ariaLabel={`${title}旅行计划，${dateRange}`}
        role="region"
      >
        {/* 图片占位符 */}
        <div
          className="w-full h-32 bg-gradient-to-t from-black/10 to-transparent rounded-2xl mb-4 overflow-hidden"
          aria-hidden="true"
        >
          {/* 空的背景卡片 */}
        </div>

        {/* 标题 */}
        <h2 className="text-lg font-semibold text-slate-900 mb-2">
          {title}
        </h2>

        {/* 日期 */}
        <p
          className="text-sm text-slate-700 opacity-80 mb-4"
          aria-label={`旅行日期: ${dateRange}`}
        >
          {dateRange}
        </p>

        {/* 参与者头像列表 */}
        <div
          className="flex items-center gap-0"
          role="list"
          aria-label="参与者"
        >
          {Array.from({ length: participants }).map((_, index) => (
            <div
              key={index}
              className="w-8 h-8 rounded-full border-2 border-white bg-slate-300 -ml-2.5 first:ml-0"
              role="listitem"
              aria-label={`参与者 ${index + 1}`}
            />
          ))}
        </div>
      </GlassCard>
    );
  }
);

TripCard.displayName = 'TripCard';

TripCard.propTypes = {
  title: PropTypes.string,
  dateRange: PropTypes.string,
  participants: PropTypes.number,
};

export default TripCard;
