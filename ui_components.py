"""
SmartMold Pilot V3 - UI Components Library
Light Frosted Glass (Glassmorphism) - Apple Vision Pro Style
"""

from nicegui import ui
from typing import Callable, Optional, List
from functools import wraps


# ============================================================
# Light Frosted Glass Theme Configuration
# ============================================================

GLASS_THEME = {
    # Background gradients
    "bg_primary": "bg-gradient-to-br from-slate-50 via-gray-100 to-slate-200",
    "bg_card": "bg-white/20",  # Ultra-transparent for true glass effect
    "bg_card_secondary": "bg-white/15",
    
    # Glass morphism effects - HARDCORE with extreme transparency
    "backdrop": "backdrop-filter backdrop-blur-2xl",  # Even stronger blur
    "border": "border border-white/80",  # More visible border for transparency
    "border_subtle": "border border-white/50",
    "rounded": "rounded-2xl",
    
    # Shadows - classic glass effect
    "shadow": "shadow-[0_8px_32px_0_rgba(31,38,135,0.15)]",
    "shadow_md": "shadow-[0_4px_16px_0_rgba(31,38,135,0.10)]",
    "shadow_sm": "shadow-[0_2px_8px_0_rgba(31,38,135,0.08)]",
    
    # Text colors - emerald green from reference image
    "text_primary": "text-slate-800",
    "text_secondary": "text-slate-600",
    "text_tertiary": "text-slate-500",
    "text_accent": "text-emerald-600",  # Changed to emerald green from reference
    "text_accent_light": "text-emerald-500",
    "text_success": "text-emerald-600",
    "text_warning": "text-amber-600",
    "text_error": "text-red-600",
    "text_light": "text-white",
}

GLASS_CARD_STYLE = f"{GLASS_THEME['bg_card']} {GLASS_THEME['backdrop']} {GLASS_THEME['border']} {GLASS_THEME['rounded']} {GLASS_THEME['shadow']} p-6"

GLASS_INPUT_STYLE = "w-full bg-white/20 backdrop-filter backdrop-blur-2xl border border-white/80 rounded-lg text-slate-800 placeholder-slate-400 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-200 px-4 py-3 text-base touch-manipulation"

GLASS_BUTTON_STYLE = "bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg px-6 py-3 transition-all duration-200 shadow-[0_4px_16px_0_rgba(31,38,135,0.10)] hover:shadow-[0_8px_32px_0_rgba(31,38,135,0.15)] active:scale-95 touch-manipulation"

GLASS_BUTTON_SECONDARY_STYLE = "bg-white/20 hover:bg-white/30 text-slate-700 font-semibold rounded-lg px-6 py-3 transition-all duration-200 border border-white/80 backdrop-filter backdrop-blur-2xl shadow-[0_4px_16px_0_rgba(31,38,135,0.10)] active:scale-95 touch-manipulation"

GLASS_BUTTON_TERTIARY_STYLE = "bg-transparent hover:bg-white/20 text-slate-700 font-semibold rounded-lg px-6 py-3 transition-all duration-200 border border-white/50 backdrop-filter backdrop-blur-md hover:backdrop-blur-xl active:scale-95 touch-manipulation"


# ============================================================
# GlassCard Component
# ============================================================

class GlassCard(ui.card):
    """Custom glass card with hardcore glassmorphism styling."""
    def __init__(self, title: str = "", subtitle: str = "", **kwargs):
        super().__init__(**kwargs)
        # 强制清除 NiceGUI 默认的卡片样式
        self.classes('no-shadow bg-transparent')
        
        # 核心玻璃配方 - 使用 inline styles 直接控制
        self.style(
            'background: rgba(255, 255, 255, 0.65); '
            'backdrop-filter: blur(20px) saturate(180%); '
            '-webkit-backdrop-filter: blur(20px) saturate(180%); '
            'border: 1px solid rgba(255, 255, 255, 0.8); '
            'box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1); '
            'border-radius: 16px;'
        )
        
        # 添加标题和副标题
        if title:
            with self:
                with ui.column().classes("gap-2"):
                    ui.label(title).classes(f"{GLASS_THEME['text_primary']} text-lg font-semibold")
                    if subtitle:
                        ui.label(subtitle).classes(f"{GLASS_THEME['text_secondary']} text-sm")


def glass_card(title: str = "", subtitle: str = "") -> GlassCard:
    """
    Create a frosted glass card with light theme.
    
    Args:
        title: Card title
        subtitle: Card subtitle
        
    Returns:
        A configured GlassCard element
    """
    return GlassCard(title=title, subtitle=subtitle)


def glass_column() -> ui.column:
    """Create a glassmorphism-styled column container."""
    col = ui.column()
    return col


def glass_row() -> ui.row:
    """Create a glassmorphism-styled row container."""
    row = ui.row()
    return row


# ============================================================
# GlassInput Components
# ============================================================

def glass_input(
    label: str = "",
    placeholder: str = "",
    value: str = "",
    on_change: Optional[Callable] = None
) -> ui.input:
    """
    Create a frosted glass input field.
    
    Args:
        label: Input label
        placeholder: Placeholder text
        value: Initial value
        on_change: Callback when value changes
        
    Returns:
        A configured ui.input element
    """
    inp = ui.input(label=label, placeholder=placeholder, value=value)
    inp.classes(GLASS_INPUT_STYLE)
    inp.props('outlined dense')
    inp.style('line-height: 1.5; min-height: 56px; max-height: 56px; overflow: hidden;')
    
    if on_change:
        inp.on_change(on_change)
    
    return inp


def glass_number(
    label: str = "",
    value: float = 0.0,
    on_change: Optional[Callable] = None
) -> ui.number:
    """Create a frosted glass number input."""
    num = ui.number(label=label, value=value)
    num.classes(GLASS_INPUT_STYLE)
    num.props('outlined dense')
    num.style('line-height: 1.5; max-height: 56px; overflow: hidden;')
    
    if on_change:
        num.on_change(on_change)
    
    return num


def glass_select(
    label: str = "",
    options: List[str] = None,
    value: str = "",
    on_change: Optional[Callable] = None
) -> ui.select:
    """Create a frosted glass select dropdown."""
    if options is None:
        options = []
    
    select = ui.select(label=label, options=options, value=value)
    select.classes(GLASS_INPUT_STYLE)
    select.props('outlined dense')
    
    if on_change:
        select.on_change(on_change)
    
    return select


# ============================================================
# Button Components
# ============================================================

def glass_button(
    text: str,
    on_click: Optional[Callable] = None,
    variant: str = "primary"
) -> ui.button:
    """
    Create a frosted glass button.
    
    Args:
        text: Button text
        on_click: Click callback
        variant: "primary", "secondary", or "tertiary"
        
    Returns:
        A configured ui.button element
    """
    if variant == "secondary":
        style = GLASS_BUTTON_SECONDARY_STYLE
    elif variant == "tertiary":
        style = GLASS_BUTTON_TERTIARY_STYLE
    else:
        style = GLASS_BUTTON_STYLE
    
    btn = ui.button(text)
    btn.classes(style)
    
    if on_click:
        btn.on_click(on_click)
    
    return btn


# ============================================================
# AppHeader Component
# ============================================================

def app_header() -> ui.header:
    """
    Create the application header with logo and title - hardcore glassmorphism.
    
    Returns:
        A configured ui.header element
    """
    header = ui.header()
    header.classes(
        f"bg-white/20 backdrop-filter backdrop-blur-2xl border-b border-white/80 {GLASS_THEME['shadow']} px-6 py-4"
    )
    
    with header:
        with ui.row().classes("items-center gap-4 w-full"):
            # Logo (text-based)
            ui.label("🧬").classes("text-3xl")
            
            # Title
            ui.label("SmartMold Pilot").classes(f"{GLASS_THEME['text_primary']} text-2xl font-bold")
            
            # Subtitle
            ui.label("v3.0").classes(f"{GLASS_THEME['text_secondary']} text-sm ml-auto")
    
    return header


# ============================================================
# AppDrawer (Sidebar) Component
# ============================================================

class AppDrawer:
    """Sidebar navigation drawer with hardcore glassmorphism styling - referencing design image."""
    
    def __init__(self):
        self.drawer = ui.left_drawer(fixed=False)
        self.drawer.classes(
            f"bg-white/20 backdrop-filter backdrop-blur-2xl border-r border-white/80 {GLASS_THEME['shadow']}"
        )
        
        with self.drawer:
            # Drawer header
            ui.label("Navigation").classes(
                f"{GLASS_THEME['text_accent']} text-lg font-semibold px-4 py-4"
            )
            
            ui.separator().classes("bg-white/50")
            
            # Navigation items
            with ui.column().classes("gap-2 px-4 py-4"):
                self._nav_item("Dashboard", "home", "/")
                self._nav_item("Scientific Molding", "science", "/scientific-molding")
                self._nav_item("Machine Check", "build", "/machine-check")
                
                ui.separator().classes("bg-white/50 my-4")
                
                self._nav_item("Settings", "settings", "/settings")
                self._nav_item("About", "info", "/about")
    
    def _nav_item(self, label: str, icon: str, route: str):
        """Create a navigation item."""
        btn = ui.button()
        btn.classes(
            f"w-full justify-start gap-3 {GLASS_THEME['text_primary']} hover:bg-white/30 transition-colors rounded-lg"
        )
        
        with btn:
            ui.icon(icon).classes(f"{GLASS_THEME['text_accent']}")
            ui.label(label)
        
        btn.on_click(lambda: ui.navigate.to(route))
    
    def toggle(self):
        """Toggle drawer visibility."""
        self.drawer.toggle()


# ============================================================
# Data Display Components
# ============================================================

def glass_stat_card(label: str, value: str, unit: str = "", icon: str = "") -> ui.card:
    """
    Create a statistics card displaying a key metric.
    
    Args:
        label: Metric label
        value: Metric value
        unit: Unit suffix
        icon: Icon code
        
    Returns:
        A configured ui.card element
    """
    card = glass_card()
    
    with card:
        with ui.row().classes("items-center justify-between w-full"):
            with ui.column().classes("gap-1"):
                ui.label(label).classes(f"{GLASS_THEME['text_secondary']} text-sm font-medium")
                with ui.row().classes("items-baseline gap-2"):
                    ui.label(value).classes(f"{GLASS_THEME['text_accent']} text-3xl font-bold")
                    if unit:
                        ui.label(unit).classes(f"{GLASS_THEME['text_secondary']} text-sm")
            
            if icon:
                ui.icon(icon).classes(f"{GLASS_THEME['text_accent']} text-4xl opacity-40")
    
    return card


def glass_info_panel(title: str, items: List[tuple] = None) -> ui.card:
    """
    Create an information panel with key-value pairs.
    
    Args:
        title: Panel title
        items: List of (key, value) tuples
        
    Returns:
        A configured ui.card element
    """
    if items is None:
        items = []
    
    card = glass_card(title)
    
    with card:
        with ui.column().classes("gap-3"):
            for key, value in items:
                with ui.row().classes("justify-between items-center"):
                    ui.label(key).classes(f"{GLASS_THEME['text_secondary']} text-sm font-medium")
                    ui.label(str(value)).classes(f"{GLASS_THEME['text_primary']} font-semibold")
    
    return card


def glass_alert(message: str, alert_type: str = "info") -> ui.element:
    """
    Create an alert/notification element.
    
    Args:
        message: Alert message
        alert_type: "info", "success", "warning", "error"
        
    Returns:
        A configured alert element
    """
    color_map = {
        "info": ("text-blue-600", "bg-blue-50/50"),
        "success": ("text-emerald-600", "bg-emerald-50/50"),
        "warning": ("text-amber-600", "bg-amber-50/50"),
        "error": ("text-red-600", "bg-red-50/50"),
    }
    
    text_color, bg_color = color_map.get(alert_type, color_map["info"])
    
    container = ui.element()
    container.classes(
        f"{bg_color} backdrop-blur-md border border-slate-200/40 rounded-lg p-4 {GLASS_THEME['shadow_sm']}"
    )
    
    with container:
        with ui.row().classes("items-start gap-3"):
            # Icon
            icon_map = {
                "info": "info",
                "success": "check_circle",
                "warning": "warning",
                "error": "error",
            }
            ui.icon(icon_map.get(alert_type, "info")).classes(text_color)
            
            # Message
            ui.label(message).classes(f"{GLASS_THEME['text_primary']}")
    
    return container


def glass_table(columns: List[str], rows: List[List] = None) -> ui.table:
    """
    Create a frosted glass table.
    
    Args:
        columns: Column headers
        rows: Table rows
        
    Returns:
        A configured ui.table element
    """
    if rows is None:
        rows = []
    
    # Build row data
    table_rows = []
    for row in rows:
        table_rows.append({col: row[i] if i < len(row) else "" for i, col in enumerate(columns)})
    
    table = ui.table(
        columns=[{"name": col, "label": col, "field": col} for col in columns],
        rows=table_rows
    )
    
    table.classes(f"bg-white/60 {GLASS_THEME['text_primary']}")
    
    return table


# ============================================================
# Layout Helpers
# ============================================================

def glass_background_layer():
    """
    Create the background layer with gradient and color blobs.
    Uses fixed positioning and negative z-index to stay behind content.
    """
    with ui.element('div').classes('fixed inset-0 -z-10'):
        # 1. 基础渐变底色 (灰蓝 -> 灰紫)
        ui.element('div').classes('absolute inset-0 bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50')
        
        # 2. 左上角的彩色光斑 (Teal - 翡翠绿)
        ui.element('div').style(
            'position: absolute; top: -10%; left: -10%; width: 50vw; height: 50vw; '
            'background: radial-gradient(circle, rgba(16, 185, 129, 0.3) 0%, rgba(255, 255, 255, 0) 70%); '
            'filter: blur(80px);'
        )
        
        # 3. 右下角的彩色光斑 (Purple)
        ui.element('div').style(
            'position: absolute; bottom: -10%; right: -10%; width: 60vw; height: 60vw; '
            'background: radial-gradient(circle, rgba(168, 85, 247, 0.3) 0%, rgba(255, 255, 255, 0) 70%); '
            'filter: blur(80px);'
        )


def glass_container() -> ui.column:
    """Create a main content container with relative positioning for mesh gradient."""
    container = ui.column()
    # Use relative positioning so glass_background_layer can be behind
    container.classes(f"w-full h-full p-8 gap-6 relative z-10")
    return container


def glass_form() -> ui.column:
    """Create a frosted glass form container."""
    form = ui.column()
    form.classes(f"{GLASS_CARD_STYLE} w-full max-w-2xl gap-4")
    return form


# ============================================================
# Chart Configuration Helper
# ============================================================

def get_plotly_light_config():
    """
    Return Plotly configuration for light theme.
    Use this when creating Plotly charts.
    
    Returns:
        dict with layout configuration
    """
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",  # Transparent background
        "plot_bgcolor": "rgba(255,255,255,0.3)",  # Subtle light background
        "font": {
            "family": "sans-serif",
            "size": 12,
            "color": "#1e293b",  # slate-800
        },
        "xaxis": {
            "gridcolor": "rgba(203, 213, 225, 0.3)",  # slate-300 with transparency
            "linecolor": "#cbd5e1",  # slate-300
            "zeroline": False,
        },
        "yaxis": {
            "gridcolor": "rgba(203, 213, 225, 0.3)",
            "linecolor": "#cbd5e1",
            "zeroline": False,
        },
        "hoverlabel": {
            "bgcolor": "#ffffff",
            "font_size": 13,
            "font_family": "sans-serif",
        },
        "margin": {"l": 50, "r": 50, "t": 50, "b": 50},
    }


# ============================================================
# Theme Setup
# ============================================================

def setup_glass_theme():
    """Apply hardcore frosted glass theme with touch-optimized interactions."""
    ui.colors(
        primary="#10b981",      # Emerald-500
        secondary="#64748b",    # Slate-500
        accent="#059669",       # Emerald-600
        positive="#10b981",
        negative="#ef4444",
        info="#0ea5e9",
        warning="#f59e0b",
    )
    
    # Apply mesh gradient + touch/mouse optimized CSS
    ui.add_css('''
    body {
        background: linear-gradient(135deg, #E0F7FA 0%, #F0F4F8 50%, #E1BEE7 100%) !important;
        min-height: 100vh;
        overflow-x: hidden;
        position: relative;
        -webkit-touch-callout: none;
        -webkit-user-select: none;
        user-select: none;
    }
    
    /* Left-top decorative blob */
    body::before {
        content: '';
        position: fixed;
        top: -100px;
        left: -150px;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(16, 185, 129, 0.25) 0%, transparent 70%);
        border-radius: 50%;
        filter: blur(80px);
        z-index: 0;
        pointer-events: none;
    }
    
    /* Right-bottom decorative blob */
    body::after {
        content: '';
        position: fixed;
        bottom: -100px;
        right: -150px;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(225, 190, 231, 0.25) 0%, transparent 70%);
        border-radius: 50%;
        filter: blur(80px);
        z-index: 0;
        pointer-events: none;
    }
    
    /* ============ 触摸优化 (Touch Optimization) ============ */
    
    /* 按钮 - 更大的触摸区域 (min 48px for touch) */
    button, .q-btn {
        min-height: 48px !important;
        min-width: 48px !important;
        padding: 12px 20px !important;
        font-size: 16px !important;
    }
    
    /* 输入框 - 大触摸区域 */
    input, textarea, select, .q-field {
        min-height: 48px !important;
        font-size: 16px !important;
        padding: 12px 16px !important;
    }
    
    /* 链接和可点击元素 - 最小 48x48px 触摸目标 */
    a, button, [role="button"], .clickable {
        min-width: 48px !important;
        min-height: 48px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    /* ============ 鼠标悬停效果 ============ */
    
    @media (hover: hover) and (pointer: fine) {
        /* 仅在可以悬停的设备上应用 (鼠标/触控板) */
        button:hover, .q-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 24px rgba(31, 38, 135, 0.2) !important;
        }
        
        a:hover, [role="button"]:hover {
            opacity: 0.9;
        }
    }
    
    /* ============ 触摸反馈 (Active State) ============ */
    
    button:active, .q-btn:active, 
    a:active, [role="button"]:active {
        transform: scale(0.98);
        transition: transform 0.1s ease-out;
    }
    
    /* 禁用文本选择误触 */
    button, [role="button"], .q-btn,
    input, textarea, select {
        -webkit-user-select: text;
        user-select: text;
    }
    
    /* 卡片 - 触摸友好间距 */
    .q-card {
        padding: 16px !important;
        margin-bottom: 16px !important;
    }
    
    /* 行间距 - 便于手指点击 */
    .q-item {
        min-height: 56px !important;
        padding: 12px 16px !important;
    }
    
    /* ============ 响应式优化 ============ */
    
    /* 超高分辨率 (2560x1600+) 平板优化 */
    @media (min-width: 2048px) {
        button, .q-btn {
            font-size: 18px !important;
            padding: 16px 28px !important;
        }
        
        input, textarea, select {
            font-size: 18px !important;
            padding: 14px 18px !important;
        }
        
        .q-item {
            min-height: 64px !important;
            padding: 16px 20px !important;
        }
    }
    
    /* 小屏幕手机 */
    @media (max-width: 480px) {
        button, .q-btn {
            width: 100% !important;
        }
        
        .gap-4 {
            gap: 8px !important;
        }
    }
    ''', shared=True)
    
    ui.dark_mode(False)


if __name__ == "__main__":
    # Demo mode for component testing
    setup_glass_theme()
    
    with ui.column().classes(f"w-full h-full {GLASS_THEME['bg_primary']}"):
        app_header()
        
        with ui.row().classes("w-full gap-4 p-8"):
            drawer = AppDrawer()
            
            with glass_container():
                ui.label("Component Preview").classes(f"{GLASS_THEME['text_primary']} text-2xl font-bold")
                
                with ui.row().classes("gap-4"):
                    glass_stat_card("Total Tests", "42", "sessions", "assessment")
                    glass_stat_card("Pass Rate", "95.2", "%", "trending_up")
                
                glass_info_panel("Machine Info", [
                    ("Brand", "Arburg"),
                    ("Tonnage", "150T"),
                    ("Status", "Active"),
                ])
                
                glass_alert("System initialized successfully", "success")
    
    ui.run(dark=False)
