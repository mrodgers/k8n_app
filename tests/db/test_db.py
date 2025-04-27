#!/usr/bin/env python
"""
Test script for database functionality.
"""

import os
import sys
import time

# Add the src directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, project_root)

# Now we can import from the research_system module
from src.research_system.models.db import (
    Database, ResearchTask, ResearchResult, generate_id, TinyDBDatabase
)

def test_tinydb():
    """Test the TinyDB implementation."""
    print("Testing TinyDB implementation...")
    
    # Ensure TinyDB is used
    os.environ["USE_POSTGRES"] = "false"
    
    # Create a database instance with a test-specific path
    test_db_path = os.path.join(os.path.dirname(os.path.dirname(script_dir)), "data", "test_tinydb.json")
    db = Database(db_path=test_db_path)
    
    # Verify it's a TinyDB instance
    if not isinstance(db.db, TinyDBDatabase):
        print("ERROR: Not using TinyDB backend")
        assert False, "Not using TinyDB backend"
    
    # Create a task
    task_id = generate_id()
    task = ResearchTask(
        id=task_id,
        title="Test Task",
        description="A test task for verifying TinyDB functionality"
    )
    
    created_task = db.create_task(task)
    assert created_task is not None, "Could not create task in TinyDB"
    
    # Retrieve the task
    retrieved_task = db.get_task(task_id)
    assert retrieved_task is not None, "Could not retrieve task from TinyDB"
    
    # Create a result
    result_id = generate_id()
    result = ResearchResult(
        id=result_id,
        task_id=task_id,
        content="Test result content",
        format="text",
        created_by="test_script"
    )
    
    created_result = db.create_result(result)
    assert created_result is not None, "Could not create result in TinyDB"
    
    # Retrieve the result
    retrieved_result = db.get_result(result_id)
    assert retrieved_result is not None, "Could not retrieve result from TinyDB"
    
    # List tasks
    tasks = db.list_tasks()
    assert len(tasks) > 0, "No tasks found in TinyDB"
    
    # Update task
    retrieved_task.status = "in_progress"
    updated = db.update_task(retrieved_task)
    assert updated is not None, "Task update failed in TinyDB"
    
    # Verify update
    updated_task = db.get_task(task_id)
    assert updated_task is not None, "Task not found after update"
    assert updated_task.status == "in_progress", "Task status not updated correctly"
    
    # Clean up
    deleted = db.delete_task(task_id)
    assert deleted, "Task deletion failed"
    
    # Verify deletion
    deleted_task = db.get_task(task_id)
    assert deleted_task is None, "Task not properly deleted from TinyDB"
    
    # Clean up the test file
    try:
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
    except Exception as e:
        print(f"Warning: Could not remove test database file: {e}")
    
    print("TinyDB tests passed!")

def test_auto_selection():
    """Test the automatic backend selection."""
    print("Testing automatic backend selection...")
    
    # Test TinyDB selection
    os.environ["USE_POSTGRES"] = "false"
    db = Database()
    tinydb_selected = isinstance(db.db, TinyDBDatabase)
    
    print(f"TinyDB auto-selection test {'passed' if tinydb_selected else 'failed'}")
    assert tinydb_selected, "TinyDB selection failed"
    
    # We can't test PostgreSQL selection properly without a connection
    # but we can verify the code doesn't crash
    try:
        os.environ["USE_POSTGRES"] = "true"
        os.environ["DATABASE_URL"] = "postgresql://fake:fake@localhost:5432/fake"
        db = Database()
        print("PostgreSQL selection test completed without errors")
    except Exception as e:
        print(f"PostgreSQL selection test error: {str(e)}")
    
    # Reset environment
    os.environ["USE_POSTGRES"] = "false"

if __name__ == "__main__":
    print("Running database tests...")
    print("========================")
    
    tinydb_passed = test_tinydb()
    selection_passed = test_auto_selection()
    
    print("\nSummary:")
    print("--------")
    print(f"TinyDB Test: {'PASSED' if tinydb_passed else 'FAILED'}")
    print(f"Auto Selection Test: {'PASSED' if selection_passed else 'FAILED'}")
    
    if tinydb_passed and selection_passed:
        print("\nAll tests PASSED!")
        sys.exit(0)
    else:
        print("\nSome tests FAILED!")
        sys.exit(1)