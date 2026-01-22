#!/bin/bash
# SmartMold Pilot V3 - Quick Start Guide
# This is a markdown version shown in terminal

cat << 'EOF'

╔══════════════════════════════════════════════════════════════════════╗
║                   SmartMold Pilot V3 - Quick Start                   ║
╚══════════════════════════════════════════════════════════════════════╝

📚 PROJECT STATUS: Step 2 & 3 Complete ✅

═══════════════════════════════════════════════════════════════════════
COMPLETED MODULES
═══════════════════════════════════════════════════════════════════════

✅ Step 1: Infrastructure
   - models.py (16 data tables with Tortoise-ORM)
   - db.py (SQLite initialization)
   - algorithms.py (9 core calculation functions)

✅ Step 2 & 3: UI Framework & Entry Point
   - ui_components.py (15+ glassmorphism components)
   - main.py (5-page routing with Dashboard)
   - README.md (complete documentation)
   - run.sh (application launcher)

═══════════════════════════════════════════════════════════════════════
FEATURES IMPLEMENTED
═══════════════════════════════════════════════════════════════════════

UI Components (ui_components.py):
  🎨 GlassCard                - Glassmorphism card container
  🎨 AppHeader               - App title bar with logo
  🎨 AppDrawer               - Sidebar navigation
  🎨 glass_input             - Styled input field
  🎨 glass_number            - Number input
  🎨 glass_select            - Dropdown select
  🎨 glass_button            - Primary/secondary buttons
  🎨 glass_stat_card         - Statistics display
  🎨 glass_info_panel        - Key-value info display
  🎨 glass_alert             - Alert/notification
  🎨 glass_table             - Data table

Pages (main.py):
  📄 Dashboard (/)            - DB stats + Recent experiments
  📄 Scientific Molding       - 6-step process (placeholder)
  📄 Machine Check            - Performance tests (placeholder)
  📄 Settings                 - Configuration (placeholder)
  📄 About                    - App metadata

Database Tables:
  🗄️  Machine                 - Injection molding machine
  🗄️  Mold                    - Mold specifications
  🗄️  ExperimentSession       - Experiment metadata + snapshot
  🗄️  ViscosityData           - Viscosity curve measurements
  🗄️  BalanceData             - Cavity balance data
  🗄️  PressureWindowData      - Pressure test data
  🗄️  InjectionWeightData     - Weight repeatability
  🗄️  InjectionSpeedData      - Speed linearity
  ... + 8 more tables

═══════════════════════════════════════════════════════════════════════
🚀 HOW TO RUN
═══════════════════════════════════════════════════════════════════════

OPTION 1: Using shell script
  $ chmod +x run.sh
  $ ./run.sh

OPTION 2: Direct command
  $ /Users/a/SmartMold_Pilot/.venv/bin/python3 -m nicegui main.py

OPTION 3: From Python REPL
  $ /Users/a/SmartMold_Pilot/.venv/bin/python3
  >>> import sys
  >>> sys.path.insert(0, '/Users/a/SmartMold_Pilot')
  >>> ui.run()

Open browser: http://localhost:8080

═══════════════════════════════════════════════════════════════════════
📊 DATABASE INITIALIZATION
═══════════════════════════════════════════════════════════════════════

The database is already initialized with test data:

Machine:     TEST-MACHINE-001 (Arburg 150T)
Mold:        TEST-MOLD-001 (4 cavities, PC)
Experiment:  EXP-SCI-20260104-* (snapshot captured)

No need to run init_db_script.py again unless you want to reset.

═══════════════════════════════════════════════════════════════════════
🎨 GLASSMORPHISM DESIGN SYSTEM
═══════════════════════════════════════════════════════════════════════

Colors:
  Primary Background:    slate-900 to slate-800 (gradient)
  Card Background:       white/5 (5% opacity)
  Backdrop Filter:       blur-md (medium blur)
  Border:                white/10 (10% opacity)
  Text Primary:          gray-100
  Accent Color:          cyan-400
  Success:               green-400
  Error:                 red-400

Styling Strategy:
  ✓ Dark mode only
  ✓ Rounded corners (rounded-xl)
  ✓ Subtle shadows (shadow-lg)
  ✓ High contrast text
  ✓ Responsive layout

═══════════════════════════════════════════════════════════════════════
📋 DASHBOARD DISPLAY
═══════════════════════════════════════════════════════════════════════

Home page shows:
  1. Database Connection Status (Green checkmark)
  2. Statistics Cards:
     - Total Machines: 1
     - Total Molds: 1
     - Total Experiments: 2+ (grows with test runs)
  3. Recent Experiments Table (5 latest with sorting)
  4. Active Machine Info Panel (TEST-MACHINE-001 specs)

═══════════════════════════════════════════════════════════════════════
🔧 INSTALLED DEPENDENCIES
═══════════════════════════════════════════════════════════════════════

Core:
  nicegui          - Web UI framework
  tortoise-orm     - Async ORM
  aiosqlite        - Async SQLite driver
  
Data/Visualization:
  pandas           - Data processing
  plotly           - Interactive charts
  openpyxl, xlrd   - Excel read support
  
Utilities:
  weasyprint       - PDF export (ready)

═══════════════════════════════════════════════════════════════════════
📝 FILE STRUCTURE
═══════════════════════════════════════════════════════════════════════

/Users/a/SmartMold_Pilot/
├── models.py                    # ORM models (700+ lines)
├── db.py                        # DB setup (70 lines)
├── algorithms.py                # Calculations (600+ lines)
├── ui_components.py             # UI library (500+ lines)
├── main.py                      # App entry (300+ lines)
├── init_db_script.py           # DB initializer
├── run.sh                       # Launcher
├── README.md                    # Full documentation
├── smartmold.db                # SQLite database
└── .venv/                      # Python environment

═══════════════════════════════════════════════════════════════════════
🎯 NEXT STEPS (ROADMAP)
═══════════════════════════════════════════════════════════════════════

Step 4: Scientific Molding Module
  [ ] Implement "粘度曲线" page (Viscosity Curve)
  [ ] Add data input table (NiceGUI table)
  [ ] Integrate Plotly chart (shear rate vs viscosity)
  [ ] Real-time calculation display

Step 5: Machine Performance Module
  [ ] Implement "射出重量" page (Weight Repeatability)
  [ ] Auto pass/fail logic (< 1% threshold)
  [ ] Add visual indicators (green/red)

Step 6: AI Integration
  [ ] Mock AI assistant panel
  [ ] Analysis suggestions based on experiment data
  [ ] JSON payload generation

═══════════════════════════════════════════════════════════════════════
❓ TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════

Q: "Address already in use" on port 8080?
A: Change port in main.py: ui.run_with(port=8081)

Q: "Database locked" error?
A: Delete .db-shm/.db-wal files and restart

Q: "Module not found"?
A: Always use: /Users/a/SmartMold_Pilot/.venv/bin/python3

═══════════════════════════════════════════════════════════════════════

✨ Ready to launch! Run: ./run.sh or main.py command above
📱 Open: http://localhost:8080
🎉 Enjoy SmartMold Pilot V3!

EOF
