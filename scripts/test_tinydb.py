#!/usr/bin/env python
"""
Simple test for TinyDB.
"""

import os
import sys
import uuid
import time
import json
from typing import Dict, List, Optional, Any, Union
from tinydb import TinyDB, Query

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
os.makedirs(data_dir, exist_ok=True)
db_path = os.path.join(data_dir, 'test_db.json')

print(f"Testing TinyDB at {db_path}")

# Set up the database
db = TinyDB(db_path)
tasks = db.table("tasks")
results = db.table("results")

# Clean up any existing data
tasks.truncate()
results.truncate()

# Helper function to generate a unique ID
def generate_id():
    return str(uuid.uuid4())

# Create a task
task_id = generate_id()
task = {
    "id": task_id,
    "title": "Test Task",
    "description": "This is a test task",
    "status": "pending",
    "created_at": time.time(),
    "updated_at": time.time(),
    "assigned_to": None,
    "tags": ["test"],
    "metadata": {"priority": 1}
}

tasks.insert(task)
print(f"Created task: {task_id}")

# Retrieve the task
Task = Query()
result = tasks.get(Task.id == task_id)
if result:
    print(f"Retrieved task: {result['title']}")
else:
    print("ERROR: Failed to retrieve task")
    sys.exit(1)

# Create a result
result_id = generate_id()
task_result = {
    "id": result_id,
    "task_id": task_id,
    "content": "This is a test result",
    "format": "text",
    "status": "draft",
    "created_at": time.time(),
    "updated_at": time.time(),
    "created_by": "test_script",
    "tags": ["test_result"],
    "metadata": {"confidence": 0.9}
}

results.insert(task_result)
print(f"Created result: {result_id}")

# Retrieve the result
Result = Query()
retrieved_result = results.get(Result.id == result_id)
if retrieved_result:
    print(f"Retrieved result for task: {retrieved_result['task_id']}")
else:
    print("ERROR: Failed to retrieve result")
    sys.exit(1)

# Update the task
task["status"] = "completed"
task["updated_at"] = time.time()
tasks.update(task, Task.id == task_id)
print(f"Updated task status to: completed")

# Clean up
tasks.remove(Task.id == task_id)
results.remove(Result.task_id == task_id)
print("Cleaned up test data")

# Verify deletion
result = tasks.get(Task.id == task_id)
if result:
    print("ERROR: Task not deleted properly")
    sys.exit(1)

print("TinyDB tests passed successfully!")