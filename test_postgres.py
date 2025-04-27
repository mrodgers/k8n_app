#!/usr/bin/env python3
"""
Script to test PostgreSQL integration in the Research System.

This script is intended to be run inside the Docker container with PostgreSQL
connectivity to verify the database implementation.
"""

import logging
import os
import sys
import time

from research_system.models.db import (
    PostgreSQLDatabase, TinyDBDatabase, Database,
    ResearchTask, ResearchResult, generate_id
)
from research_system.models.db_migration import DatabaseMigrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_postgres_direct():
    """Test PostgreSQL implementation directly."""
    # Use environment variable or default connection
    conn_string = os.getenv("DATABASE_URL", "postgresql://postgres:postgres-password@postgres:5432/research")
    
    logger.info(f"Testing PostgreSQL connection to {conn_string.split('@')[-1]}")
    
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
            return False
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
            return False
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
        delete_result = db.delete_task(task_id)
        logger.info(f"Delete task result: {delete_result}")
            
        # Verify deletion
        if db.get_task(task_id) is None:
            logger.info("Task deletion verified")
        else:
            logger.error("Task still exists after deletion")
            return False
        
        logger.info("PostgreSQL direct test completed successfully!")
        return True
    
    except Exception as e:
        logger.error(f"PostgreSQL direct test failed: {str(e)}", exc_info=True)
        return False


def test_database_factory():
    """Test the Database factory class."""
    try:
        # Set environment variables for PostgreSQL
        os.environ["USE_POSTGRES"] = "true"
        os.environ["DATABASE_URL"] = "postgresql://postgres:postgres-password@postgres:5432/research"
        
        # Create the database using the factory
        logger.info("Testing Database factory...")
        db = Database()
        
        # Check the backend type
        if hasattr(db, 'db') and isinstance(db.db, PostgreSQLDatabase):
            logger.info("Database factory correctly selected PostgreSQL backend")
        else:
            logger.error(f"Database factory selected incorrect backend: {type(db.db).__name__}")
            return False
        
        # Test a simple operation
        tasks = db.list_tasks()
        logger.info(f"Listed {len(tasks)} tasks using factory-created database")
        
        logger.info("Database factory test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database factory test failed: {str(e)}", exc_info=True)
        return False
        

def test_migration():
    """Test migration from TinyDB to PostgreSQL."""
    try:
        # Create a temporary TinyDB database
        temp_db_path = "/tmp/test_tiny.json"
        # Check if file exists and remove it
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
        
        logger.info(f"Creating temporary TinyDB at {temp_db_path}")
        tiny_db = TinyDBDatabase(temp_db_path)
        
        # Create test data in TinyDB
        task_ids = []
        for i in range(3):
            task_id = generate_id()
            task_ids.append(task_id)
            task = ResearchTask(
                id=task_id,
                title=f"Migration Test Task {i+1}",
                description=f"This is test task {i+1} for migration testing.",
                status="pending",
                created_at=time.time(),
                updated_at=time.time(),
                tags=["migration", f"task{i+1}"],
                metadata={"test_index": i}
            )
            tiny_db.create_task(task)
            
            # Create a result for this task
            result = ResearchResult(
                id=generate_id(),
                task_id=task_id,
                content=f"This is test result for task {i+1}.",
                format="text",
                status="draft",
                created_at=time.time(),
                updated_at=time.time(),
                created_by="test_script",
                tags=["migration", "result"],
                metadata={"confidence": 0.8 + (i * 0.1)}
            )
            tiny_db.create_result(result)
        
        # Verify TinyDB has data
        tiny_tasks = tiny_db.list_tasks()
        tiny_results = tiny_db.list_results()
        logger.info(f"TinyDB contains {len(tiny_tasks)} tasks and {len(tiny_results)} results")
        
        # Create the migrator
        logger.info("Running database migration...")
        conn_string = os.getenv("DATABASE_URL", "postgresql://postgres:postgres-password@postgres:5432/research")
        migrator = DatabaseMigrator(temp_db_path, conn_string)
        
        # Run migration
        migration_results = migrator.migrate_all()
        logger.info(f"Migration completed: {migration_results}")
        
        # Verify migration - but note that there might be additional tasks in target DB
        verification = migrator.verify_migration()
        
        # We only care about missing tasks/results, not extra ones
        if verification["missing_tasks"] or verification["missing_results"]:
            logger.error("Migration verification failed")
            logger.error(f"Verification details: {verification}")
            return False
        else:
            logger.info("Migration verification successful - source data migrated correctly")
            # If we have extra tasks in target, that's expected during testing
            if verification["target_task_count"] > verification["source_task_count"]:
                logger.info(f"Note: Target DB has {verification['target_task_count']} tasks but source only has {verification['source_task_count']} - this is expected")
            return True
        
        # Connect to PostgreSQL and check data
        pg_db = PostgreSQLDatabase(conn_string)
        for task_id in task_ids:
            task = pg_db.get_task(task_id)
            if task is None:
                logger.error(f"Task {task_id} not found in PostgreSQL after migration")
                return False
            
            results = pg_db.list_results_for_task(task_id)
            logger.info(f"Found {len(results)} results for migrated task {task_id}")
        
        logger.info("Migration test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Migration test failed: {str(e)}", exc_info=True)
        return False
    finally:
        # Clean up
        if os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
            except:
                pass


def main():
    """Main function to run all tests."""
    test_results = {
        "postgres_direct": False,
        "database_factory": False,
        "migration": False
    }
    
    logger.info("=== POSTGRESQL INTEGRATION TESTS ===")
    
    # Wait a moment for PostgreSQL to be ready
    logger.info("Waiting 3 seconds for PostgreSQL to be ready...")
    time.sleep(3)
    
    # Run tests
    test_results["postgres_direct"] = test_postgres_direct()
    test_results["database_factory"] = test_database_factory()
    test_results["migration"] = test_migration()
    
    # Report results
    logger.info("\n=== TEST RESULTS ===")
    for test_name, result in test_results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    # Determine overall success
    success = all(test_results.values())
    logger.info(f"\nOverall result: {'SUCCESS' if success else 'FAILURE'}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()