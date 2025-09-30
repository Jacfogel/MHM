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
        'CHANGELOG_DETAIL.md', 
        'DEVELOPMENT_WORKFLOW.md',
        'DOCUMENTATION_GUIDE.md',
        'development_docs/FUNCTION_REGISTRY_DETAIL.md',
        'HOW_TO_RUN.md',
        'QUICK_REFERENCE.md',
        'UI_MIGRATION_PLAN_DETAIL.md',
        'TODO.md',
        'DEVELOPMENT_GUIDELINES.md',
        'development_docs/MODULE_DEPENDENCIES_DETAIL.md'
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

def detect_verbatim_duplicates():
    """Detect verbatim duplicates between AI and human documentation pairs."""
    import config
    project_root = config.get_project_root()
    
    # Define paired documentation files
    paired_docs = {
        'DEVELOPMENT_WORKFLOW.md': 'ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md',
        'ARCHITECTURE.md': 'ai_development_docs/AI_ARCHITECTURE.md',
        'DOCUMENTATION_GUIDE.md': 'ai_development_docs/AI_DOCUMENTATION_GUIDE.md',
        'development_docs/CHANGELOG_DETAIL.md': 'ai_development_docs/AI_CHANGELOG.md',
    }
    
    duplicates_found = []
    
    for human_doc, ai_doc in paired_docs.items():
        human_path = project_root / human_doc
        ai_path = project_root / ai_doc
        
        if not human_path.exists() or not ai_path.exists():
            continue
            
        try:
            with open(human_path, 'r', encoding='utf-8') as f:
                human_content = f.read()
            with open(ai_path, 'r', encoding='utf-8') as f:
                ai_content = f.read()
            
            # Extract sections from both files
            human_sections = extract_sections(human_content)
            ai_sections = extract_sections(ai_content)
            
            # Check for verbatim duplicates
            for section_name, section_content in human_sections.items():
                if section_name in ai_sections:
                    ai_section_content = ai_sections[section_name]
                    
                    # Normalize content for comparison (remove whitespace differences)
                    human_normalized = re.sub(r'\s+', ' ', section_content.strip())
                    ai_normalized = re.sub(r'\s+', ' ', ai_section_content.strip())
                    
                    # Check if content is verbatim duplicate (allowing for minor whitespace differences)
                    if human_normalized == ai_normalized and len(human_normalized) > 50:  # Only flag substantial duplicates
                        duplicates_found.append({
                            'human_file': human_doc,
                            'ai_file': ai_doc,
                            'section': section_name,
                            'content_length': len(human_normalized)
                        })
            
        except Exception as e:
            print(f"Error comparing {human_doc} and {ai_doc}: {e}")
    
    return duplicates_found

def check_placeholder_content():
    """Check for placeholder content in documentation."""
    import config
    project_root = config.get_project_root()
    
    # Define files to check
    files_to_check = [
        'ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md',
        'ai_development_docs/AI_ARCHITECTURE.md',
        'ai_development_docs/AI_DOCUMENTATION_GUIDE.md',
        'ai_development_docs/AI_CHANGELOG.md',
    ]
    
    placeholder_patterns = [
        r'\[Main Content Sections\]',
        r'\[Content\]',
        r'\[TODO\]',
        r'\[PLACEHOLDER\]',
        r'\[INSERT.*\]',
        r'\[.*Content.*\]',
        r'\[.*Section.*\]',
        r'\[.*TODO.*\]',
        r'\[.*PLACEHOLDER.*\]',
    ]
    
    placeholders_found = []
    
    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            continue
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for pattern in placeholder_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    placeholders_found.append({
                        'file': file_path,
                        'pattern': pattern,
                        'matches': matches
                    })
                    
        except Exception as e:
            print(f"Error checking {file_path}: {e}")
    
    return placeholders_found

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
        print(f"      -> Consolidate into single 'SETUP.md'")
    
    workflow_files = [f for f in docs.keys() if 'workflow' in f.lower() or 'development' in f.lower()]
    if len(workflow_files) > 1:
        print(f"\n   [WORKFLOW] Workflow Files ({len(workflow_files)} files):")
        for file in workflow_files:
            print(f"      - {file}")
        print(f"      -> Consolidate into single 'DEVELOPMENT.md'")
    
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
    
    # Check for verbatim duplicates
    print(f"\n[DUPLICATE] CHECKING FOR VERBATIM DUPLICATES:")
    duplicates = detect_verbatim_duplicates()
    if duplicates:
        print(f"   Found {len(duplicates)} verbatim duplicate sections:")
        for dup in duplicates:
            print(f"      - {dup['human_file']} <-> {dup['ai_file']}: '{dup['section']}' ({dup['content_length']} chars)")
        print(f"   -> FAIL: Remove verbatim duplicates between AI and human docs")
        return False
    else:
        print(f"   No verbatim duplicates found")
    
    # Check for placeholder content
    print(f"\n[PLACEHOLDER] CHECKING FOR PLACEHOLDER CONTENT:")
    placeholders = check_placeholder_content()
    if placeholders:
        print(f"   Found {len(placeholders)} files with placeholder content:")
        for placeholder in placeholders:
            print(f"      - {placeholder['file']}: {placeholder['matches']}")
        print(f"   -> FAIL: Replace placeholder content with actual content")
        return False
    else:
        print(f"   No placeholder content found")
    
    return True

if __name__ == "__main__":
    success = generate_consolidation_report()
    if not success:
        exit(1) 