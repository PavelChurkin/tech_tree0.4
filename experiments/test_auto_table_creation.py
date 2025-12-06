#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify automatic table creation without calling init_db()
This simulates the production server scenario where init_db() is not called
"""

import os
import sys
import sqlite3
import tempfile
import shutil

# Add parent directory to path to import app functions
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_auto_table_creation():
    """Test that table is created automatically on first save/load operation"""
    # Create a temporary directory for test database
    test_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(test_dir, 'test_progress.db')

    print("=" * 60)
    print("Test: Automatic Table Creation (without init_db)")
    print("=" * 60)
    print(f"\nTest database path: {test_db_path}")

    try:
        # Import app module and temporarily replace DB_PATH
        import app
        original_db_path = app.DB_PATH
        app.DB_PATH = test_db_path

        # Step 1: Verify database doesn't exist
        print("\n[Step 1] Initial state check")
        assert not os.path.exists(test_db_path), "Database should not exist initially"
        print("✓ Database doesn't exist yet")

        # Step 2: Call save_progress_to_db without calling init_db()
        # This simulates what happens on production server
        print("\n[Step 2] Save progress without calling init_db()")
        test_progress = {
            'Кремень': True,
            'Огонь': True,
            'Копье': False
        }
        test_ip = '192.168.1.100'

        result = app.save_progress_to_db(test_ip, test_progress)
        assert result, "save_progress_to_db should return True"
        print(f"✓ Saved {len(test_progress)} technologies for IP {test_ip}")

        # Step 3: Verify database and table were created
        print("\n[Step 3] Verify database and table creation")
        assert os.path.exists(test_db_path), "Database file should be created"
        print(f"✓ Database file created: {test_db_path}")

        # Check table exists
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_progress'")
        table_exists = cursor.fetchone() is not None
        assert table_exists, "Table 'user_progress' should be created"
        print("✓ Table 'user_progress' exists")

        # Check index exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_user_ip'")
        index_exists = cursor.fetchone() is not None
        assert index_exists, "Index 'idx_user_ip' should be created"
        print("✓ Index 'idx_user_ip' exists")

        # Verify data was saved
        cursor.execute("SELECT COUNT(*) FROM user_progress WHERE user_ip = ?", (test_ip,))
        count = cursor.fetchone()[0]
        assert count == 3, f"Should have 3 records, got {count}"
        print(f"✓ Saved {count} records")

        conn.close()

        # Step 4: Test load_progress_from_db
        print("\n[Step 4] Load progress")
        loaded_progress = app.load_progress_from_db(test_ip)
        assert len(loaded_progress) == 2, f"Should load 2 completed technologies, got {len(loaded_progress)}"
        assert 'Кремень' in loaded_progress and loaded_progress['Кремень'] == True
        assert 'Огонь' in loaded_progress and loaded_progress['Огонь'] == True
        assert 'Копье' not in loaded_progress  # Not completed, so not returned
        print(f"✓ Loaded {len(loaded_progress)} completed technologies")
        print(f"  Progress: {loaded_progress}")

        # Step 5: Test with fresh database (delete and try load)
        print("\n[Step 5] Test load with fresh database (no init_db)")
        os.remove(test_db_path)
        assert not os.path.exists(test_db_path), "Database should be deleted"
        print("✓ Database deleted")

        loaded_progress = app.load_progress_from_db(test_ip)
        assert loaded_progress == {}, "Should return empty dict for new user"
        assert os.path.exists(test_db_path), "Database should be created by load operation"
        print("✓ Database and table created by load_progress_from_db")
        print(f"✓ Empty progress returned: {loaded_progress}")

        # Verify table was created
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_progress'")
        table_exists = cursor.fetchone() is not None
        assert table_exists, "Table should be created by load operation"
        conn.close()
        print("✓ Table created automatically by load operation")

        # Restore original DB_PATH
        app.DB_PATH = original_db_path

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nSummary:")
        print("- Table is created automatically on save operation")
        print("- Table is created automatically on load operation")
        print("- No need to call init_db() explicitly")
        print("- This will work on production servers (gunicorn/uwsgi)")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"\n🧹 Cleanup: Removed test directory {test_dir}")

if __name__ == '__main__':
    success = test_auto_table_creation()
    sys.exit(0 if success else 1)
