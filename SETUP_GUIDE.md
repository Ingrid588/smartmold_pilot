# React Glassmorphism 项目 - 完整设置指南

## 📂 项目结构

```
glassmorphism-react/
├── src/
│   ├── components/
│   │   ├── GlassCard.jsx              # 基础玻璃卡片组件
│   │   ├── MusicPlayer.jsx            # 音乐播放卡片（带状态管理）
│   │   ├── IconCard.jsx               # 图标卡片
│   │   ├── TripCard.jsx               # 旅行计划卡片
│   │   └── index.js                   # 导出所有组件
│   ├── App.jsx                        # 主应用
│   ├── App.css                        # 全局样式（最小化）
│   └── main.jsx                       # 入口文件
├── public/
│   └── index.html
├── package.json
├── tailwind.config.js
├── postcss.config.js
├── vite.config.js
├── GLASSMORPHISM_GUIDE.md             # 完整文档
├── ACCESSIBILITY_REPORT.md            # A11y 报告
└── README.md                          # 项目 README
```

## 🚀 快速开始

### 1. 安装依赖

```bash
npm install
# 或
yarn install
```

### 2. 启动开发服务器

```bash
npm run dev
# 或
yarn dev
```

打开浏览器访问：`http://localhost:5173`

### 3. 构建生产版本

```bash
npm run build
# 或
yarn build
```

## 📦 package.json 配置

```json
{
  "name": "glassmorphism-react",
  "version": "1.0.0",
  "description": "现代化磨砂玻璃 React 组件库，完整无障碍性支持",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext .js,.jsx",
    "test": "vitest"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "prop-types": "^15.8.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^4.4.0",
    "tailwindcss": "^3.3.0",
    "postcss": "^8.4.24",
    "autoprefixer": "^10.4.14",
    "eslint": "^8.46.0",
    "eslint-plugin-react": "^7.32.2",
    "vitest": "^0.34.1"
  }
}
```

## 🎨 Tailwind CSS 配置

### tailwind.config.js

```javascript
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      backdropFilter: {
        'blur-[16px]': 'blur(16px)',
      },
      boxShadow: {
        'glass-light': '0 8px 32px 0 rgba(31, 38, 135, 0.07)',
        'glass-dark': '0 8px 32px 0 rgba(31, 38, 135, 0.15)',
      },
      animation: {
        float: 'float 10s infinite ease-in-out',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translate(0, 0)' },
          '50%': { transform: 'translate(0, 30px)' },
        },
      },
    },
  },
  plugins: [],
}
```

### postcss.config.js

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

## 📝 使用示例

### 基础示例

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
        {/* 标题 */}
        <h1 className="text-4xl font-bold text-slate-900 mb-8">
          Glassmorphism UI Kit
        </h1>

        {/* 卡片网格 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {/* 音乐播放卡片 */}
          <MusicPlayer
            title="Now Playing"
            artist="Glass Animals - Heat Waves"
            progress={60}
          />

          {/* 旅行计划卡片 */}
          <TripCard
            title="Kyoto Trip"
            dateRange="Feb 24 - Mar 02"
            participants={2}
          />

          {/* 图标卡片 */}
          <IconCard
            icon="📁"
            label="Files"
            description="访问您的文件和文件夹"
          />
        </div>
      </div>
    </div>
  );
}

export default App;
```

### 自定义 GlassCard

```jsx
<GlassCard
  className="w-full max-w-md"
  variant="large"
  interactive={true}
  ariaLabel="自定义内容卡片"
>
  <div className="space-y-4">
    <h2 className="text-2xl font-bold text-slate-900">
      自定义标题
    </h2>
    <p className="text-slate-700 leading-relaxed">
      在这里添加任何内容。GlassCard 为所有子元素提供玻璃背景。
    </p>
    <button className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors">
      点击我
    </button>
  </div>
</GlassCard>
```

### 音乐播放卡片状态管理

```jsx
import React, { useState } from 'react';
import MusicPlayer from './components/MusicPlayer';

function MusicApp() {
  const [currentTrack, setCurrentTrack] = useState({
    title: 'Now Playing',
    artist: 'Glass Animals - Heat Waves',
    progress: 60,
  });

  const handlePlayChange = (isPlaying) => {
    console.log('播放状态:', isPlaying);
    // 这里可以连接到实际的音乐播放器
  };

  return (
    <MusicPlayer
      {...currentTrack}
      onPlayChange={handlePlayChange}
    />
  );
}

export default MusicApp;
```

## 🧪 测试指南

### 无障碍性测试

```bash
# 安装 axe-core 测试工具
npm install --save-dev @axe-core/react

# 在组件中使用
import { axe, toHaveNoViolations } from 'jest-axe';

expect(toHaveNoViolations());
```

### 键盘导航测试

1. 使用 **Tab** 键在所有元素间导航
2. 使用 **Shift+Tab** 反向导航
3. 使用 **Enter** 或 **Space** 激活按钮
4. 验证焦点顺序正确且焦点环清晰可见

### 屏幕阅读器测试

#### macOS - VoiceOver
```
启用: Cmd + F5
导航: VO + 右箭头键
激活: VO + Space
```

#### Windows - NVDA
```
下载: https://www.nvaccess.org/
导航: 箭头键
激活: Enter 或 Space
```

## 🎨 主题定制

### 亮色主题（默认）

```jsx
<div className="bg-gradient-to-br from-cyan-100 to-indigo-100 min-h-screen">
  {/* 内容 */}
</div>
```

### 深色主题

```jsx
<div className="dark bg-gradient-to-br from-slate-950 to-blue-950 min-h-screen">
  {/* 内容 - 自动适应深色模式 */}
</div>
```

### 自定义颜色方案

编辑 `tailwind.config.js`：

```javascript
theme: {
  colors: {
    primary: '#10b981',      // 主颜色
    secondary: '#64748b',    // 次要颜色
    glass: 'rgba(255,255,255,0.65)',  // 玻璃背景
  }
}
```

## 📱 响应式设计

### 断点系统

```javascript
// Tailwind 默认断点
sm:  640px   // 小屏幕
md:  768px   // 中等屏幕
lg:  1024px  // 大屏幕
xl:  1280px  // 超大屏幕
2xl: 1536px  // 2K 屏幕
```

### 使用示例

```jsx
<div className="
  w-full               // 手机: 全宽
  sm:w-1/2            // 小屏幕: 50%
  md:w-1/3            // 中等屏幕: 33%
  lg:w-1/4            // 大屏幕: 25%
">
  响应式内容
</div>
```

## 🔧 常见问题（FAQ）

### Q1: 如何改变玻璃效果的强度？

```jsx
// 减少模糊强度
backdrop-blur-[12px]  // 默认: blur-[16px]

// 增加不透明度
bg-white/75           // 默认: bg-white/65

// 编辑 GlassCard.jsx
baseClasses = [
  'bg-white/75',         // 更不透明
  'backdrop-blur-[20px]', // 更模糊
]
```

### Q2: 如何在深色模式下调整玻璃效果？

```jsx
<article className={`
  ${isDarkMode ? 'bg-slate-900/40' : 'bg-white/65'}
  ${isDarkMode ? 'text-white' : 'text-slate-900'}
`}>
```

### Q3: 我可以添加阴影吗？

```jsx
<GlassCard className="shadow-lg">
  {/* 内容 */}
</GlassCard>

// 或自定义阴影
className="shadow-[0_10px_40px_rgba(0,0,0,0.1)]"
```

### Q4: 如何禁用悬停效果？

```jsx
<GlassCard interactive={false}>
  {/* 无悬停效果的内容 */}
</GlassCard>
```

### Q5: 如何集成真实的音乐播放器？

```jsx
import MusicPlayer from './components/MusicPlayer';

function IntegratedPlayer() {
  const [audioRef] = useState(new Audio());

  const handlePlayChange = (isPlaying) => {
    if (isPlaying) {
      audioRef.play();
    } else {
      audioRef.pause();
    }
  };

  return (
    <MusicPlayer onPlayChange={handlePlayChange} />
  );
}
```

## 📚 资源链接

- [Tailwind CSS 文档](https://tailwindcss.com/)
- [React 官方文档](https://react.dev/)
- [WCAG 2.1 指南](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA 实践指南](https://www.w3.org/WAI/ARIA/apg/)
- [Vite 官方文档](https://vitejs.dev/)

## 🤝 贡献

欢迎提交 Issues 和 Pull Requests！

### 贡献步骤

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 📞 联系方式

有问题或建议？

- 提交 GitHub Issue
- 发送邮件至 support@example.com
- 在讨论区提问

---

**祝你使用愉快！🎉**
