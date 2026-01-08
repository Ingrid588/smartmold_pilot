# SmartMold Pilot V3 - Setup & Run Guide

## 📋 Project Structure

```
SmartMold_Pilot/
├── models.py                  # Tortoise-ORM data models
├── db.py                      # Database initialization & connection
├── algorithms.py              # Core calculation algorithms
├── ui_components.py           # Glassmorphism UI component library
├── main.py                    # NiceGUI main entry point with routing
├── init_db_script.py         # Database initialization script
├── run.sh                     # Application launcher script
├── smartmold.db              # SQLite database (auto-generated)
└── .venv/                    # Python virtual environment
```

---

## 🚀 Quick Start

### 1. Prerequisites
Ensure you have Python 3.9+ and the virtual environment activated.

### 2. Initialize Database (First Time Only)
```bash
/Users/a/SmartMold_Pilot/.venv/bin/python3 init_db_script.py
```

Expected output:
```
[DB] Database initialized successfully
✓ Created test machine: TEST-MACHINE-001
✓ Created test mold: TEST-MOLD-001
✓ Created test experiment session: EXP-SCI-...
Database Summary:
✓ Total Machines: 1
✓ Total Molds: 1
✓ Total Experiment Sessions: 1
```

### 3. Run the Application
```bash
chmod +x run.sh
./run.sh
```

Or directly:
```bash
/Users/a/SmartMold_Pilot/.venv/bin/python3 -m nicegui main.py
```

The application will start on **http://localhost:8080**

---

## 📱 Features

### UI Components (ui_components.py)
- **GlassCard**: Glassmorphism-styled cards with backdrop blur
- **AppHeader**: Application header with logo and title
- **AppDrawer**: Sidebar navigation with links
- **glass_input, glass_number, glass_select**: Form inputs
- **glass_button**: Styled buttons (primary/secondary variants)
- **glass_stat_card**: Statistics display cards
- **glass_info_panel**: Information panels with key-value pairs
- **glass_alert**: Alert/notification elements
- **glass_table**: Data table with glass styling

### Styling System
- **Glassmorphism**: bg-white/5 + backdrop-blur-md + border-white/10
- **Colors**: Cyan (#06b6d4) accent, Slate-900 background, Gray-100 text
- **Theme**: Dark mode by default

### Pages (main.py)
1. **Dashboard** (`/`)
   - Database connection status
   - Statistics cards (Machines, Molds, Experiments)
   - Recent experiments table
   - Active machine information

2. **Scientific Molding** (`/scientific-molding`)
   - Placeholder for 6-step process (coming in Step 3)

3. **Machine Check** (`/machine-check`)
   - Placeholder for performance tests (coming in Step 3)

4. **Settings** (`/settings`)
   - Configuration page (placeholder)

5. **About** (`/about`)
   - App version and metadata

---

## 🗄️ Database

### Tables Created
- **Machine**: Injection molding machine info
- **Mold**: Mold specifications
- **ExperimentSession**: Experiment metadata with snapshot_machine_data
- **ViscosityData, BalanceData, PressureWindowData**: Scientific Molding data
- **InjectionWeightData, InjectionSpeedData, CheckRingData**: Machine Performance data

### Test Data
```
Machine: TEST-MACHINE-001
  - Brand: Arburg
  - Tonnage: 150T
  - Screw Diameter: 40mm
  - Max Pressure: 2000 MPa

Mold: TEST-MOLD-001
  - Cavity Count: 4
  - Material: PC
  - Gate Type: Side Gate
```

---

## 🔧 Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend/Backend | **NiceGUI** (Python web framework) |
| Database | **SQLite** + **Tortoise-ORM** |
| Styling | **Tailwind CSS** (Glassmorphism) |
| Charts | **Plotly** (ready for integration) |
| ORM | **Tortoise-ORM** (async-first) |

---

## 📝 Development Notes

### Adding New Pages
1. Create page function with `@ui.page("/route")`
2. Add navigation item in `AppDrawer._nav_item()`
3. Use `glass_container()` for layout

### Creating New Components
1. Define in `ui_components.py`
2. Use `GLASS_THEME` constants for consistent styling
3. Return NiceGUI elements (ui.card, ui.input, etc.)

### Database Operations
All database calls are async. Example:
```python
from models import Machine
machine = await Machine.get(code="TEST-MACHINE-001")
machines = await Machine.all()
count = await Machine.all().count()
```

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'nicegui'"
Solution: Use virtual environment Python
```bash
/Users/a/SmartMold_Pilot/.venv/bin/python3 main.py
```

### "Database connection error"
Solution: Run init_db_script.py first
```bash
/Users/a/SmartMold_Pilot/.venv/bin/python3 init_db_script.py
```

### Port 8080 already in use
Modify `main.py` line (in `ui.run_with()`):
```python
port=8081,  # Change to different port
```

---

## 🎯 Next Steps

- **Step 4**: Implement Scientific Molding module (Viscosity Curve page with Plotly chart)
- **Step 5**: Implement Machine Check module (Weight Repeatability with Pass/Fail logic)
- **Step 6**: Add AI mock assistant panel with optimization suggestions

---

## 📞 Support

For issues or questions, check:
1. Database initialization logs
2. Browser console (F12)
3. Terminal output for server errors
