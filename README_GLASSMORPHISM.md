# 🎨 Glassmorphism React 组件库

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![WCAG Compliant](https://img.shields.io/badge/WCAG-2.1%20AA-brightgreen)]()
[![React](https://img.shields.io/badge/React-18.2%2B-blue)]()
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-3.3%2B-blue)]()

一套现代化的磨砂玻璃（Glassmorphism）React 组件库，完整支持无障碍性标准（WCAG 2.1 AA），使用 Tailwind CSS 确保样式隔离。

## ✨ 核心特性

- 🎨 **Glassmorphism 设计** - 现代化磨砂玻璃效果
- ♿ **完整无障碍性** - WCAG 2.1 AA 标准合规
- 📱 **响应式设计** - 支持 768px 到 2560px+ 的所有设备
- ⌨️ **键盘导航** - 完全支持键盘操作（Tab、Enter、Space）
- 🔊 **屏幕阅读器** - 完整的 ARIA 支持
- 🎯 **Tailwind CSS** - 零全局污染的原子化设计
- 🌓 **深色模式** - 开箱即用的深色模式支持
- 🎭 **交互状态** - 完整的状态管理示例

## 🚀 快速开始

### 安装

```bash
npm install
# 或使用 yarn
yarn install
# 或使用 pnpm
pnpm install
```

### 开发

```bash
npm run dev
```

打开浏览器访问 `http://localhost:5173`

### 生产构建

```bash
npm run build
```

## 📦 组件库

### GlassCard - 基础玻璃卡片

```jsx
import { GlassCard } from './components';

<GlassCard className="w-80" variant="large">
  <h2>标题</h2>
  <p>内容</p>
</GlassCard>
```

**Props:**
- `children` (ReactNode) - 卡片内容 **必需**
- `className` (string) - 额外的 Tailwind 类名
- `variant` ('default' | 'small' | 'large') - 卡片尺寸
- `interactive` (boolean) - 是否启用悬停效果
- `ariaLabel` (string) - 无障碍标签
- `role` (string) - 语义角色

### MusicPlayer - 音乐播放卡片

```jsx
import { MusicPlayer } from './components';

<MusicPlayer
  title="Now Playing"
  artist="Glass Animals - Heat Waves"
  progress={60}
  onPlayChange={(isPlaying) => console.log(isPlaying)}
/>
```

**功能:**
- ⏯️ 播放/暂停状态管理（useState）
- 📊 交互式进度条
- ⌨️ 键盘支持（Space/Enter）
- 🎨 动态按钮颜色反馈
- 🔊 完整屏幕阅读器支持

### IconCard - 图标卡片

```jsx
import { IconCard } from './components';

<IconCard
  icon="📁"
  label="Files"
  description="访问您的文件和文件夹"
  onClick={() => console.log('clicked')}
/>
```

### TripCard - 旅行计划卡片

```jsx
import { TripCard } from './components';

<TripCard
  title="Kyoto Trip"
  dateRange="Feb 24 - Mar 02"
  participants={2}
/>
```

## 📋 完整示例

```jsx
import React from 'react';
import {
  GlassCard,
  MusicPlayer,
  IconCard,
  TripCard,
} from './components';

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-100 to-indigo-100 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-slate-900 mb-8">
          Glassmorphism UI Kit
        </h1>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <MusicPlayer />
          <TripCard />
          <IconCard icon="📁" label="Files" />
          <IconCard icon="☁️" label="Cloud" />
        </div>
      </div>
    </div>
  );
}

export default App;
```

## ♿ 无障碍性（A11y）

### WCAG 2.1 AA 标准

✅ **色彩对比度**
- 文字对比度: 11.2:1 (AAA 级别)
- 按钮对比度: 4.5:1+ (AA 级别)
- 焦点环对比度: 5.8:1 (AA 级别)

✅ **键盘导航**
- Tab 键导航所有元素
- Enter/Space 激活按钮
- 进度条支持点击调整
- 焦点陷阱防止

✅ **屏幕阅读器**
- 完整的 ARIA 标签
- aria-live 实时更新
- 语义 HTML 元素
- sr-only 隐藏内容

✅ **焦点管理**
- 清晰的焦点环（3px）
- 正确的焦点顺序
- focus:ring-blue-400 高对比度

✅ **响应式设计**
- 44x44px 最小触摸目标
- 流动布局支持 200% 放大
- 支持各种屏幕尺寸

详见 [ACCESSIBILITY_REPORT.md](./ACCESSIBILITY_REPORT.md) 获取完整无障碍性审查报告。

## 🎨 样式系统

### 玻璃效果规范

```css
背景: rgba(255, 255, 255, 0.65)    /* 65% 不透明白色 */
模糊: blur(16px)                   /* 16px 模糊效果 */
边框: 1px solid rgba(255,255,255,0.8)
圆角: 24px
阴影: 0 8px 32px rgba(31,38,135,0.07)
```

### Tailwind CSS 类名

所有样式使用 Tailwind 原子类，完全隔离：

```jsx
className={`
  bg-white/65              // 背景不透明度
  backdrop-blur-[16px]     // 模糊效果
  border border-white/80   // 边框
  rounded-3xl              // 圆角
  p-6                      // 内边距
  shadow-[0_8px_32px...]   // 自定义阴影
  hover:bg-white/75        // 悬停效果
  transition-all duration-300  // 过渡动画
`}
```

## 📱 响应式设计

| 屏幕尺寸 | 断点 | 布局 |
|---------|------|------|
| 手机 | < 640px | 1 列 |
| 平板 | 640px - 1024px | 2 列 |
| 桌面 | 1024px - 1536px | 3 列 |
| 超大 | > 1536px | 4+ 列 |

## 🧪 测试

### 键盘导航测试

```bash
1. 按 Tab 键在所有元素间导航
2. 按 Shift+Tab 反向导航
3. 按 Enter 或 Space 激活按钮
4. 验证焦点顺序正确且焦点环清晰
```

### 屏幕阅读器测试

```bash
macOS: Cmd + F5 (VoiceOver)
Windows: NVDA (https://www.nvaccess.org/)
```

### 色彩对比度检查

- [WebAIM Color Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Wave Evaluation Tool](https://wave.webaim.org/)

## 📚 文档

- [GLASSMORPHISM_GUIDE.md](./GLASSMORPHISM_GUIDE.md) - 完整 API 文档
- [ACCESSIBILITY_REPORT.md](./ACCESSIBILITY_REPORT.md) - 无障碍性审查报告
- [SETUP_GUIDE.md](./SETUP_GUIDE.md) - 项目设置指南

## 🛠️ 技术栈

- **React 18.2+** - 现代化 React 框架
- **Tailwind CSS 3.3+** - 原子化 CSS 框架
- **Vite** - 极速 Web 构建工具
- **PostCSS** - CSS 后处理器
- **PropTypes** - 运行时类型检查

## 📦 项目结构

```
src/
├── components/
│   ├── GlassCard.jsx          # 基础玻璃卡片
│   ├── MusicPlayer.jsx        # 音乐播放卡片
│   ├── IconCard.jsx           # 图标卡片
│   ├── TripCard.jsx           # 旅行计划卡片
│   └── index.js               # 导出入口
├── GlassUIDemo.jsx            # 完整示例应用
├── App.jsx                    # 主应用入口
└── main.jsx                   # React 入口
```

## 🌓 深色模式

组件自动支持深色模式：

```jsx
<div className="dark">
  <MusicPlayer />  // 自动适应深色背景
</div>
```

## 🎯 最佳实践

### ✅ 使用组件时

1. 始终提供 `ariaLabel` 以增强无障碍性
2. 使用 `variant` 属性调整卡片尺寸
3. 在 `onClick` 处理器中提供用户反馈
4. 使用 Tailwind 类名自定义样式
5. 测试键盘和屏幕阅读器兼容性

### ✅ 添加新组件时

1. 使用语义 HTML 元素
2. 添加必要的 ARIA 属性
3. 实现键盘导航支持
4. 确保色彩对比度符合标准
5. 测试无障碍性合规性
6. 文档化所有 Props

## 🚨 已知限制

- 需要现代浏览器支持 CSS backdrop-filter
- IE11 不支持（已过支持周期）
- 某些旧版 iOS Safari 可能需要特殊处理

## 🤝 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing`)
5. 打开 Pull Request

### 贡献时请确保：

- ✅ 代码遵循现有风格
- ✅ 添加了适当的注释
- ✅ 更新了相关文档
- ✅ 通过了无障碍性检查
- ✅ 在多个浏览器上测试

## 📄 许可证

MIT License © 2026

本项目采用 MIT 许可证。详见 [LICENSE](./LICENSE) 文件。

## 💬 反馈和支持

- 🐛 发现 Bug？提交 [GitHub Issue](https://github.com/yourname/repo/issues)
- 💡 有功能建议？提交 [Discussion](https://github.com/yourname/repo/discussions)
- ❓ 有问题？查看 [FAQ](#faq) 或提问

## 📞 联系方式

- Email: support@example.com
- Twitter: [@yourhandle](https://twitter.com/yourhandle)
- Discord: [加入我们的社区](https://discord.gg/yourserver)

## 🙏 致谢

感谢所有贡献者和用户的支持！

特别感谢：
- Gemini Vision 提供的原始设计灵感
- Tailwind CSS 团队的优秀框架
- React 社区的最佳实践

---

**⭐ 如果此项目对你有帮助，请给一个 Star！**

---

**最后更新：2026-01-05**

Made with ❤️ by the community
