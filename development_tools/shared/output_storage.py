# TOOL_TIER: core

"""
Standardized output storage utility for development tools.

Provides consistent storage patterns for tool results and cache files,
with automatic archiving and rotation support.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

from core.logger import get_component_logger
from .file_rotation import create_output_file, FileRotator

logger = get_component_logger("development_tools")


def _get_domain_from_tool_name(tool_name: str, project_root: Path) -> str:
    """
    Determine the domain directory for a tool based on its name and SCRIPT_REGISTRY.
    
    Args:
        tool_name: Name of the tool (e.g., 'analyze_functions')
        project_root: Project root directory
        
    Returns:
        Domain directory name (e.g., 'functions', 'docs', 'error_handling')
    """
    # Import SCRIPT_REGISTRY to map tool names to paths
    try:
        from ..shared.operations import SCRIPT_REGISTRY
        script_path = SCRIPT_REGISTRY.get(tool_name)
        if script_path:
            # Extract domain from path like 'functions/analyze_functions.py'
            domain = script_path.split('/')[0]
            return domain
    except (ImportError, AttributeError):
        pass
    
    # Fallback: try to infer from tool name patterns
    if 'function' in tool_name:
        return 'functions'
    elif 'documentation' in tool_name or 'doc' in tool_name:
        return 'docs'
    elif 'error' in tool_name or 'handling' in tool_name:
        return 'error_handling'
    elif 'test' in tool_name or 'coverage' in tool_name:
        return 'tests'
    elif 'import' in tool_name or 'module' in tool_name or 'dependency' in tool_name:
        return 'imports'
    elif 'legacy' in tool_name:
        return 'legacy'
    elif 'config' in tool_name:
        return 'config'
    elif 'ai_work' in tool_name or 'ai' in tool_name:
        return 'ai_work'
    elif 'status' in tool_name or 'signal' in tool_name or 'decision' in tool_name:
        return 'reports'
    else:
        # Default to 'reports' for unknown tools
        return 'reports'


def _get_project_root() -> Path:
    """Get project root directory."""
    # Try to get from config
    try:
        from .. import config
        return Path(config.get_project_root())
    except (ImportError, AttributeError):
        # Fallback: assume we're in development_tools/shared/
        return Path(__file__).parent.parent.parent


def save_tool_result(tool_name: str, domain: Optional[str] = None, data: Dict[str, Any] = None, 
                     archive_count: int = 5, project_root: Optional[Path] = None) -> Path:
    """
    Save tool result to domain-specific JSON file with automatic archiving.
    
    Args:
        tool_name: Name of the tool (e.g., 'analyze_functions')
        domain: Domain directory (e.g., 'functions'). If None, inferred from tool_name
        data: Data to save (dict)
        archive_count: Number of archive versions to keep (default: 5)
        project_root: Project root directory. If None, auto-detected
        
    Returns:
        Path to the saved file
    """
    if project_root is None:
        project_root = _get_project_root()
    else:
        project_root = Path(project_root).resolve()
    
    if domain is None:
        domain = _get_domain_from_tool_name(tool_name, project_root)
    
    # Build file path: development_tools/{domain}/jsons/{tool}_results.json
    dev_tools_dir = project_root / "development_tools"
    jsons_dir = dev_tools_dir / domain / "jsons"
    jsons_dir.mkdir(parents=True, exist_ok=True)
    
    result_file = jsons_dir / f"{tool_name}_results.json"
    
    # Prepare data with metadata
    timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    timestamp_iso = datetime.now().isoformat()
    
    result_data = {
        'generated_by': f'{tool_name} - Development Tools',
        'last_generated': timestamp_str,
        'timestamp': timestamp_iso,
        'tool_name': tool_name,
        'domain': domain,
        'source': f'python development_tools/{domain}/{tool_name}.py',
        'note': 'This file is auto-generated. Do not edit manually.',
        'data': data or {}
    }
    
    # Use create_output_file for rotation, but we need custom archiving for jsons/archive/
    # First, handle rotation if file exists
    if result_file.exists():
        archive_dir = jsons_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped archive
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        archive_name = f"{tool_name}_results_{timestamp}.json"
        archive_path = archive_dir / archive_name
        
        # Move existing file to archive
        import shutil
        shutil.move(str(result_file), str(archive_path))
        
        # Clean up old archives (keep last archive_count)
        rotator = FileRotator(base_dir=str(jsons_dir))
        rotator._cleanup_old_versions(f"{tool_name}_results", archive_count)
    
    # Write new file
    result_file.parent.mkdir(parents=True, exist_ok=True)
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2)
    
    logger.debug(f"Saved tool result: {result_file}")
    return result_file


def load_tool_result(tool_name: str, domain: Optional[str] = None, 
                     project_root: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Load tool result from domain-specific JSON file.
    
    Args:
        tool_name: Name of the tool (e.g., 'analyze_functions')
        domain: Domain directory (e.g., 'functions'). If None, inferred from tool_name
        project_root: Project root directory. If None, auto-detected
        
    Returns:
        Data dict if file exists, None otherwise
    """
    if project_root is None:
        project_root = _get_project_root()
    else:
        project_root = Path(project_root).resolve()
    
    if domain is None:
        domain = _get_domain_from_tool_name(tool_name, project_root)
    
    # Build file path
    dev_tools_dir = project_root / "development_tools"
    result_file = dev_tools_dir / domain / "jsons" / f"{tool_name}_results.json"
    
    if not result_file.exists():
        return None
    
    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        return result_data.get('data', result_data)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load tool result from {result_file}: {e}")
        return None


def save_tool_cache(tool_name: str, domain: Optional[str] = None, data: Dict[str, Any] = None,
                    project_root: Optional[Path] = None) -> Path:
    """
    Save tool cache file to domain-specific jsons/ directory.
    
    Args:
        tool_name: Name of the tool (e.g., 'analyze_functions')
        domain: Domain directory (e.g., 'functions'). If None, inferred from tool_name
        data: Data to save (dict)
        project_root: Project root directory. If None, auto-detected
        
    Returns:
        Path to the saved cache file
    """
    if project_root is None:
        project_root = _get_project_root()
    else:
        project_root = Path(project_root).resolve()
    
    if domain is None:
        domain = _get_domain_from_tool_name(tool_name, project_root)
    
    # Build file path: development_tools/{domain}/jsons/.{tool}_cache.json
    dev_tools_dir = project_root / "development_tools"
    jsons_dir = dev_tools_dir / domain / "jsons"
    jsons_dir.mkdir(parents=True, exist_ok=True)
    
    cache_file = jsons_dir / f".{tool_name}_cache.json"
    
    # Prepare cache data with metadata
    timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    timestamp_iso = datetime.now().isoformat()
    
    cache_data = {
        'generated_by': f'{tool_name} - Development Tools',
        'last_generated': timestamp_str,
        'timestamp': timestamp_iso,
        'tool_name': tool_name,
        'domain': domain,
        'note': 'This file is auto-generated. Do not edit manually.',
        'data': data or {}
    }
    
    # Write cache file (no rotation for cache files)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2)
    
    logger.debug(f"Saved tool cache: {cache_file}")
    return cache_file


def load_tool_cache(tool_name: str, domain: Optional[str] = None,
                    project_root: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Load tool cache file from domain-specific jsons/ directory.
    
    Args:
        tool_name: Name of the tool (e.g., 'analyze_functions')
        domain: Domain directory (e.g., 'functions'). If None, inferred from tool_name
        project_root: Project root directory. If None, auto-detected
        
    Returns:
        Data dict if file exists, None otherwise
    """
    if project_root is None:
        project_root = _get_project_root()
    else:
        project_root = Path(project_root).resolve()
    
    if domain is None:
        domain = _get_domain_from_tool_name(tool_name, project_root)
    
    # Build file path
    dev_tools_dir = project_root / "development_tools"
    cache_file = dev_tools_dir / domain / "jsons" / f".{tool_name}_cache.json"
    
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        return cache_data.get('data', cache_data)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load tool cache from {cache_file}: {e}")
        return None


def get_all_tool_results(project_root: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate all tool results from all domain jsons/ directories.
    
    Args:
        project_root: Project root directory. If None, auto-detected
        
    Returns:
        Dict mapping tool_name -> result_data
    """
    if project_root is None:
        project_root = _get_project_root()
    else:
        project_root = Path(project_root).resolve()
    
    dev_tools_dir = project_root / "development_tools"
    all_results = {}
    
    # Known domain directories
    domains = ['functions', 'docs', 'error_handling', 'tests', 'imports', 'legacy', 
               'config', 'ai_work', 'reports', 'shared']
    
    for domain in domains:
        jsons_dir = dev_tools_dir / domain / "jsons"
        if not jsons_dir.exists():
            continue
        
        # Find all _results.json files
        for result_file in jsons_dir.glob("*_results.json"):
            tool_name = result_file.stem.replace('_results', '')
            
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
                all_results[tool_name] = result_data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load result from {result_file}: {e}")
                continue
    
    return all_results

