<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Light Glassmorphism UI Kit</title>
    <style>
        /* 
         * 全局设置：引入无衬线字体以匹配现代感 
         * 背景：浅色系的关键在于背景不能是纯白，否则玻璃看不见。
         * 使用了流动的柔和渐变模拟图1和图2的氛围。
         */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

        body {
            margin: 0;
            padding: 0;
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #e0f2fe 0%, #f0f9ff 50%, #eef2ff 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: #334155; /* 深蓝灰色字体，保证浅色背景下的对比度 */
        }

        /* 
         * 装饰性背景球体 
         * 用于衬托玻璃效果，没有背景物体的玻璃是看不出磨砂感的。
         */
       .decorative-shape {
            position: absolute;
            border-radius: 50%;
            filter: blur(60px);
            z-index: -1;
            animation: float 10s infinite ease-in-out;
        }
       .shape-1 {
            width: 300px;
            height: 300px;
            background: #bae6fd; /* 浅蓝 */
            top: 10%;
            left: 20%;
        }
       .shape-2 {
            width: 250px;
            height: 250px;
            background: #ddd6fe; /* 浅紫 */
            bottom: 15%;
            right: 20%;
            animation-delay: -5s;
        }

        @keyframes float {
            0%, 100% { transform: translate(0, 0); }
            50% { transform: translate(0, 30px); }
        }

        /* 主容器 */
       .container {
            display: flex;
            gap: 24px;
            padding: 40px;
            flex-wrap: wrap;
            justify-content: center;
            max-width: 1200px;
        }

        /* 
         * 核心 Glassmorphism 类 
         * 针对浅色系调整了 rgba 的透明度
         */
       .glass-panel {
            /* 背景色：白色，但透明度较高 (0.6)，保证亮度的同时透出背景 */
            background: rgba(255, 255, 255, 0.65);
            
            /* 核心模糊属性 */
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            
            /* 边框：利用透明度差异制造“厚度感” */
            border: 1px solid rgba(255, 255, 255, 0.8);
            border-bottom: 1px solid rgba(255, 255, 255, 0.4);
            border-right: 1px solid rgba(255, 255, 255, 0.4);
            
            /* 阴影：浅色系阴影要柔和，使用带蓝色的灰，避免纯黑脏感 */
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
            
            border-radius: 24px;
            padding: 24px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

       .glass-panel:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.12);
            /* 悬停时稍微增加不透明度，提升交互感 */
            background: rgba(255, 255, 255, 0.75);
        }

        /* 卡片类型 A：类似图2的音乐播放/控制面板 */
       .card-large {
            width: 320px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        /* 卡片类型 B：类似图3的图标卡片 */
       .card-small {
            width: 140px;
            height: 140px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }

        /* 内部元素样式 */
        h2 { font-size: 18px; font-weight: 600; margin: 0 0 8px 0; }
        p { font-size: 14px; margin: 0; opacity: 0.8; line-height: 1.5; }
        
       .btn {
            margin-top: 20px;
            padding: 10px 20px;
            border: none;
            border-radius: 12px;
            background: linear-gradient(135deg, #60a5fa, #3b82f6);
            color: white;
            font-weight: 500;
            cursor: pointer;
            /* 按钮内部也有微弱的玻璃感 */
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
            transition: 0.2s;
        }
       .btn:hover { filter: brightness(1.1); }

       .icon-box {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            /* 图标背景使用更通透的渐变，呼应图3 */
            background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.4));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }

    </style>
</head>
<body>

    <div class="decorative-shape shape-1"></div>
    <div class="decorative-shape shape-2"></div>

    <div class="container">
        <div class="glass-panel card-large">
            <div>
                <div class="icon-box" style="margin-bottom: 16px;">🎵</div>
                <h2>Now Playing</h2>
                <p>Glass Animals - Heat Waves</p>
                <div style="height: 4px; background: rgba(0,0,0,0.05); border-radius: 2px; margin-top: 16px; position: relative;">
                    <div style="width: 60%; height: 100%; background: #3b82f6; border-radius: 2px;"></div>
                </div>
            </div>
            <button class="btn">Play</button>
        </div>

        <div class="glass-panel card-large">
            <div style="height: 120px; background: rgba(255,255,255,0.3); border-radius: 16px; margin-bottom: 16px; overflow: hidden; position: relative;">
                <div style="width: 100%; height: 100%; background: linear-gradient(to top, rgba(0,0,0,0.1), transparent);"></div>
            </div>
            <h2>Kyoto Trip</h2>
            <p style="margin-bottom: 8px;">Feb 24 - Mar 02</p>
            <div style="display: flex; gap: -8px;">
                <div style="width: 30px; height: 30px; border-radius: 50%; background: #e2e8f0; border: 2px solid #fff;"></div>
                <div style="width: 30px; height: 30px; border-radius: 50%; background: #cbd5e1; border: 2px solid #fff; margin-left: -10px;"></div>
            </div>
        </div>

        <div class="glass-panel card-small">
            <div class="icon-box">📁</div>
            <p style="font-weight: 600; font-size: 13px;">Files</p>
        </div>

        <div class="glass-panel card-small">
            <div class="icon-box">☁️</div>
            <p style="font-weight: 600; font-size: 13px;">Cloud</p>
        </div>
    </div>

</body>
</html>