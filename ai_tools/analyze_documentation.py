#!/usr/bin/env python3
"""
Analyze documentation overlap and redundancy to help consolidate files.
"""

import os
from pathlib import Path
from typing import Dict, List, Set
import re

def get_documentation_files() -> Dict[str, str]:
    """Get all documentation files and their content."""
    import config
    project_root = config.get_project_root()
    docs = {}
    
    # Documentation files to analyze
    doc_files = [
        'ARCHITECTURE.md',
        'CHANGELOG.md', 
        'DEVELOPMENT_WORKFLOW.md',
        'DOCUMENTATION_GUIDE.md',
        'FUNCTION_REGISTRY_DETAIL.md',
        'HOW_TO_RUN.md',
        'QUICK_REFERENCE.md',
        'UI_MIGRATION_PLAN_DETAIL.md',
        'TODO.md',
        'TESTING_IMPROVEMENT_PLAN_DETAIL.md',
        'DEVELOPMENT_GUIDELINES.md',
        'MODULE_DEPENDENCIES_DETAIL.md'
    ]
    
    for doc_file in doc_files:
        file_path = project_root / doc_file
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                docs[doc_file] = f.read()
    
    return docs

def extract_sections(content: str) -> Dict[str, str]:
    """Extract sections from markdown content."""
    sections = {}
    
    # Split by headers (## or ###)
    lines = content.split('\n')
    current_section = "Introduction"
    current_content = []
    
    for line in lines:
        if line.startswith('## ') or line.startswith('### '):
            # Save previous section
            if current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # Start new section
            current_section = line.strip('#').strip()
            current_content = []
        else:
            current_content.append(line)
    
    # Save last section
    if current_content:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return sections

def find_common_topics(docs: Dict[str, str]) -> Dict[str, List[str]]:
    """Find common topics across documentation files."""
    common_topics = {
        'setup_installation': [],
        'development_workflow': [],
        'testing': [],
        'ui_migration': [],
        'architecture': [],
        'troubleshooting': [],
        'code_quality': [],
        'project_structure': []
    }
    
    topic_keywords = {
        'setup_installation': ['install', 'setup', 'run', 'start', 'virtual environment', 'requirements'],
        'development_workflow': ['workflow', 'development', 'git', 'commit', 'branch', 'merge'],
        'testing': ['test', 'testing', 'coverage', 'pytest', 'unit test'],
        'ui_migration': ['ui', 'migration', 'pyside', 'tkinter', 'qt'],
        'architecture': ['architecture', 'structure', 'modules', 'dependencies'],
        'troubleshooting': ['troubleshoot', 'error', 'fix', 'debug', 'problem'],
        'code_quality': ['quality', 'style', 'lint', 'format', 'best practice'],
        'project_structure': ['structure', 'directory', 'file', 'organization']
    }
    
    for filename, content in docs.items():
        content_lower = content.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                common_topics[topic].append(filename)
    
    return common_topics

def analyze_file_purposes(docs: Dict[str, str]) -> Dict[str, Dict]:
    """Analyze the purpose and content of each documentation file."""
    purposes = {}
    
    for filename, content in docs.items():
        # Extract first few lines to understand purpose
        lines = content.split('\n')[:20]
        header_info = '\n'.join(lines)
        
        # Count sections
        sections = extract_sections(content)
        
        # Estimate content length
        content_length = len(content)
        
        purposes[filename] = {
            'header_info': header_info,
            'section_count': len(sections),
            'content_length': content_length,
            'sections': list(sections.keys())
        }
    
    return purposes

def generate_consolidation_report():
    """Generate a report on documentation consolidation opportunities."""
    print("[DOC] Analyzing documentation files...")
    docs = get_documentation_files()
    
    print(f"\n[STATS] DOCUMENTATION ANALYSIS REPORT")
    print("="*60)
    
    print(f"\n[FILES] Files Found: {len(docs)}")
    for filename in sorted(docs.keys()):
        print(f"   - {filename}")
    
    # Analyze purposes
    purposes = analyze_file_purposes(docs)
    
    print(f"\n[INFO] FILE PURPOSES & CONTENT:")
    for filename, info in sorted(purposes.items()):
        print(f"\n[FILE] {filename}")
        print(f"   Length: {info['content_length']:,} characters")
        print(f"   Sections: {info['section_count']}")
        # Replace non-ASCII characters in section names
        safe_sections = [s.encode('ascii', 'replace').decode('ascii') for s in info['sections'][:5]]
        print(f"   Main sections: {', '.join(safe_sections)}")
    
    # Find common topics
    common_topics = find_common_topics(docs)
    
    print(f"\n[DIR] COMMON TOPICS ACROSS FILES:")
    for topic, files in common_topics.items():
        if files:
            print(f"\n   {topic.replace('_', ' ').title()}:")
            for file in files:
                print(f"      - {file}")
    
    # Identify consolidation opportunities
    print(f"\n[IDEA] CONSOLIDATION RECOMMENDATIONS:")
    
    # Group by purpose
    setup_files = [f for f in docs.keys() if 'setup' in f.lower() or 'run' in f.lower()]
    if len(setup_files) > 1:
        print(f"\n   [SETUP] Setup/Installation Files ({len(setup_files)} files):")
        for file in setup_files:
            print(f"      - {file}")
        print(f"      → Consolidate into single 'SETUP.md'")
    
    workflow_files = [f for f in docs.keys() if 'workflow' in f.lower() or 'development' in f.lower()]
    if len(workflow_files) > 1:
        print(f"\n   [WORKFLOW] Workflow Files ({len(workflow_files)} files):")
        for file in workflow_files:
            print(f"      - {file}")
        print(f"      → Consolidate into single 'DEVELOPMENT.md'")
    
    # Identify redundant information
    print(f"\n[REDUNDANT] REDUNDANT INFORMATION:")
    
    # Check for duplicate sections
    all_sections = set()
    duplicate_sections = set()
    
    for filename, content in docs.items():
        sections = extract_sections(content)
        for section in sections.keys():
            if section in all_sections:
                duplicate_sections.add(section)
            all_sections.add(section)
    
    if duplicate_sections:
        print(f"   Sections appearing in multiple files:")
        for section in sorted(duplicate_sections):
            safe_section = section.encode('ascii', 'replace').decode('ascii')
            print(f"      - {safe_section}")
    
    # Recommend new structure
    print(f"\n[STRUCTURE] RECOMMENDED NEW STRUCTURE:")
    print(f"   [FILE] README.md - Project overview and quick start")
    print(f"   [FILE] SETUP.md - Installation and setup instructions")
    print(f"   [FILE] DEVELOPMENT.md - Development workflow and guidelines")
    print(f"   [FILE] ARCHITECTURE.md - System architecture and design")
    print(f"   [FILE] API.md - Function registry and module dependencies")
    print(f"   [FILE] CHANGELOG.md - Version history and changes")
    print(f"   [FILE] TODO.md - Current priorities and planned work")

if __name__ == "__main__":
    generate_consolidation_report() 