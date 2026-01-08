"""
SmartMold Pilot V3 - Database Initialization Script
Run this script to initialize the database and insert test data.

Usage:
    python init_db_script.py
"""

import asyncio
from datetime import datetime
from db import init_db, close_db, get_db_path
from models import Machine, Mold, ExperimentSession


async def init_database_and_test_data():
    """Initialize database and insert test data."""
    
    print("\n" + "="*80)
    print("SmartMold Pilot V3 - Database Initialization")
    print("="*80 + "\n")
    
    # Initialize database
    await init_db()
    
    try:
        # Check if test machine already exists
        existing_machine = await Machine.get_or_none(code="TEST-MACHINE-001")
        
        if existing_machine:
            print(f"✓ Test machine already exists: {existing_machine.code}")
        else:
            # Create test machine
            test_machine = await Machine.create(
                code="TEST-MACHINE-001",
                brand="Arburg",
                tonnage=150,
                screw_diameter=40.0,
                max_pressure=2000.0,  # MPa
                max_speed=200.0,  # mm/s
                intensification_ratio=1.5,
                theoretical_injection_weight=211.0,
            )
            print(f"✓ Created test machine: {test_machine.code}")
            print(f"  Brand: {test_machine.brand}")
            print(f"  Tonnage: {test_machine.tonnage}T")
            print(f"  Screw Diameter: {test_machine.screw_diameter}mm")
            print(f"  Max Pressure: {test_machine.max_pressure}MPa")
            print(f"  Max Speed: {test_machine.max_speed}mm/s")
        
        # Check if test mold already exists
        existing_mold = await Mold.get_or_none(code="TEST-MOLD-001")
        
        if existing_mold:
            print(f"\n✓ Test mold already exists: {existing_mold.code}")
        else:
            # Create test mold
            test_mold = await Mold.create(
                code="TEST-MOLD-001",
                cavity_count=4,
                material="PC",
                gate_type="Side Gate",
            )
            print(f"\n✓ Created test mold: {test_mold.code}")
            print(f"  Cavity Count: {test_mold.cavity_count}")
            print(f"  Material: {test_mold.material}")
            print(f"  Gate Type: {test_mold.gate_type}")
        
        # Create test experiment session
        machine = await Machine.get(code="TEST-MACHINE-001")
        mold = await Mold.get(code="TEST-MOLD-001")
        
        session_code = f"EXP-SCI-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        experiment_session = await ExperimentSession.create(
            session_code=session_code,
            machine=machine,
            mold=mold,
            snapshot_machine_data={
                "code": machine.code,
                "brand": machine.brand,
                "tonnage": machine.tonnage,
                "screw_diameter": machine.screw_diameter,
                "max_pressure": machine.max_pressure,
                "max_speed": machine.max_speed,
                "intensification_ratio": machine.intensification_ratio,
                "theoretical_injection_weight": machine.theoretical_injection_weight,
                "snapshot_time": datetime.now().isoformat(),
            },
            experiment_type="scientific_molding",
            status="in_progress",
            notes="Test experiment session for Scientific Molding module",
        )
        
        print(f"\n✓ Created test experiment session: {experiment_session.session_code}")
        print(f"  Type: {experiment_session.experiment_type}")
        print(f"  Status: {experiment_session.status}")
        print(f"  Snapshot captured at: {experiment_session.snapshot_machine_data['snapshot_time']}")
        
        print("\n" + "="*80)
        print("Database Summary")
        print("="*80)
        
        machine_count = await Machine.all().count()
        mold_count = await Mold.all().count()
        session_count = await ExperimentSession.all().count()
        
        print(f"\n✓ Total Machines: {machine_count}")
        print(f"✓ Total Molds: {mold_count}")
        print(f"✓ Total Experiment Sessions: {session_count}")
        
        print(f"\nDatabase location: {get_db_path()}")
        print("\n" + "="*80)
        print("✅ Database initialization completed successfully!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await close_db()


if __name__ == "__main__":
    # Run async initialization
    asyncio.run(init_database_and_test_data())
