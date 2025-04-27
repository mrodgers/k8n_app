#!/usr/bin/env python3
"""
Script to test PostgreSQL connectivity and operations.

This script tests the PostgreSQL database implementation directly, allowing
for debugging outside of the test suite context.
"""

import logging
import os
import sys
import time

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from src.research_system.models.db import PostgreSQLDatabase, ResearchTask, ResearchResult, generate_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to test PostgreSQL database."""
    # Set up the connection
    conn_string = os.getenv("DATABASE_URL", "postgresql://postgres:postgres-password@localhost:5432/research")
    logger.info(f"Connecting to PostgreSQL with: {conn_string}")
    
    try:
        # Initialize PostgreSQL DB
        db = PostgreSQLDatabase(conn_string)
        logger.info("Successfully connected to PostgreSQL")
        
        # Test basic operations
        logger.info("Testing basic operations...")
        
        # Create a task
        task_id = generate_id()
        task = ResearchTask(
            id=task_id,
            title="Test Task",
            description="This is a test task for PostgreSQL testing.",
            status="pending",
            created_at=time.time(),
            updated_at=time.time(),
            assigned_to="test_user",
            tags=["test", "postgresql"],
            metadata={"source": "test_script"}
        )
        
        db.create_task(task)
        logger.info(f"Created task with ID: {task_id}")
        
        # Get the task
        retrieved_task = db.get_task(task_id)
        if retrieved_task is None:
            logger.error("Failed to retrieve task")
        else:
            logger.info(f"Retrieved task: {retrieved_task.title}")
            
            # Test task update
            retrieved_task.status = "in_progress"
            retrieved_task.tags.append("updated")
            db.update_task(retrieved_task)
            logger.info("Updated task status and tags")
            
            # Verify update
            updated_task = db.get_task(task_id)
            logger.info(f"Task status: {updated_task.status}, tags: {updated_task.tags}")
        
        # Create a result
        result_id = generate_id()
        result = ResearchResult(
            id=result_id,
            task_id=task_id,
            content="This is a test result for PostgreSQL testing.",
            format="text",
            status="draft",
            created_at=time.time(),
            updated_at=time.time(),
            created_by="test_script",
            tags=["test", "result"],
            metadata={"confidence": 0.9}
        )
        
        db.create_result(result)
        logger.info(f"Created result with ID: {result_id}")
        
        # Get the result
        retrieved_result = db.get_result(result_id)
        if retrieved_result is None:
            logger.error("Failed to retrieve result")
        else:
            logger.info(f"Retrieved result: {retrieved_result.content[:30]}...")
        
        # List tasks and results
        tasks = db.list_tasks()
        logger.info(f"Retrieved {len(tasks)} tasks")
        
        # List by status
        in_progress_tasks = db.list_tasks(status="in_progress")
        logger.info(f"Retrieved {len(in_progress_tasks)} in-progress tasks")
        
        # List by tag
        tagged_tasks = db.list_tasks(tag="test")
        logger.info(f"Retrieved {len(tagged_tasks)} tasks with 'test' tag")
        
        # List results for task
        task_results = db.list_results_for_task(task_id)
        logger.info(f"Retrieved {len(task_results)} results for task {task_id}")
        
        # List all results
        all_results = db.list_results()
        logger.info(f"Retrieved {len(all_results)} total results")
        
        # Test result filtering
        draft_results = db.list_results(status="draft")
        logger.info(f"Retrieved {len(draft_results)} draft results")
        
        # Test deletion
        if db.delete_task(task_id):
            logger.info(f"Successfully deleted task {task_id}")
        else:
            logger.error(f"Failed to delete task {task_id}")
            
        # Verify deletion
        if db.get_task(task_id) is None:
            logger.info("Task deletion verified")
        else:
            logger.error("Task still exists after deletion")
        
        logger.info("PostgreSQL connectivity test completed successfully!")
    
    except Exception as e:
        logger.error(f"PostgreSQL test failed: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()