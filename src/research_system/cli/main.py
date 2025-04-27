"""
Command Line Interface for the Research System.

This module provides a command-line interface for interacting with the
research system, allowing users to create and manage research tasks,
execute searches, and retrieve results.
"""

import argparse
import logging
import sys
import json
import time
import os
import traceback
from typing import Dict, List, Optional, Any, Union
import yaml
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

# Import research system components
from src.research_system.core.server import Context
from src.research_system.core.coordinator import default_coordinator
from src.research_system.agents.planner import PlannerAgent, default_planner
from src.research_system.agents.search import SearchAgent, default_search
from src.research_system.models.db import Database, ResearchTask, ResearchResult, default_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/research_cli.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Rich console for better output
console = Console()

# Load configuration
def load_config():
    """Load configuration from config.yaml file."""
    try:
        config_path = os.getenv("CONFIG_PATH", "config.yaml")
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        # Return default configuration
        return {
            "app": {"port": 8080, "max_workers": 4},
            "logging": {"level": "INFO"},
            "environment": "development"
        }

config = load_config()

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

def parse_args():
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(description="Research System CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Execute a search query")
    search_parser.add_argument("--query", "-q", required=True, help="Search query")
    search_parser.add_argument("--task-id", "-t", help="Associated task ID")
    search_parser.add_argument("--max-results", "-m", type=int, default=5, help="Maximum number of results")
    search_parser.add_argument("--output", "-o", choices=["text", "json"], default="text", help="Output format")
    
    # Task commands
    task_parser = subparsers.add_parser("task", help="Manage research tasks")
    task_subparsers = task_parser.add_subparsers(dest="subcommand", help="Task subcommand")
    
    # Task create
    task_create = task_subparsers.add_parser("create", help="Create a new research task")
    task_create.add_argument("--title", required=True, help="Task title")
    task_create.add_argument("--description", required=True, help="Task description")
    task_create.add_argument("--tags", nargs="+", help="Task tags")
    
    # Task list
    task_list = task_subparsers.add_parser("list", help="List research tasks")
    task_list.add_argument("--status", choices=["pending", "in_progress", "completed", "failed"], help="Filter by status")
    task_list.add_argument("--tag", help="Filter by tag")
    task_list.add_argument("--assigned-to", help="Filter by assignment")
    
    # Task get
    task_get = task_subparsers.add_parser("get", help="Get a research task by ID")
    task_get.add_argument("--id", required=True, help="Task ID")
    
    # Task update
    task_update = task_subparsers.add_parser("update", help="Update a research task")
    task_update.add_argument("--id", required=True, help="Task ID")
    task_update.add_argument("--status", choices=["pending", "in_progress", "completed", "failed"], help="New status")
    task_update.add_argument("--title", help="New title")
    task_update.add_argument("--description", help="New description")
    
    # Result commands
    result_parser = subparsers.add_parser("result", help="Manage research results")
    result_subparsers = result_parser.add_subparsers(dest="subcommand", help="Result subcommand")
    
    # Result list
    result_list = result_subparsers.add_parser("list", help="List research results")
    result_list.add_argument("--task-id", help="Filter by task ID")
    result_list.add_argument("--status", choices=["draft", "reviewed", "final"], help="Filter by status")
    result_list.add_argument("--tag", help="Filter by tag")
    
    # Result get
    result_get = result_subparsers.add_parser("get", help="Get a research result by ID")
    result_get.add_argument("--id", required=True, help="Result ID")
    
    # Plan commands
    plan_parser = subparsers.add_parser("plan", help="Manage research plans")
    plan_subparsers = plan_parser.add_subparsers(dest="subcommand", help="Plan subcommand")
    
    # Plan create
    plan_create = plan_subparsers.add_parser("create", help="Create a research plan for a task")
    plan_create.add_argument("--task-id", required=True, help="Task ID")
    
    # Plan get
    plan_get = plan_subparsers.add_parser("get", help="Get a research plan by ID")
    plan_get.add_argument("--id", required=True, help="Plan ID")
    
    return parser.parse_args()

def validate_args(args):
    """
    Validate command-line arguments.
    
    Args:
        args: Parsed arguments namespace.
        
    Raises:
        ValueError: If arguments are invalid.
    """
    if args.command == "search":
        if not args.query.strip():
            raise ValueError("Query cannot be empty")
    
    elif args.command == "task":
        if args.subcommand == "create":
            if not args.title.strip():
                raise ValueError("Title cannot be empty")
            if not args.description.strip():
                raise ValueError("Description cannot be empty")
    
    elif args.command == "result" or args.command == "plan":
        if args.subcommand == "get":
            if not args.id.strip():
                raise ValueError("ID cannot be empty")

def execute_search_command(args, search_agent=None, db=None):
    """
    Execute a search command.
    
    Args:
        args: Parsed arguments namespace.
        search_agent: Optional search agent instance.
        db: Optional database instance.
    """
    # Use default instances if not provided
    search_agent = search_agent or default_search
    db = db or default_db
    
    # Create a context for tracking progress
    context = Context()
    
    try:
        # If task ID is not provided, create a temporary task
        task_id = args.task_id
        if not task_id:
            task = ResearchTask(
                id=f"temp_{int(time.time())}",
                title=f"Search: {args.query}",
                description=f"Temporary task for search query: {args.query}"
            )
            db.create_task(task)
            task_id = task.id
            console.print(f"[green]Created temporary task: {task_id}[/green]")
        
        console.print(f"[bold blue]Executing search:[/bold blue] '{args.query}'")
        
        # Show progress bar for search execution
        with Progress() as progress:
            search_task = progress.add_task("[cyan]Searching...", total=100)
            
            # Create a custom context that updates our progress bar
            class ProgressContext(Context):
                def update_progress(self, progress_value, status=None):
                    super().update_progress(progress_value, status)
                    progress.update(search_task, completed=int(progress_value * 100))
            
            # Use our custom context
            custom_context = ProgressContext(task_id=task_id)
            
            # Execute the search
            results = search_agent.execute_search(
                task_id=task_id,
                query=args.query,
                max_results=args.max_results,
                context=custom_context
            )
            
            # Complete the progress
            progress.update(search_task, completed=100)
        
        # Display results
        console.print(f"\n[bold green]Search Results ([/bold green][bold yellow]{len(results)}[/bold yellow][bold green] found):[/bold green]\n")
        
        if args.output == "json":
            console.print_json(json.dumps(results))
        else:
            # Create a table for the results
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("#", style="dim")
            table.add_column("Title", style="cyan")
            table.add_column("URL", style="blue")
            table.add_column("Description", style="green")
            
            for i, result in enumerate(results, 1):
                table.add_row(
                    str(i),
                    result['title'],
                    result['url'],
                    result['snippet'][:100] + ("..." if len(result['snippet']) > 100 else "")
                )
            
            console.print(table)
        
        # Store results in database
        search_agent.store_search_results(task_id, results)
        console.print(f"[green]Results stored in task:[/green] {task_id}")
        console.print(f"[dim]View task details with:[/dim] task get --id {task_id}")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        logger.error(f"Search command error: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)

def execute_task_command(args, planner_agent=None, db=None):
    """
    Execute a task command.
    
    Args:
        args: Parsed arguments namespace.
        planner_agent: Optional planner agent instance.
        db: Optional database instance.
    """
    # Use default instances if not provided
    planner_agent = planner_agent or default_planner
    db = db or default_db
    
    try:
        if args.subcommand == "create":
            # Create a task
            tags = args.tags or []
            
            with Progress() as progress:
                create_task = progress.add_task("[cyan]Creating task...", total=100)
                progress.update(create_task, advance=50)
                
                task = planner_agent.create_research_task(
                    title=args.title,
                    description=args.description,
                    tags=tags
                )
                
                progress.update(create_task, completed=100)
            
            console.print("[bold green]Task created successfully:[/bold green]")
            console.print(f"[bold]ID:[/bold] {task['id']}")
            console.print(f"[bold]Title:[/bold] {task['title']}")
            console.print(f"[bold]Description:[/bold] {task['description']}")
            if tags:
                console.print(f"[bold]Tags:[/bold] {', '.join(tags)}")
        
        elif args.subcommand == "list":
            # List tasks
            with Progress() as progress:
                list_task = progress.add_task("[cyan]Fetching tasks...", total=100)
                
                tasks = planner_agent.list_research_tasks(
                    status=args.status,
                    assigned_to=args.assigned_to,
                    tag=args.tag
                )
                
                progress.update(list_task, completed=100)
            
            # Apply filters description for the user
            filters = []
            if args.status:
                filters.append(f"status={args.status}")
            if args.assigned_to:
                filters.append(f"assigned to {args.assigned_to}")
            if args.tag:
                filters.append(f"tag={args.tag}")
                
            filter_text = f" ({', '.join(filters)})" if filters else ""
                
            console.print(f"[bold green]Tasks{filter_text}[/bold green] [yellow]({len(tasks)})[/yellow]:\n")
            
            if not tasks:
                console.print("[dim]No tasks found.[/dim]")
                return
                
            # Create a table for the tasks
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("#", style="dim")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="blue")
            table.add_column("Status", style="green")
            table.add_column("Tags", style="yellow")
            
            for i, task in enumerate(tasks, 1):
                status_color = {
                    "pending": "yellow",
                    "in_progress": "blue", 
                    "completed": "green",
                    "failed": "red"
                }.get(task['status'], "white")
                
                table.add_row(
                    str(i),
                    task['id'],
                    task['title'],
                    f"[{status_color}]{task['status']}[/{status_color}]",
                    ", ".join(task['tags']) if task['tags'] else ""
                )
            
            console.print(table)
        
        elif args.subcommand == "get":
            # Get a task
            with Progress() as progress:
                get_task = progress.add_task("[cyan]Fetching task...", total=100)
                task = db.get_task(args.id)
                progress.update(get_task, completed=100)
                
            if task is None:
                console.print(f"[bold red]Task not found:[/bold red] {args.id}")
                sys.exit(1)
            
            console.print(f"[bold green]Task Details:[/bold green] {task.id}\n")
            
            # Create a detail panel for the task
            details = Table.grid(padding=1)
            details.add_column(style="bold")
            details.add_column()
            
            details.add_row("Title", task.title)
            details.add_row("Description", task.description)
            
            status_color = {
                "pending": "yellow",
                "in_progress": "blue", 
                "completed": "green",
                "failed": "red"
            }.get(task.status, "white")
            details.add_row("Status", f"[{status_color}]{task.status}[/{status_color}]")
            
            if task.tags:
                details.add_row("Tags", ", ".join(task.tags))
                
            if task.assigned_to:
                details.add_row("Assigned To", task.assigned_to)
                
            details.add_row("Created", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task.created_at)))
            details.add_row("Updated", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task.updated_at)))
            
            console.print(details)
            
            # Check if task has a plan
            if task.metadata.get("has_plan"):
                plan_id = task.metadata.get('plan_id')
                console.print(f"\n[bold blue]This task has a research plan:[/bold blue] {plan_id}")
                console.print(f"[dim]View plan with:[/dim] plan get --id {plan_id}")
            else:
                console.print("\n[dim]This task doesn't have a research plan yet.[/dim]")
                console.print(f"[dim]Create a plan with:[/dim] plan create --task-id {task.id}")
        
        elif args.subcommand == "update":
            # Get the task
            with Progress() as progress:
                update_task = progress.add_task("[cyan]Updating task...", total=100)
                progress.update(update_task, advance=30)
                
                task = db.get_task(args.id)
                if task is None:
                    progress.update(update_task, completed=100)
                    console.print(f"[bold red]Task not found:[/bold red] {args.id}")
                    sys.exit(1)
                
                progress.update(update_task, advance=30)
                
                # Track what was updated
                updated_fields = []
                
                # Update fields
                if args.status:
                    task.status = args.status
                    updated_fields.append("status")
                    
                if args.title:
                    task.title = args.title
                    updated_fields.append("title")
                    
                if args.description:
                    task.description = args.description
                    updated_fields.append("description")
                
                # Save the task
                db.update_task(task)
                progress.update(update_task, completed=100)
            
            console.print(f"[bold green]Task updated successfully:[/bold green] {task.id}")
            console.print(f"[dim]Updated fields:[/dim] {', '.join(updated_fields)}")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        logger.error(f"Task command error: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)

def execute_result_command(args, db=None):
    """
    Execute a result command.
    
    Args:
        args: Parsed arguments namespace.
        db: Optional database instance.
    """
    # Use default instance if not provided
    db = db or default_db
    
    try:
        if args.subcommand == "list":
            # List results
            with Progress() as progress:
                list_task = progress.add_task("[cyan]Fetching results...", total=100)
                
                if args.task_id:
                    results = db.list_results_for_task(args.task_id)
                else:
                    results = db.list_results(status=args.status, tag=args.tag)
                    
                progress.update(list_task, completed=100)
            
            # Apply filters description for the user
            filters = []
            if args.task_id:
                filters.append(f"task_id={args.task_id}")
            if args.status:
                filters.append(f"status={args.status}")
            if args.tag:
                filters.append(f"tag={args.tag}")
                
            filter_text = f" ({', '.join(filters)})" if filters else ""
                
            console.print(f"[bold green]Results{filter_text}[/bold green] [yellow]({len(results)})[/yellow]:\n")
            
            if not results:
                console.print("[dim]No results found.[/dim]")
                return
                
            # Create a table for the results
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("#", style="dim")
            table.add_column("ID", style="cyan")
            table.add_column("Task ID", style="blue")
            table.add_column("Format", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Created", style="dim")
            table.add_column("Tags", style="magenta")
            
            for i, result in enumerate(results, 1):
                status_color = {
                    "draft": "yellow",
                    "reviewed": "blue", 
                    "final": "green"
                }.get(result.status, "white")
                
                table.add_row(
                    str(i),
                    result.id,
                    result.task_id,
                    result.format,
                    f"[{status_color}]{result.status}[/{status_color}]",
                    time.strftime('%Y-%m-%d %H:%M', time.localtime(result.created_at)),
                    ", ".join(result.tags) if result.tags else ""
                )
            
            console.print(table)
            console.print(f"[dim]View result details with:[/dim] result get --id <result_id>")
        
        elif args.subcommand == "get":
            # Get a result
            with Progress() as progress:
                get_task = progress.add_task("[cyan]Fetching result...", total=100)
                result = db.get_result(args.id)
                progress.update(get_task, completed=100)
                
            if result is None:
                console.print(f"[bold red]Result not found:[/bold red] {args.id}")
                sys.exit(1)
            
            console.print(f"[bold green]Result Details:[/bold green] {result.id}\n")
            
            # Create a detail panel for the result
            details = Table.grid(padding=1)
            details.add_column(style="bold")
            details.add_column()
            
            details.add_row("Task ID", result.task_id)
            details.add_row("Format", result.format)
            
            status_color = {
                "draft": "yellow",
                "reviewed": "blue", 
                "final": "green"
            }.get(result.status, "white")
            details.add_row("Status", f"[{status_color}]{result.status}[/{status_color}]")
            
            details.add_row("Created", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(result.created_at)))
            details.add_row("Updated", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(result.updated_at)))
            
            if result.created_by:
                details.add_row("Created By", result.created_by)
                
            if result.tags:
                details.add_row("Tags", ", ".join(result.tags))
            
            console.print(details)
            
            # Display the content
            console.print("\n[bold]Content:[/bold]")
            if result.format == "json":
                # Pretty print JSON content
                try:
                    content_obj = json.loads(result.content)
                    console.print_json(json.dumps(content_obj))
                except json.JSONDecodeError:
                    console.print(f"[italic red]Warning:[/italic red] Content is marked as JSON but failed to parse.")
                    console.print(result.content)
            else:
                console.print(result.content)
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        logger.error(f"Result command error: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)

def execute_plan_command(args, planner_agent=None):
    """
    Execute a plan command.
    
    Args:
        args: Parsed arguments namespace.
        planner_agent: Optional planner agent instance.
    """
    # Use default instance if not provided
    planner_agent = planner_agent or default_planner
    
    try:
        if args.subcommand == "create":
            # Create a plan
            with Progress() as progress:
                create_task = progress.add_task("[cyan]Generating research plan...", total=100)
                
                # Create a custom context that updates our progress bar
                class ProgressContext(Context):
                    def update_progress(self, progress_value, status=None):
                        super().update_progress(progress_value, status)
                        progress.update(create_task, completed=int(progress_value * 100))
                
                # Use our custom context
                context = ProgressContext()
                
                # Generate the plan
                plan = planner_agent.generate_plan_for_task(args.task_id, context=context)
                
                # Ensure progress is complete
                progress.update(create_task, completed=100)
            
            console.print("[bold green]Plan created successfully:[/bold green]")
            console.print(f"[bold]ID:[/bold] {plan['id']}")
            console.print(f"[bold]Task ID:[/bold] {plan['task_id']}")
            console.print(f"[bold]Status:[/bold] {plan['status']}")
            
            console.print("\n[bold cyan]Research Steps:[/bold cyan]")
            
            # Create a table for the steps
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="dim")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="blue")
            table.add_column("Status", style="green")
            table.add_column("Dependencies", style="yellow")
            
            for step in plan["steps"]:
                status_color = {
                    "pending": "yellow",
                    "in_progress": "blue", 
                    "completed": "green",
                    "failed": "red"
                }.get(step['status'], "white")
                
                dependencies = ", ".join(str(dep) for dep in step.get('depends_on', [])) if 'depends_on' in step else ""
                
                table.add_row(
                    str(step['id']),
                    step['name'],
                    step['type'],
                    f"[{status_color}]{step['status']}[/{status_color}]",
                    dependencies
                )
            
            console.print(table)
            console.print(f"\n[dim]You can view this plan later with:[/dim] plan get --id {plan['id']}")
        
        elif args.subcommand == "get":
            # Get a plan
            with Progress() as progress:
                get_task = progress.add_task("[cyan]Fetching research plan...", total=100)
                plan = planner_agent.get_research_plan(args.id)
                progress.update(get_task, completed=100)
            
            console.print(f"[bold green]Research Plan:[/bold green] {plan['id']}\n")
            
            # Create a detail panel for the plan
            details = Table.grid(padding=1)
            details.add_column(style="bold")
            details.add_column()
            
            details.add_row("Task ID", plan['task_id'])
            
            status_color = {
                "draft": "yellow",
                "approved": "blue", 
                "in_progress": "cyan",
                "completed": "green"
            }.get(plan['status'], "white")
            details.add_row("Status", f"[{status_color}]{plan['status']}[/{status_color}]")
            
            details.add_row("Created", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(plan['created_at'])))
            details.add_row("Updated", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(plan['updated_at'])))
            
            console.print(details)
            
            console.print("\n[bold cyan]Research Steps:[/bold cyan]")
            
            # Create a table for the steps
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="dim")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="blue")
            table.add_column("Status", style="green")
            table.add_column("Dependencies", style="yellow")
            
            for step in plan["steps"]:
                status_color = {
                    "pending": "yellow",
                    "in_progress": "blue", 
                    "completed": "green",
                    "failed": "red"
                }.get(step['status'], "white")
                
                dependencies = ", ".join(str(dep) for dep in step.get('depends_on', [])) if 'depends_on' in step else ""
                
                table.add_row(
                    str(step['id']),
                    step['name'],
                    step['type'],
                    f"[{status_color}]{step['status']}[/{status_color}]",
                    dependencies
                )
            
            console.print(table)
            
            # Print step details
            console.print("\n[bold]Step Details:[/bold]")
            for step in plan["steps"]:
                console.print(f"[bold cyan]{step['id']}. {step['name']}[/bold cyan]")
                console.print(f"   [dim]Description:[/dim] {step['description']}")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        logger.error(f"Plan command error: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)

def main():
    """Main entry point for the CLI."""
    try:
        # Show welcome header
        console.print("\n[bold blue]=====================================[/bold blue]")
        console.print("[bold blue]  Research System Command Line Tool  [/bold blue]")
        console.print("[bold blue]=====================================[/bold blue]\n")
        
        args = parse_args()
        
        # Handle empty command
        if not args.command:
            console.print("[yellow]No command specified. Use --help for usage information.[/yellow]")
            console.print("Available commands: search, task, result, plan")
            sys.exit(1)
        
        # Validate arguments
        try:
            validate_args(args)
        except ValueError as e:
            console.print(f"[bold red]Error in arguments:[/bold red] {e}")
            sys.exit(1)
        
        # Execute the appropriate command
        if args.command == "search":
            execute_search_command(args)
        
        elif args.command == "task":
            execute_task_command(args)
        
        elif args.command == "result":
            execute_result_command(args)
        
        elif args.command == "plan":
            execute_plan_command(args)
    
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(0)
    
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        logger.error(f"Unexpected error: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
