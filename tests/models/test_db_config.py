"""
Tests for the database configuration module.

This module contains tests for all the functionality in the db_config.py module,
including config loading, environment variable handling, and connection string building.
"""

import os
import pytest
import tempfile
import yaml
from unittest.mock import patch, mock_open

from src.research_system.models.db_config import (
    load_config,
    get_env_config,
    build_connection_string,
    deep_merge,
    get_database_config,
    DEFAULT_CONFIG
)


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    test_config = {
        "database": {
            "use_postgres": True,
            "tinydb_path": "./test/db.json",
            "postgres": {
                "host": "test-host",
                "port": 5433,
                "dbname": "test-db",
                "user": "test-user",
                "password": "test-password"
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_config, f)
        config_path = f.name
    
    yield config_path
    
    # Cleanup
    if os.path.exists(config_path):
        os.unlink(config_path)


@pytest.fixture
def reset_env():
    """Save and restore environment variables for tests."""
    # Save original environment variables
    original_env = {}
    db_vars = [
        "DB_USE_POSTGRES", "USE_POSTGRES", "DB_TINYDB_PATH", "DATABASE_URL",
        "DB_POSTGRES_HOST", "POSTGRES_SERVICE_HOST", 
        "DB_POSTGRES_PORT", "POSTGRES_SERVICE_PORT",
        "DB_POSTGRES_DBNAME", "POSTGRES_DB",
        "DB_POSTGRES_USER", "POSTGRES_USER",
        "DB_POSTGRES_PASSWORD", "POSTGRES_PASSWORD"
    ]
    
    for var in db_vars:
        if var in os.environ:
            original_env[var] = os.environ[var]
            del os.environ[var]
    
    yield
    
    # Restore original environment
    for var in db_vars:
        if var in os.environ:
            del os.environ[var]
    
    for var, value in original_env.items():
        os.environ[var] = value


class TestDbConfig:
    """Tests for the db_config module."""
    
    def test_load_config_defaults(self, reset_env):
        """Test loading default configuration."""
        # Make sure environment doesn't interfere
        config = load_config()
        # We only assert specific values since other tests might have set env vars
        assert "database" in config
        assert "use_postgres" in config["database"]
        assert "tinydb_path" in config["database"]
        assert "postgres" in config["database"]
    
    def test_load_config_from_file(self, temp_config_file):
        """Test loading configuration from a file."""
        config = load_config(temp_config_file)
        assert config["database"]["use_postgres"] is True
        assert config["database"]["tinydb_path"] == "./test/db.json"
        assert config["database"]["postgres"]["host"] == "test-host"
        assert config["database"]["postgres"]["port"] == 5433
    
    def test_load_config_file_not_found(self):
        """Test loading configuration when file doesn't exist."""
        config = load_config("/path/does/not/exist.yaml")
        assert config == DEFAULT_CONFIG
    
    def test_load_config_invalid_file(self):
        """Test loading configuration from an invalid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content:")
            invalid_path = f.name
        
        try:
            with patch('builtins.open', mock_open(read_data="invalid: yaml: content:")):
                config = load_config(invalid_path)
                assert config == DEFAULT_CONFIG
        finally:
            if os.path.exists(invalid_path):
                os.unlink(invalid_path)
    
    def test_get_env_config_empty(self, reset_env):
        """Test getting config from environment when no variables are set."""
        config = get_env_config()
        assert config == {"database": {}}
    
    def test_get_env_config_use_postgres(self, reset_env):
        """Test USE_POSTGRES environment variable."""
        # Test different values that should be interpreted as True
        for value in ["true", "True", "TRUE", "1", "yes", "y", "Y"]:
            os.environ["USE_POSTGRES"] = value
            config = get_env_config()
            assert config["database"]["use_postgres"] is True
            del os.environ["USE_POSTGRES"]
        
        # Test values that should be interpreted as False
        for value in ["false", "False", "FALSE", "0", "no", "n", "N"]:
            os.environ["USE_POSTGRES"] = value
            config = get_env_config()
            assert config["database"]["use_postgres"] is False
            del os.environ["USE_POSTGRES"]
    
    def test_get_env_config_db_use_postgres(self, reset_env):
        """Test DB_USE_POSTGRES environment variable."""
        os.environ["DB_USE_POSTGRES"] = "true"
        config = get_env_config()
        assert config["database"]["use_postgres"] is True
    
    def test_get_env_config_tinydb_path(self, reset_env):
        """Test DB_TINYDB_PATH environment variable."""
        os.environ["DB_TINYDB_PATH"] = "/custom/path/db.json"
        config = get_env_config()
        assert config["database"]["tinydb_path"] == "/custom/path/db.json"
    
    def test_get_env_config_database_url(self, reset_env):
        """Test DATABASE_URL environment variable."""
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/db"
        config = get_env_config()
        assert config["database"]["use_postgres"] is True
        assert config["database"]["postgres"]["connection_url"] == "postgresql://user:pass@localhost:5432/db"
    
    def test_get_env_config_postgres_components(self, reset_env):
        """Test individual PostgreSQL component environment variables."""
        os.environ["DB_POSTGRES_HOST"] = "db.example.com"
        os.environ["DB_POSTGRES_PORT"] = "5433"
        os.environ["DB_POSTGRES_DBNAME"] = "research_db"
        os.environ["DB_POSTGRES_USER"] = "db_user"
        os.environ["DB_POSTGRES_PASSWORD"] = "db_password"
        
        config = get_env_config()
        postgres = config["database"]["postgres"]
        assert postgres["host"] == "db.example.com"
        assert postgres["port"] == 5433  # Should be converted to int
        assert postgres["dbname"] == "research_db"
        assert postgres["user"] == "db_user"
        assert postgres["password"] == "db_password"
    
    def test_get_env_config_kubernetes_service(self, reset_env):
        """Test Kubernetes service environment variables."""
        # Kubernetes sets these environment variables for service discovery
        os.environ["POSTGRES_SERVICE_HOST"] = "postgres.svc.cluster.local"
        os.environ["POSTGRES_SERVICE_PORT"] = "5432"
        os.environ["POSTGRES_DB"] = "k8s_db"
        os.environ["POSTGRES_USER"] = "k8s_user"
        os.environ["POSTGRES_PASSWORD"] = "k8s_password"
        
        config = get_env_config()
        postgres = config["database"]["postgres"]
        assert postgres["host"] == "postgres.svc.cluster.local"
        assert postgres["port"] == 5432
        assert postgres["dbname"] == "k8s_db"
        assert postgres["user"] == "k8s_user"
        assert postgres["password"] == "k8s_password"
    
    def test_env_vars_precedence(self, reset_env):
        """Test that DB_ vars take precedence over Kubernetes service vars."""
        os.environ["POSTGRES_SERVICE_HOST"] = "postgres.svc.cluster.local"
        os.environ["DB_POSTGRES_HOST"] = "custom.example.com"
        
        config = get_env_config()
        assert config["database"]["postgres"]["host"] == "custom.example.com"
    
    def test_build_connection_string_default(self):
        """Test building a connection string with default values."""
        config = {"database": {"postgres": {}}}
        conn_str = build_connection_string(config)
        assert conn_str == "postgresql://postgres:postgres@localhost:5432/research"
    
    def test_build_connection_string_custom(self):
        """Test building a connection string with custom values."""
        config = {
            "database": {
                "postgres": {
                    "host": "db.example.com",
                    "port": 5433,
                    "dbname": "custom_db",
                    "user": "custom_user",
                    "password": "custom_password"
                }
            }
        }
        conn_str = build_connection_string(config)
        assert conn_str == "postgresql://custom_user:custom_password@db.example.com:5433/custom_db"
    
    def test_build_connection_string_from_url(self):
        """Test using a preconfigured connection URL."""
        config = {
            "database": {
                "postgres": {
                    "connection_url": "postgresql://user:pass@host:5432/db"
                }
            }
        }
        conn_str = build_connection_string(config)
        assert conn_str == "postgresql://user:pass@host:5432/db"
    
    def test_deep_merge_simple(self):
        """Test deep merging of simple dictionaries."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        deep_merge(base, override)
        assert base == {"a": 1, "b": 3, "c": 4}
    
    def test_deep_merge_nested(self):
        """Test deep merging of nested dictionaries."""
        base = {"a": 1, "b": {"x": 1, "y": 2}}
        override = {"b": {"y": 3, "z": 4}, "c": 5}
        deep_merge(base, override)
        assert base == {"a": 1, "b": {"x": 1, "y": 3, "z": 4}, "c": 5}
    
    def test_deep_merge_override_non_dict(self):
        """Test that non-dict values override dict values."""
        base = {"a": {"x": 1}}
        override = {"a": "value"}
        deep_merge(base, override)
        assert base == {"a": "value"}
    
    def test_get_database_config_default(self):
        """Test getting database config with defaults."""
        config_copy = {
            "database": {
                "use_postgres": False,
                "tinydb_path": "./data/research.json",
                "postgres": DEFAULT_CONFIG["database"]["postgres"].copy()
            }
        }
        with patch('src.research_system.models.db_config.load_config', return_value=config_copy):
            db_config = get_database_config()
            assert db_config["use_postgres"] is False
            assert db_config["tinydb_path"] == "./data/research.json"
            assert "connection_string" not in db_config
    
    def test_get_database_config_postgres(self):
        """Test getting database config with PostgreSQL enabled."""
        test_config = {
            "database": {
                "use_postgres": True,
                "postgres": {
                    "host": "test-host",
                    "dbname": "test-db"
                }
            }
        }
        
        with patch('src.research_system.models.db_config.load_config', return_value=test_config):
            db_config = get_database_config()
            assert db_config["use_postgres"] is True
            assert "connection_string" in db_config
            assert db_config["connection_string"] == "postgresql://postgres:postgres@test-host:5432/test-db"
    
    def test_config_loading_priority(self, temp_config_file, reset_env):
        """Test that config loading respects the priority order."""
        # Set up environment variables (highest priority)
        os.environ["DB_USE_POSTGRES"] = "true"
        os.environ["DB_POSTGRES_HOST"] = "env-host"
        
        # Load config, which should prioritize env vars over file
        config = load_config(temp_config_file)
        
        # Check priorities:
        # - use_postgres: true from env (env wins)
        # - host: env-host from env (env wins)
        # - port: 5433 from file (file wins over default)
        # - dbname: test-db from file (file wins over default)
        assert config["database"]["use_postgres"] is True
        assert config["database"]["postgres"]["host"] == "env-host"
        assert config["database"]["postgres"]["port"] == 5433
        assert config["database"]["postgres"]["dbname"] == "test-db"
        
        # Check that defaults are preserved when not overridden
        assert config["database"]["postgres"]["connect_timeout"] == 5