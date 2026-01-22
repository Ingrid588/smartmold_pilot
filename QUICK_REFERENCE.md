# 快速参考指南 - Glassmorphism React 组件库

## 📦 组件速查表

### GlassCard - 基础组件

```jsx
import { GlassCard } from './components';

// 基础使用
<GlassCard>
  <p>内容</p>
</GlassCard>

// 完整示例
<GlassCard
  className="w-80"
  variant="large"
  interactive={true}
  ariaLabel="卡片标题"
  role="article"
>
  <h2>标题</h2>
  <p>描述</p>
</GlassCard>
```

**可用变体：**
- `variant="default"` - 默认 (Tailwind: w-full sm:w-80)
- `variant="small"` - 小卡片 (Tailwind: w-36 h-36)
- `variant="large"` - 大卡片 (Tailwind: w-full sm:w-96)

---

### MusicPlayer - 音乐播放卡片

```jsx
import { MusicPlayer } from './components';

// 基础使用
<MusicPlayer />

// 自定义数据
<MusicPlayer
  title="Now Playing"
  artist="Glass Animals - Heat Waves"
  progress={60}
  onPlayChange={(isPlaying) => {
    console.log('播放状态:', isPlaying);
  }}
/>
```

**状态管理实现：**
```jsx
const [isPlaying, setIsPlaying] = useState(false);
const [progress, setProgress] = useState(60);

// 播放/暂停切换
const handlePlayToggle = () => {
  setIsPlaying(!isPlaying);
};

// 更新进度
const handleProgress = (newProgress) => {
  setProgress(newProgress);
};
```

---

### IconCard - 图标卡片

```jsx
import { IconCard } from './components';

// 基础使用
<IconCard
  icon="📁"
  label="Files"
/>

// 完整示例（可交互）
<IconCard
  icon="📁"
  label="Files"
  description="访问您的文件和文件夹"
  onClick={() => console.log('打开文件管理器')}
/>
```

**常用图标：**
- 📁 Files
- ☁️ Cloud
- ⚙️ Settings
- 👤 Profile
- 🎵 Music
- 📸 Photos

---

### TripCard - 旅行计划卡片

```jsx
import { TripCard } from './components';

// 基础使用
<TripCard />

// 自定义数据
<TripCard
  title="Tokyo Trip"
  dateRange="Mar 10 - Mar 20"
  participants={3}
/>
```

---

## 🎨 Tailwind 类名速查

### 背景和玻璃效果
```css
bg-white/65              /* 65% 不透明白色背景 */
bg-white/75              /* 75% 不透明（悬停时） */
backdrop-blur-[16px]     /* 16px 模糊效果 */
```

### 边框和圆角
```css
border                   /* 默认 1px 边框 */
border-white/80          /* 白色 80% 不透明 */
border-b-white/40        /* 下边框白色 40% 不透明 */
rounded-3xl              /* 24px 圆角 */
```

### 阴影
```css
shadow-[0_8px_32px_0_rgba(31,38,135,0.07)]    /* 轻阴影 */
shadow-[0_12px_40px_0_rgba(31,38,135,0.12)]   /* 重阴影 */
```

### 过渡和动画
```css
transition-all           /* 所有属性过渡 */
duration-300             /* 300ms 过渡时间 */
ease-in-out              /* 缓动函数 */
```

### 焦点和交互
```css
focus:outline-none       /* 移除默认轮廓 */
focus:ring-2             /* 2px 焦点环 */
focus:ring-blue-400      /* 蓝色焦点环 */
focus:ring-offset-2      /* 2px 焦点偏移 */
hover:bg-white/75        /* 悬停更改背景 */
hover:shadow-[...]       /* 悬停更改阴影 */
```

### 响应式
```css
w-full                   /* 100% 宽度 */
sm:w-1/2                 /* 小屏: 50% */
md:w-1/3                 /* 中等: 33% */
lg:w-1/4                 /* 大屏: 25% */
```

---

## ⌨️ 键盘快捷键

| 快捷键 | 功能 | 适用 |
|--------|------|------|
| **Tab** | 导航到下一个元素 | 所有交互元素 |
| **Shift+Tab** | 导航到前一个元素 | 所有交互元素 |
| **Enter** | 激活按钮 | 按钮、链接 |
| **Space** | 激活按钮 | 按钮、进度条 |
| **点击进度条** | 跳转到位置 | MusicPlayer |

---

## ♿ 无障碍性检查清单

在使用组件前检查：

- [ ] 提供了 `ariaLabel` 标签？
- [ ] 色彩对比度是否足够（4.5:1+）？
- [ ] 焦点环是否清晰可见？
- [ ] 键盘可以完全操作吗？
- [ ] 屏幕阅读器能读出内容吗？
- [ ] 触摸目标至少 44x44px？
- [ ] 响应式设计测试通过？

---

## 🎯 常见用法模式

### 模式 1: 基础卡片网格

```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
  <GlassCard><h2>Card 1</h2></GlassCard>
  <GlassCard><h2>Card 2</h2></GlassCard>
  <GlassCard><h2>Card 3</h2></GlassCard>
</div>
```

### 模式 2: 带背景的全屏页面

```jsx
<div className="min-h-screen bg-gradient-to-br from-cyan-100 to-indigo-100 p-8">
  <div className="max-w-7xl mx-auto">
    {/* 内容 */}
  </div>
</div>
```

### 模式 3: 深色模式支持

```jsx
const [isDarkMode, setIsDarkMode] = useState(false);

<div className={isDarkMode ? 'dark' : ''}>
  <GlassCard className={isDarkMode ? 'text-white' : 'text-slate-900'}>
    {/* 内容 */}
  </GlassCard>
</div>
```

### 模式 4: 带加载状态的互动卡片

```jsx
const [isLoading, setIsLoading] = useState(false);

<GlassCard className="w-80">
  <button 
    disabled={isLoading}
    onClick={async () => {
      setIsLoading(true);
      await fetchData();
      setIsLoading(false);
    }}
  >
    {isLoading ? '加载中...' : '点击'}
  </button>
</GlassCard>
```

---

## 🎨 颜色方案快速参考

### 浅色模式
```
背景渐变: 
  from-cyan-100 (#cffafe)
  to-indigo-100 (#e0e7ff)

文字色:
  slate-900 (#0f172a) - 标题
  slate-700 (#334155) - 正文
  
按钮:
  蓝色: #3b82f6 (blue-500)
  绿色: #22c55e (green-500)
```

### 深色模式
```
背景渐变:
  from-slate-950 (#020617)
  to-blue-950 (#172554)

文字色:
  slate-100 (#f1f5f9) - 标题
  slate-300 (#cbd5e1) - 正文

按钮:
  蓝色: #3b82f6 (blue-400) - 保持不变
  绿色: #10b981 (emerald-500) - 更鲜艳
```

---

## 🧪 测试速查表

### 无障碍性测试工具

```bash
# axe DevTools - 自动化检查
# 网址: https://www.deque.com/axe/

# Wave - WCAG 评估
# 网址: https://wave.webaim.org/

# WebAIM 对比度检查
# 网址: https://webaim.org/resources/contrastchecker/

# NVDA - 免费屏幕阅读器（Windows）
# 下载: https://www.nvaccess.org/

# JAWS - 商业屏幕阅读器
# 官网: https://www.freedomscientific.com/
```

### 快速测试步骤

```
1. 打开开发者工具 (F12)
2. 按 Tab 键在页面间导航
3. 检查焦点环清晰度
4. 右键 → 检查元素
5. 搜索 ARIA 属性
6. 验证色彩对比度
7. 用屏幕阅读器测试
```

---

## 🚀 性能优化提示

### ✅ 推荐做法

```jsx
// ✅ 使用 React.memo 避免不必要的重新渲染
const MemoizedCard = React.memo(GlassCard);

// ✅ 使用 useCallback 缓存回调函数
const handlePlayChange = useCallback((isPlaying) => {
  console.log(isPlaying);
}, []);

// ✅ 使用 useMemo 缓存计算结果
const cardVariant = useMemo(() => {
  return isSmallScreen ? 'small' : 'large';
}, [isSmallScreen]);
```

### ❌ 避免做法

```jsx
// ❌ 在渲染方法中创建新对象
<GlassCard style={{ color: 'blue' }} />

// ❌ 直接在 JSX 中定义函数
<button onClick={() => doSomething()} />

// ❌ 过度使用 state
// (应该用 CSS 处理的不要用 state)
```

---

## 💡 调试技巧

### 调试焦点问题

```javascript
// 在控制台运行，查看焦点路径
document.addEventListener('focus', (e) => {
  console.log('Focused:', e.target);
}, true);
```

### 调试 ARIA 问题

```javascript
// 查看元素的 ARIA 属性
const element = document.querySelector('[role="button"]');
console.log(element.getAttribute('aria-label'));
console.log(element.getAttribute('aria-pressed'));
```

### 调试样式问题

```javascript
// 查看元素的计算样式
const element = document.querySelector('.glass-panel');
console.log(window.getComputedStyle(element));
```

---

## 📱 设备测试尺寸

```
iPhone 14:      390 x 844
iPad Pro 11":   834 x 1194
Galaxy Tab:     1440 x 2560
MacBook Air:    1440 x 900
4K Monitor:     3840 x 2160
```

---

## 🔗 有用的链接

- [Tailwind CSS 文档](https://tailwindcss.com/)
- [React Docs](https://react.dev/)
- [WCAG 2.1 清单](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA 实践](https://www.w3.org/WAI/ARIA/apg/)
- [MDN Web Docs](https://developer.mozilla.org/)

---

## ❓ FAQ

**Q: 如何改变玻璃强度？**
A: 编辑 `bg-white/65` (0-100) 和 `backdrop-blur-[16px]`

**Q: 能用 CSS Modules 吗？**
A: 可以，但 Tailwind 已经提供了完整隔离

**Q: 支持 TypeScript 吗？**
A: 可以，添加 `.jsx` → `.tsx` 和类型定义

**Q: 如何自定义颜色？**
A: 编辑 `tailwind.config.js` 的 theme 部分

**Q: 支持移动端吗？**
A: 完全支持，所有组件都是响应式的

---

## 📝 版本历史

| 版本 | 日期 | 更新内容 |
|-----|------|---------|
| 1.0.0 | 2026-01-05 | 初始发布 |

---

**最后更新：2026-01-05**

[返回主文档](./GLASSMORPHISM_GUIDE.md) | [设置指南](./SETUP_GUIDE.md) | [A11y 报告](./ACCESSIBILITY_REPORT.md)
