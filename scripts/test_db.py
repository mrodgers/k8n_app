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
    
    # Create a database instance
    db = Database()
    
    # Verify it's a TinyDB instance
    if not isinstance(db.db, TinyDBDatabase):
        print("ERROR: Not using TinyDB backend")
        return False
    
    # Create a task
    task_id = generate_id()
    task = ResearchTask(
        id=task_id,
        title="Test Task",
        description="A test task for verifying TinyDB functionality"
    )
    
    db.create_task(task)
    
    # Retrieve the task
    retrieved_task = db.get_task(task_id)
    if not retrieved_task:
        print("ERROR: Could not retrieve task from TinyDB")
        return False
    
    # Create a result
    result_id = generate_id()
    result = ResearchResult(
        id=result_id,
        task_id=task_id,
        content="Test result content",
        format="text",
        created_by="test_script"
    )
    
    db.create_result(result)
    
    # Retrieve the result
    retrieved_result = db.get_result(result_id)
    if not retrieved_result:
        print("ERROR: Could not retrieve result from TinyDB")
        return False
    
    # List tasks
    tasks = db.list_tasks()
    if not tasks or len(tasks) == 0:
        print("ERROR: No tasks found in TinyDB")
        return False
    
    # Update task
    retrieved_task.status = "in_progress"
    db.update_task(retrieved_task)
    
    # Verify update
    updated_task = db.get_task(task_id)
    if not updated_task or updated_task.status != "in_progress":
        print("ERROR: Task update failed in TinyDB")
        return False
    
    # Clean up
    db.delete_task(task_id)
    
    # Verify deletion
    deleted_task = db.get_task(task_id)
    if deleted_task:
        print("ERROR: Task not deleted from TinyDB")
        return False
    
    print("TinyDB tests passed!")
    return True

def test_auto_selection():
    """Test the automatic backend selection."""
    print("Testing automatic backend selection...")
    
    # Test TinyDB selection
    os.environ["USE_POSTGRES"] = "false"
    db = Database()
    tinydb_selected = isinstance(db.db, TinyDBDatabase)
    
    print(f"TinyDB auto-selection test {'passed' if tinydb_selected else 'failed'}")
    
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
    return tinydb_selected

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