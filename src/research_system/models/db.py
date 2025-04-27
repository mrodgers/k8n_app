"""
Database Implementation for the Research System.

This module contains the database implementation for storing research tasks and results.
It supports both TinyDB (for development/testing) and PostgreSQL (for production) backends.
"""

import logging
import os
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure data directory exists for TinyDB
os.makedirs("./data", exist_ok=True)

# Models
class ResearchTask(BaseModel):
    """Model representing a research task."""
    id: str
    title: str
    description: str
    status: str = "pending"  # pending, in_progress, completed, failed
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    assigned_to: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self):
        """Convert the task to a dictionary."""
        return self.dict()
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create a task from a dictionary."""
        return cls(**data)

class ResearchResult(BaseModel):
    """Model representing a research result."""
    id: str
    task_id: str
    content: str
    format: str = "text"  # text, json, html, etc.
    status: str = "draft"  # draft, reviewed, final
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self):
        """Convert the result to a dictionary."""
        return self.dict()
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create a result from a dictionary."""
        return cls(**data)

class TinyDBDatabase:
    """
    TinyDB implementation of the research database.
    
    This class provides methods for storing and retrieving research tasks and results
    using TinyDB. Primarily intended for development and testing environments.
    """
    
    def __init__(self, db_path: str = "./data/research.json"):
        """
        Initialize the TinyDB database.
        
        Args:
            db_path: The path to the database file.
        """
        from tinydb import TinyDB, Query
        self.db_path = db_path
        self.db = TinyDB(db_path)
        self.tasks = self.db.table("tasks")
        self.results = self.db.table("results")
        self.Query = Query
        logger.info(f"TinyDB initialized at {db_path}")
    
    # Task methods
    def create_task(self, task: ResearchTask) -> ResearchTask:
        """
        Create a new task.
        
        Args:
            task: The task to create.
            
        Returns:
            The created task.
        """
        task.updated_at = time.time()
        self.tasks.insert(task.to_dict())
        logger.info(f"Created task: {task.id}")
        return task
    
    def get_task(self, task_id: str) -> Optional[ResearchTask]:
        """
        Get a task by ID.
        
        Args:
            task_id: The ID of the task.
            
        Returns:
            The task with the specified ID, or None if not found.
        """
        Task = self.Query()
        result = self.tasks.get(Task.id == task_id)
        if result is None:
            return None
        return ResearchTask.from_dict(result)
    
    def update_task(self, task: ResearchTask) -> ResearchTask:
        """
        Update a task.
        
        Args:
            task: The task to update.
            
        Returns:
            The updated task.
            
        Raises:
            ValueError: If the task does not exist.
        """
        Task = self.Query()
        task.updated_at = time.time()
        if not self.tasks.update(task.to_dict(), Task.id == task.id):
            raise ValueError(f"Task not found: {task.id}")
        logger.info(f"Updated task: {task.id}")
        return task
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.
        
        Args:
            task_id: The ID of the task to delete.
            
        Returns:
            True if the task was deleted, False if it did not exist.
        """
        Task = self.Query()
        count = self.tasks.remove(Task.id == task_id)
        if count > 0:
            logger.info(f"Deleted task: {task_id}")
            return True
        return False
    
    def list_tasks(self, status: Optional[str] = None, assigned_to: Optional[str] = None, 
                  tag: Optional[str] = None) -> List[ResearchTask]:
        """
        List tasks, optionally filtered by status, assignment, or tag.
        
        Args:
            status: Optional status filter.
            assigned_to: Optional assignment filter.
            tag: Optional tag filter.
            
        Returns:
            A list of tasks matching the filters.
        """
        Task = self.Query()
        query_parts = []
        
        if status:
            query_parts.append(Task.status == status)
        
        if assigned_to:
            query_parts.append(Task.assigned_to == assigned_to)
        
        if tag:
            query_parts.append(Task.tags.any([tag]))
        
        if query_parts:
            # Combine all query parts with logical AND
            combined_query = query_parts[0]
            for part in query_parts[1:]:
                combined_query = combined_query & part
            
            results = self.tasks.search(combined_query)
        else:
            results = self.tasks.all()
        
        return [ResearchTask.from_dict(result) for result in results]
    
    # Result methods
    def create_result(self, result: ResearchResult) -> ResearchResult:
        """
        Create a new result.
        
        Args:
            result: The result to create.
            
        Returns:
            The created result.
        """
        result.updated_at = time.time()
        self.results.insert(result.to_dict())
        logger.info(f"Created result: {result.id} for task: {result.task_id}")
        return result
    
    def get_result(self, result_id: str) -> Optional[ResearchResult]:
        """
        Get a result by ID.
        
        Args:
            result_id: The ID of the result.
            
        Returns:
            The result with the specified ID, or None if not found.
        """
        Result = self.Query()
        result = self.results.get(Result.id == result_id)
        if result is None:
            return None
        return ResearchResult.from_dict(result)
    
    def update_result(self, result: ResearchResult) -> ResearchResult:
        """
        Update a result.
        
        Args:
            result: The result to update.
            
        Returns:
            The updated result.
            
        Raises:
            ValueError: If the result does not exist.
        """
        Result = self.Query()
        result.updated_at = time.time()
        if not self.results.update(result.to_dict(), Result.id == result.id):
            raise ValueError(f"Result not found: {result.id}")
        logger.info(f"Updated result: {result.id}")
        return result
    
    def delete_result(self, result_id: str) -> bool:
        """
        Delete a result.
        
        Args:
            result_id: The ID of the result to delete.
            
        Returns:
            True if the result was deleted, False if it did not exist.
        """
        Result = self.Query()
        count = self.results.remove(Result.id == result_id)
        if count > 0:
            logger.info(f"Deleted result: {result_id}")
            return True
        return False
    
    def list_results_for_task(self, task_id: str) -> List[ResearchResult]:
        """
        List all results for a specific task.
        
        Args:
            task_id: The ID of the task.
            
        Returns:
            A list of results for the specified task.
        """
        Result = self.Query()
        results = self.results.search(Result.task_id == task_id)
        return [ResearchResult.from_dict(result) for result in results]
    
    def list_results(self, status: Optional[str] = None, created_by: Optional[str] = None,
                    tag: Optional[str] = None) -> List[ResearchResult]:
        """
        List results, optionally filtered by status, creator, or tag.
        
        Args:
            status: Optional status filter.
            created_by: Optional creator filter.
            tag: Optional tag filter.
            
        Returns:
            A list of results matching the filters.
        """
        Result = self.Query()
        query_parts = []
        
        if status:
            query_parts.append(Result.status == status)
        
        if created_by:
            query_parts.append(Result.created_by == created_by)
        
        if tag:
            query_parts.append(Result.tags.any([tag]))
        
        if query_parts:
            # Combine all query parts with logical AND
            combined_query = query_parts[0]
            for part in query_parts[1:]:
                combined_query = combined_query & part
            
            results = self.results.search(combined_query)
        else:
            results = self.results.all()
        
        return [ResearchResult.from_dict(result) for result in results]


class PostgreSQLDatabase:
    """
    PostgreSQL implementation of the research database.
    
    This class provides methods for storing and retrieving research tasks and results
    using PostgreSQL. Recommended for production environments, especially in Kubernetes.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize the PostgreSQL database.
        
        Args:
            connection_string: The database connection string. If not provided,
                              will use the DATABASE_URL environment variable.
        """
        import psycopg2
        import psycopg2.extras
        
        self.connection_string = connection_string or os.getenv(
            "DATABASE_URL", 
            "postgresql://postgres:postgres@localhost:5432/research"
        )
        
        # Initialize connection pool (will be created on first use)
        self.conn = None
        self._init_db()
        logger.info(f"PostgreSQL initialized with connection to {self.connection_string.split('@')[-1]}")
    
    def _init_db(self):
        """Initialize the database schema if it doesn't exist."""
        import psycopg2
        
        # Connect to the database
        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.conn.autocommit = True
            
            # Create tables if they don't exist
            self._create_tables()
            
        except psycopg2.Error as e:
            logger.error(f"Error connecting to PostgreSQL: {str(e)}")
            raise
    
    def _create_tables(self):
        """Create the necessary tables if they don't exist."""
        # Table creation SQL
        create_tasks_table = """
        CREATE TABLE IF NOT EXISTS tasks (
            id VARCHAR(64) PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at DOUBLE PRECISION NOT NULL,
            updated_at DOUBLE PRECISION NOT NULL,
            assigned_to VARCHAR(64),
            tags JSONB DEFAULT '[]',
            metadata JSONB DEFAULT '{}'
        );
        """
        
        create_results_table = """
        CREATE TABLE IF NOT EXISTS results (
            id VARCHAR(64) PRIMARY KEY,
            task_id VARCHAR(64) NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            format VARCHAR(20) NOT NULL DEFAULT 'text',
            status VARCHAR(20) NOT NULL DEFAULT 'draft',
            created_at DOUBLE PRECISION NOT NULL,
            updated_at DOUBLE PRECISION NOT NULL,
            created_by VARCHAR(64),
            tags JSONB DEFAULT '[]',
            metadata JSONB DEFAULT '{}'
        );
        """
        
        # Create index for faster task_id lookups
        create_task_id_index = """
        CREATE INDEX IF NOT EXISTS results_task_id_idx ON results(task_id);
        """
        
        # Execute the SQL
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(create_tasks_table)
                cursor.execute(create_results_table)
                cursor.execute(create_task_id_index)
            self.conn.commit()
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            raise
    
    def _get_connection(self):
        """Get a database connection, reconnecting if necessary."""
        import psycopg2
        
        try:
            if self.conn is None or self.conn.closed:
                self.conn = psycopg2.connect(self.connection_string)
                self.conn.autocommit = False
            return self.conn
        except psycopg2.Error as e:
            logger.error(f"Error reconnecting to PostgreSQL: {str(e)}")
            raise
    
    def _execute_with_retry(self, operation_name, callback, max_retries=3):
        """Execute a database operation with retry logic."""
        import psycopg2
        
        retries = 0
        while retries < max_retries:
            try:
                conn = self._get_connection()
                result = callback(conn)
                if not conn.closed:
                    conn.commit()
                return result
            except psycopg2.OperationalError as e:
                logger.warning(f"Operational error in {operation_name}: {str(e)}. Retrying...")
                self.conn = None  # Force reconnection
                retries += 1
                if retries >= max_retries:
                    logger.error(f"Failed to execute {operation_name} after {max_retries} retries")
                    raise
                time.sleep(0.5 * retries)  # Exponential backoff
            except Exception as e:
                logger.error(f"Error in {operation_name}: {str(e)}")
                if not conn.closed:
                    conn.rollback()
                raise
    
    # Task methods
    def create_task(self, task: ResearchTask) -> ResearchTask:
        """
        Create a new task.
        
        Args:
            task: The task to create.
            
        Returns:
            The created task.
        """
        import psycopg2.extras
        
        def _create(conn):
            task.updated_at = time.time()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO tasks (id, title, description, status, created_at, updated_at, 
                                     assigned_to, tags, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        task.id,
                        task.title,
                        task.description,
                        task.status,
                        task.created_at,
                        task.updated_at,
                        task.assigned_to,
                        json.dumps(task.tags),
                        json.dumps(task.metadata)
                    )
                )
            return task
        
        result = self._execute_with_retry("create_task", _create)
        logger.info(f"Created task: {task.id}")
        return result
    
    def get_task(self, task_id: str) -> Optional[ResearchTask]:
        """
        Get a task by ID.
        
        Args:
            task_id: The ID of the task.
            
        Returns:
            The task with the specified ID, or None if not found.
        """
        import psycopg2.extras
        
        def _get(conn):
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, title, description, status, created_at, updated_at, 
                           assigned_to, tags, metadata
                    FROM tasks
                    WHERE id = %s
                    """,
                    (task_id,)
                )
                row = cursor.fetchone()
                
                if row is None:
                    return None
                
                # Convert JSONB to Python data types
                data = dict(row)
                
                # Handle tags field
                if data['tags'] is None:
                    data['tags'] = []
                elif isinstance(data['tags'], str):
                    data['tags'] = json.loads(data['tags'])
                # For PostgreSQL's json/jsonb type
                elif hasattr(data['tags'], '__iter__') and not isinstance(data['tags'], (str, bytes)):
                    # Already a proper iterable object, no conversion needed
                    pass
                    
                # Handle metadata field
                if data['metadata'] is None:
                    data['metadata'] = {}
                elif isinstance(data['metadata'], str):
                    data['metadata'] = json.loads(data['metadata'])
                # For PostgreSQL's json/jsonb type
                elif hasattr(data['metadata'], 'keys') and callable(data['metadata'].keys):
                    # Already a dict-like object, no conversion needed
                    pass
                
                return ResearchTask.from_dict(data)
        
        return self._execute_with_retry("get_task", _get)
    
    def update_task(self, task: ResearchTask) -> ResearchTask:
        """
        Update a task.
        
        Args:
            task: The task to update.
            
        Returns:
            The updated task.
            
        Raises:
            ValueError: If the task does not exist.
        """
        import psycopg2.extras
        
        def _update(conn):
            task.updated_at = time.time()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE tasks
                    SET title = %s, description = %s, status = %s, updated_at = %s, 
                        assigned_to = %s, tags = %s, metadata = %s
                    WHERE id = %s
                    """,
                    (
                        task.title,
                        task.description,
                        task.status,
                        task.updated_at,
                        task.assigned_to,
                        json.dumps(task.tags),
                        json.dumps(task.metadata),
                        task.id
                    )
                )
                
                if cursor.rowcount == 0:
                    raise ValueError(f"Task not found: {task.id}")
            
            return task
        
        result = self._execute_with_retry("update_task", _update)
        logger.info(f"Updated task: {task.id}")
        return result
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.
        
        Args:
            task_id: The ID of the task to delete.
            
        Returns:
            True if the task was deleted, False if it did not exist.
        """
        def _delete(conn):
            # First check if the task exists
            try:
                with conn.cursor() as check_cursor:
                    check_cursor.execute(
                        """
                        SELECT COUNT(*) FROM tasks WHERE id = %s
                        """,
                        (task_id,)
                    )
                    result = check_cursor.fetchone()
                    if result is None:
                        logger.warning(f"Task {task_id} check query returned None")
                        return False
                        
                    count = result[0]
                    if count == 0:
                        logger.warning(f"Task {task_id} does not exist, nothing to delete")
                        return False
                    
                # If we reached here, the task exists, so delete it
                with conn.cursor() as cursor:
                    # Since we have ON DELETE CASCADE on the foreign key constraint,
                    # we don't need to manually delete the results - the database will do it.
                    # Just delete the task directly
                    cursor.execute(
                        """
                        DELETE FROM tasks
                        WHERE id = %s
                        """,
                        (task_id,)
                    )
                    
                    deleted = cursor.rowcount > 0
                    return deleted
            except Exception as e:
                logger.error(f"Error deleting task {task_id}: {str(e)}")
                return False
        
        result = self._execute_with_retry("delete_task", _delete)
        if result:
            logger.info(f"Deleted task: {task_id}")
        return result
    
    def list_tasks(self, status: Optional[str] = None, assigned_to: Optional[str] = None,
                  tag: Optional[str] = None) -> List[ResearchTask]:
        """
        List tasks, optionally filtered by status, assignment, or tag.
        
        Args:
            status: Optional status filter.
            assigned_to: Optional assignment filter.
            tag: Optional tag filter.
            
        Returns:
            A list of tasks matching the filters.
        """
        import psycopg2.extras
        
        def _list(conn):
            try:
                # Check if table exists
                with conn.cursor() as check_cursor:
                    check_cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = current_schema()
                            AND table_name = 'tasks'
                        )
                    """)
                    table_exists = check_cursor.fetchone()[0]
                    if not table_exists:
                        logger.warning("Tasks table does not exist in the current schema")
                        return []
                
                # Build the query dynamically based on filters
                query = """
                    SELECT id, title, description, status, created_at, updated_at, 
                           assigned_to, tags, metadata
                    FROM tasks
                    WHERE 1=1
                """
                params = []
                
                if status:
                    query += " AND status = %s"
                    params.append(status)
                
                if assigned_to:
                    query += " AND assigned_to = %s"
                    params.append(assigned_to)
                
                if tag:
                    query += " AND tags @> %s::jsonb"
                    params.append(json.dumps([tag]))
                
                query += " ORDER BY updated_at DESC"
                
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    
                    tasks = []
                    for row in rows:
                        try:
                            data = dict(row)
                            
                            # Handle tags field
                            if data['tags'] is None:
                                data['tags'] = []
                            elif isinstance(data['tags'], str):
                                data['tags'] = json.loads(data['tags'])
                            # For PostgreSQL's json/jsonb type
                            elif hasattr(data['tags'], '__iter__') and not isinstance(data['tags'], (str, bytes)):
                                # Already a proper iterable object, no conversion needed
                                pass
                            
                            # Handle metadata field
                            if data['metadata'] is None:
                                data['metadata'] = {}
                            elif isinstance(data['metadata'], str):
                                data['metadata'] = json.loads(data['metadata'])
                            # For PostgreSQL's json/jsonb type
                            elif hasattr(data['metadata'], 'keys') and callable(data['metadata'].keys):
                                # Already a dict-like object, no conversion needed
                                pass
                                
                            tasks.append(ResearchTask.from_dict(data))
                        except Exception as e:
                            logger.error(f"Error processing task row: {str(e)}")
                    
                    return tasks
            except Exception as e:
                logger.error(f"Error in list_tasks: {str(e)}")
                return []
        
        return self._execute_with_retry("list_tasks", _list)
    
    # Result methods
    def create_result(self, result: ResearchResult) -> ResearchResult:
        """
        Create a new result.
        
        Args:
            result: The result to create.
            
        Returns:
            The created result.
        """
        import psycopg2.extras
        
        def _create(conn):
            result.updated_at = time.time()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO results (id, task_id, content, format, status, created_at, 
                                       updated_at, created_by, tags, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        result.id,
                        result.task_id,
                        result.content,
                        result.format,
                        result.status,
                        result.created_at,
                        result.updated_at,
                        result.created_by,
                        json.dumps(result.tags),
                        json.dumps(result.metadata)
                    )
                )
            return result
        
        result = self._execute_with_retry("create_result", _create)
        logger.info(f"Created result: {result.id} for task: {result.task_id}")
        return result
    
    def get_result(self, result_id: str) -> Optional[ResearchResult]:
        """
        Get a result by ID.
        
        Args:
            result_id: The ID of the result.
            
        Returns:
            The result with the specified ID, or None if not found.
        """
        import psycopg2.extras
        
        def _get(conn):
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, task_id, content, format, status, created_at, updated_at, 
                           created_by, tags, metadata
                    FROM results
                    WHERE id = %s
                    """,
                    (result_id,)
                )
                row = cursor.fetchone()
                
                if row is None:
                    return None
                
                # Convert JSONB to Python data types
                data = dict(row)
                
                # Handle tags field
                if data['tags'] is None:
                    data['tags'] = []
                elif isinstance(data['tags'], str):
                    data['tags'] = json.loads(data['tags'])
                # For PostgreSQL's json/jsonb type
                elif hasattr(data['tags'], '__iter__') and not isinstance(data['tags'], (str, bytes)):
                    # Already a proper iterable object, no conversion needed
                    pass
                
                # Handle metadata field    
                if data['metadata'] is None:
                    data['metadata'] = {}
                elif isinstance(data['metadata'], str):
                    data['metadata'] = json.loads(data['metadata'])
                # For PostgreSQL's json/jsonb type
                elif hasattr(data['metadata'], 'keys') and callable(data['metadata'].keys):
                    # Already a dict-like object, no conversion needed
                    pass
                
                return ResearchResult.from_dict(data)
        
        return self._execute_with_retry("get_result", _get)
    
    def update_result(self, result: ResearchResult) -> ResearchResult:
        """
        Update a result.
        
        Args:
            result: The result to update.
            
        Returns:
            The updated result.
            
        Raises:
            ValueError: If the result does not exist.
        """
        import psycopg2.extras
        
        def _update(conn):
            result.updated_at = time.time()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE results
                    SET content = %s, format = %s, status = %s, updated_at = %s, 
                        created_by = %s, tags = %s, metadata = %s
                    WHERE id = %s
                    """,
                    (
                        result.content,
                        result.format,
                        result.status,
                        result.updated_at,
                        result.created_by,
                        json.dumps(result.tags),
                        json.dumps(result.metadata),
                        result.id
                    )
                )
                
                if cursor.rowcount == 0:
                    raise ValueError(f"Result not found: {result.id}")
            
            return result
        
        result = self._execute_with_retry("update_result", _update)
        logger.info(f"Updated result: {result.id}")
        return result
    
    def delete_result(self, result_id: str) -> bool:
        """
        Delete a result.
        
        Args:
            result_id: The ID of the result to delete.
            
        Returns:
            True if the result was deleted, False if it did not exist.
        """
        def _delete(conn):
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM results
                    WHERE id = %s
                    """,
                    (result_id,)
                )
                
                return cursor.rowcount > 0
        
        result = self._execute_with_retry("delete_result", _delete)
        if result:
            logger.info(f"Deleted result: {result_id}")
        return result
    
    def list_results_for_task(self, task_id: str) -> List[ResearchResult]:
        """
        List all results for a specific task.
        
        Args:
            task_id: The ID of the task.
            
        Returns:
            A list of results for the specified task.
        """
        import psycopg2.extras
        
        def _list(conn):
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, task_id, content, format, status, created_at, updated_at, 
                           created_by, tags, metadata
                    FROM results
                    WHERE task_id = %s
                    ORDER BY created_at DESC
                    """,
                    (task_id,)
                )
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    try:
                        data = dict(row)
                        
                        # Handle tags field
                        if data['tags'] is None:
                            data['tags'] = []
                        elif isinstance(data['tags'], str):
                            data['tags'] = json.loads(data['tags'])
                        # For PostgreSQL's json/jsonb type
                        elif hasattr(data['tags'], '__iter__') and not isinstance(data['tags'], (str, bytes)):
                            # Already a proper iterable object, no conversion needed
                            pass
                        
                        # Handle metadata field
                        if data['metadata'] is None:
                            data['metadata'] = {}
                        elif isinstance(data['metadata'], str):
                            data['metadata'] = json.loads(data['metadata'])
                        # For PostgreSQL's json/jsonb type
                        elif hasattr(data['metadata'], 'keys') and callable(data['metadata'].keys):
                            # Already a dict-like object, no conversion needed
                            pass
                        
                        results.append(ResearchResult.from_dict(data))
                    except Exception as e:
                        logger.error(f"Error processing result row for task {task_id}: {str(e)}")
                
                return results
        
        return self._execute_with_retry("list_results_for_task", _list)
    
    def list_results(self, status: Optional[str] = None, created_by: Optional[str] = None,
                    tag: Optional[str] = None) -> List[ResearchResult]:
        """
        List results, optionally filtered by status, creator, or tag.
        
        Args:
            status: Optional status filter.
            created_by: Optional creator filter.
            tag: Optional tag filter.
            
        Returns:
            A list of results matching the filters.
        """
        import psycopg2.extras
        
        def _list(conn):
            try:
                # Check if the results table exists
                try:
                    with conn.cursor() as check_cursor:
                        check_cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_schema = current_schema()
                                AND table_name = 'results'
                            )
                        """)
                        result = check_cursor.fetchone()
                        if result is None or not result[0]:
                            logger.warning("Results table does not exist in the current schema")
                            return []
                except Exception as table_check_error:
                    logger.error(f"Error checking if results table exists: {str(table_check_error)}")
                    # Continue anyway - the query will fail later if the table doesn't exist
                
                try:
                    # Direct approach - get all results and filter them
                    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                        cursor.execute("""
                            SELECT id, task_id, content, format, status, created_at, updated_at, 
                                  created_by, tags, metadata
                            FROM results
                            ORDER BY updated_at DESC
                        """)
                        rows = cursor.fetchall()
                        
                        results = []
                        for row in rows:
                            try:
                                data = dict(row)
                                
                                # Handle tags field
                                if data['tags'] is None:
                                    data['tags'] = []
                                elif isinstance(data['tags'], str):
                                    data['tags'] = json.loads(data['tags'])
                                # For PostgreSQL's json/jsonb type - already a proper object
                                
                                # Handle metadata field
                                if data['metadata'] is None:
                                    data['metadata'] = {}
                                elif isinstance(data['metadata'], str):
                                    data['metadata'] = json.loads(data['metadata'])
                                # For PostgreSQL's json/jsonb type - already a proper object
                                
                                result = ResearchResult.from_dict(data)
                                
                                # Apply filters in Python
                                if status and result.status != status:
                                    continue
                                if created_by and result.created_by != created_by:
                                    continue
                                if tag and tag not in result.tags:
                                    continue
                                    
                                results.append(result)
                            except Exception as row_error:
                                logger.error(f"Error processing result row: {str(row_error)}")
                        
                        return results
                except Exception as query_error:
                    logger.error(f"Error querying results: {str(query_error)}")
                    raise
                    
            except Exception as e:
                logger.error(f"Error in list_results: {str(e)}")
                
                # Fallback: get results through task listing
                try:
                    # FALLBACK: Get all tasks and then get results for each task
                    logger.info("Using fallback method to list results via tasks")
                    task_ids = []
                    
                    # First get all task IDs
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT id FROM tasks")
                        task_ids = [row[0] for row in cursor.fetchall()]
                    
                    if not task_ids:
                        logger.warning("No tasks found")
                        return []
                    
                    # Now get results for each task
                    all_results = []
                    for task_id in task_ids:
                        try:
                            # This already implements robust JSON handling
                            task_results = self.list_results_for_task(task_id)
                            
                            # Apply filters
                            filtered_results = task_results
                            if status:
                                filtered_results = [r for r in filtered_results if r.status == status]
                            if created_by:
                                filtered_results = [r for r in filtered_results if r.created_by == created_by]
                            if tag:
                                filtered_results = [r for r in filtered_results if tag in r.tags]
                            
                            all_results.extend(filtered_results)
                        except Exception as task_error:
                            logger.error(f"Error getting results for task {task_id}: {str(task_error)}")
                            continue
                    
                    return all_results
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback method failed: {str(fallback_error)}")
                    # Last resort - return an empty list
                    return []
        
        results = self._execute_with_retry("list_results", _list)
        logger.info(f"Retrieved {len(results)} results from list_results")
        return results


class Database:
    """
    Database implementation for the research system that automatically selects 
    the appropriate backend (TinyDB or PostgreSQL) based on environment configuration.
    """
    
    def __init__(self, db_path: str = "./data/research.json", connection_string: Optional[str] = None):
        """
        Initialize the database with the appropriate backend.
        
        Args:
            db_path: The path to the TinyDB database file (used in development).
            connection_string: The PostgreSQL connection string (used in production).
                              If not provided, it will check the DATABASE_URL environment variable.
        """
        # Determine which database backend to use
        use_postgres = os.getenv("USE_POSTGRES", "false").lower() in ("true", "1", "yes")
        db_url = connection_string or os.getenv("DATABASE_URL", "")
        
        if use_postgres or db_url:
            try:
                # Try to import psycopg2 to see if it's available
                import psycopg2
                self.db = PostgreSQLDatabase(connection_string)
                logger.info("Using PostgreSQL database backend")
            except ImportError:
                logger.warning("psycopg2 not available, falling back to TinyDB")
                self.db = TinyDBDatabase(db_path)
        else:
            logger.info("Using TinyDB database backend")
            self.db = TinyDBDatabase(db_path)
    
    # Delegate all method calls to the selected backend
    def __getattr__(self, name):
        return getattr(self.db, name)


# Helper function to generate a unique ID
def generate_id() -> str:
    """Generate a unique ID for database records."""
    return str(uuid.uuid4())


# Create a default database instance
default_db = Database()