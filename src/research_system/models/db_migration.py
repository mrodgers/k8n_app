"""
Database Migration Utility for Research System.

This script provides utilities for migrating data from TinyDB to PostgreSQL.
"""

import os
import logging
import time
from typing import List, Optional, Dict, Any
import json
import argparse

from research_system.models.db import TinyDBDatabase, PostgreSQLDatabase, ResearchTask, ResearchResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """
    Utility class for migrating data between database backends.
    """
    
    def __init__(
        self, 
        source_db_path: str = "./data/research.json", 
        target_connection_string: Optional[str] = None
    ):
        """
        Initialize the database migrator.
        
        Args:
            source_db_path: Path to the TinyDB database file.
            target_connection_string: PostgreSQL connection string. If not provided,
                                    will use the DATABASE_URL environment variable.
        """
        self.source_db = TinyDBDatabase(source_db_path)
        self.target_db = PostgreSQLDatabase(target_connection_string)
        logger.info(f"Initialized migrator from {source_db_path} to PostgreSQL")
    
    def migrate_tasks(self) -> int:
        """
        Migrate all tasks from TinyDB to PostgreSQL.
        
        Returns:
            Number of tasks migrated.
        """
        tasks = self.source_db.list_tasks()
        logger.info(f"Found {len(tasks)} tasks to migrate")
        
        migrated_count = 0
        for task in tasks:
            try:
                # Check if task already exists in the target
                existing_task = self.target_db.get_task(task.id)
                if existing_task:
                    logger.warning(f"Task {task.id} already exists in target database, skipping")
                    continue
                
                # Create the task in the target database
                self.target_db.create_task(task)
                migrated_count += 1
                logger.info(f"Migrated task {task.id}: {task.title}")
            except Exception as e:
                logger.error(f"Error migrating task {task.id}: {str(e)}")
        
        logger.info(f"Successfully migrated {migrated_count} tasks")
        return migrated_count
    
    def migrate_results(self) -> int:
        """
        Migrate all results from TinyDB to PostgreSQL.
        
        Returns:
            Number of results migrated.
        """
        results = self.source_db.list_results()
        logger.info(f"Found {len(results)} results to migrate")
        
        migrated_count = 0
        for result in results:
            try:
                # Check if result already exists in the target
                existing_result = self.target_db.get_result(result.id)
                if existing_result:
                    logger.warning(f"Result {result.id} already exists in target database, skipping")
                    continue
                
                # Verify that the associated task exists
                task = self.target_db.get_task(result.task_id)
                if not task:
                    logger.warning(f"Result {result.id} references task {result.task_id} "
                                 f"which does not exist in target database")
                    # We could create a placeholder task here, but for now we'll skip
                    continue
                
                # Create the result in the target database
                self.target_db.create_result(result)
                migrated_count += 1
                logger.info(f"Migrated result {result.id} for task {result.task_id}")
            except Exception as e:
                logger.error(f"Error migrating result {result.id}: {str(e)}")
        
        logger.info(f"Successfully migrated {migrated_count} results")
        return migrated_count
    
    def migrate_all(self) -> Dict[str, int]:
        """
        Migrate all data from TinyDB to PostgreSQL.
        
        Returns:
            Dictionary with counts of migrated items by type.
        """
        start_time = time.time()
        logger.info("Starting full database migration")
        
        # First migrate tasks, then results (due to foreign key constraints)
        task_count = self.migrate_tasks()
        result_count = self.migrate_results()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        logger.info(f"Migration completed in {total_time:.2f} seconds")
        
        return {
            "tasks": task_count,
            "results": result_count,
            "total_time": total_time
        }
    
    def verify_migration(self) -> Dict[str, Any]:
        """
        Verify that the migration was successful by comparing record counts.
        
        Returns:
            Dictionary with verification results.
        """
        source_tasks = self.source_db.list_tasks()
        target_tasks = self.target_db.list_tasks()
        
        source_results = self.source_db.list_results()
        target_results = self.target_db.list_results()
        
        verification = {
            "source_task_count": len(source_tasks),
            "target_task_count": len(target_tasks),
            "source_result_count": len(source_results),
            "target_result_count": len(target_results),
            "tasks_match": len(source_tasks) == len(target_tasks),
            "results_match": len(source_results) == len(target_results),
            "missing_tasks": [],
            "missing_results": []
        }
        
        # Check for missing tasks
        source_task_ids = {task.id for task in source_tasks}
        target_task_ids = {task.id for task in target_tasks}
        missing_task_ids = source_task_ids - target_task_ids
        verification["missing_tasks"] = list(missing_task_ids)
        
        # Check for missing results
        source_result_ids = {result.id for result in source_results}
        target_result_ids = {result.id for result in target_results}
        missing_result_ids = source_result_ids - target_result_ids
        verification["missing_results"] = list(missing_result_ids)
        
        verification["all_verified"] = (
            verification["tasks_match"] and 
            verification["results_match"] and
            not verification["missing_tasks"] and
            not verification["missing_results"]
        )
        
        if verification["all_verified"]:
            logger.info("Migration verification successful: all records transferred")
        else:
            logger.warning("Migration verification found discrepancies")
            if verification["missing_tasks"]:
                logger.warning(f"{len(verification['missing_tasks'])} tasks missing from target")
            if verification["missing_results"]:
                logger.warning(f"{len(verification['missing_results'])} results missing from target")
        
        return verification


def run_migration(source_path: str, target_connection: str, verify: bool = True) -> None:
    """
    Run the database migration.
    
    Args:
        source_path: Path to the TinyDB database file
        target_connection: PostgreSQL connection string
        verify: Whether to verify the migration after completion
    """
    try:
        migrator = DatabaseMigrator(source_path, target_connection)
        results = migrator.migrate_all()
        
        logger.info(f"Migration summary:")
        logger.info(f"  Tasks migrated: {results['tasks']}")
        logger.info(f"  Results migrated: {results['results']}")
        logger.info(f"  Total time: {results['total_time']:.2f} seconds")
        
        if verify:
            verification = migrator.verify_migration()
            if verification["all_verified"]:
                logger.info("Migration verification: SUCCESS")
            else:
                logger.warning("Migration verification: FAILED")
                logger.warning(f"  Source tasks: {verification['source_task_count']}")
                logger.warning(f"  Target tasks: {verification['target_task_count']}")
                logger.warning(f"  Source results: {verification['source_result_count']}")
                logger.warning(f"  Target results: {verification['target_result_count']}")
                
                if verification["missing_tasks"]:
                    logger.warning(f"  Missing tasks: {len(verification['missing_tasks'])}")
                if verification["missing_results"]:
                    logger.warning(f"  Missing results: {len(verification['missing_results'])}")
    
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate TinyDB data to PostgreSQL")
    parser.add_argument("--source", default="./data/research.json",
                       help="Path to the TinyDB database file")
    parser.add_argument("--target", 
                       help="PostgreSQL connection string (overrides DATABASE_URL env var)")
    parser.add_argument("--skip-verify", action="store_true",
                       help="Skip migration verification")
    
    args = parser.parse_args()
    
    # If target is not provided, use environment variable
    target_conn = args.target or os.getenv("DATABASE_URL")
    if not target_conn:
        logger.error("No PostgreSQL connection string provided. "
                   "Use --target or set DATABASE_URL environment variable.")
        exit(1)
    
    run_migration(args.source, target_conn, not args.skip_verify)