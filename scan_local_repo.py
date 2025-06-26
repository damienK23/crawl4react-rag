#!/usr/bin/env python3
"""
Script pour scanner le repository local avec focus sur src/
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add knowledge_graphs to path
knowledge_graphs_path = Path(__file__).parent / 'knowledge_graphs'
sys.path.insert(0, str(knowledge_graphs_path))

from parse_repo_into_neo4j import DirectNeo4jExtractor

# Load environment variables
load_dotenv()


async def scan_local_repository():
    """Scanner le repository local actuel avec focus sur src/"""
    print("🔍 SCAN DU REPOSITORY LOCAL")
    print("=" * 50)
    
    # Get current directory as "repository"
    current_dir = Path(__file__).parent.absolute()
    repo_name = current_dir.name
    
    print(f"📁 Repository: {repo_name}")
    print(f"📂 Path: {current_dir}")
    
    # Check if src/ exists
    src_path = current_dir / 'src'
    if not src_path.exists():
        print(f"❌ No src/ directory found in {current_dir}")
        return False
    
    print(f"✅ src/ directory found at: {src_path}")
    
    # Initialize Neo4j extractor
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER") 
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    if not all([neo4j_uri, neo4j_user, neo4j_password]):
        print("❌ Neo4j credentials not found in environment variables")
        return False
    
    extractor = DirectNeo4jExtractor(neo4j_uri, neo4j_user, neo4j_password)
    
    try:
        print("🔗 Connexion à Neo4j...")
        await extractor.initialize()
        
        # Create a fake "repository URL" for local analysis
        fake_repo_url = f"local://{repo_name}"
        
        print(f"🚀 Début de l'analyse du repository local...")
        print(f"🎯 Focus sur: {src_path}")
        
        # Temporarily change the analyze method to work with local path
        await analyze_local_repository(extractor, str(current_dir), repo_name)
        
        print("✅ Analyse terminée!")
        
        # Show results
        await show_scan_results(extractor, repo_name)
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du scan: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await extractor.close()


async def analyze_local_repository(extractor, repo_path: str, repo_name: str):
    """Analyser le repository local sans clonage"""
    print(f"📊 Analysing repository: {repo_name}")
    
    # Clear existing data for this repository
    await extractor.clear_repository_data(repo_name)
    
    # Get source files from src/ only
    source_files = extractor.get_react_typescript_files(repo_path)
    python_files = extractor.get_python_files(repo_path)
    
    print(f"📄 Found {len(source_files)} React/TypeScript files in src/")
    print(f"🐍 Found {len(python_files)} Python files in src/")
    
    if not source_files and not python_files:
        print("⚠️  No files found in src/ directory")
        return
    
    # Skip manual Repository creation - let _create_graph handle it
    
    # Identify project modules for TypeScript
    repo_path_obj = Path(repo_path)
    project_modules = set()
    for file_path in source_files:
        relative_path = str(file_path.relative_to(repo_path_obj))
        module_parts = relative_path.replace('/', '.')
        for ext in ['.ts', '.tsx', '.js', '.jsx']:
            module_parts = module_parts.replace(ext, '')
        module_parts = module_parts.split('.')
        if len(module_parts) > 0 and not module_parts[0].startswith('.'):
            project_modules.add(module_parts[0])
    
    print(f"📦 Identified project modules: {sorted(project_modules)}")
    
    # Analyze TypeScript/React files
    modules_data = []
    for i, file_path in enumerate(source_files):
        if i % 5 == 0:
            print(f"📝 Processing TypeScript file {i+1}/{len(source_files)}: {file_path.name}")
        
        module_data = extractor.analyzer.analyze_typescript_file(
            file_path, repo_path_obj, project_modules
        )
        if module_data:
            modules_data.append(module_data)
    
    # Analyze Python files  
    python_data = []
    for i, file_path in enumerate(python_files):
        if i % 5 == 0:
            print(f"🐍 Processing Python file {i+1}/{len(python_files)}: {file_path.name}")
        
        py_data = extractor.analyzer.analyze_python_file(
            file_path, repo_path_obj, set()
        )
        if py_data:
            python_data.append(py_data)
    
    # Store data in Neo4j
    print("💾 Storing analysis results in Neo4j...")
    
    # Combine all module data
    all_modules_data = modules_data + python_data
    
    if all_modules_data:
        await extractor._create_graph(repo_name, all_modules_data)
    else:
        print("⚠️  No module data to store")
    
    print("✅ Data stored successfully in Neo4j")


async def show_scan_results(extractor, repo_name: str):
    """Afficher les résultats du scan"""
    print(f"\n📊 RÉSULTATS DU SCAN: {repo_name}")
    print("=" * 40)
    
    async with extractor.driver.session() as session:
        # Get comprehensive statistics
        stats_query = """
        MATCH (r:Repository {name: $repo_name})
        OPTIONAL MATCH (r)-[:CONTAINS]->(f:File)
        OPTIONAL MATCH (f)-[:DEFINES]->(c:Class)
        OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Method)
        OPTIONAL MATCH (f)-[:DEFINES]->(func:Function)
        OPTIONAL MATCH (f)-[:DEFINES]->(comp:Component)
        OPTIONAL MATCH (f)-[:DEFINES]->(hook:Hook)
        WITH r, 
             count(DISTINCT f) as files_count,
             count(DISTINCT c) as classes_count,
             count(DISTINCT m) as methods_count,
             count(DISTINCT func) as functions_count,
             count(DISTINCT comp) as components_count,
             count(DISTINCT hook) as hooks_count
        
        RETURN 
            r.name as repo_name,
            files_count,
            classes_count, 
            methods_count,
            functions_count,
            components_count,
            hooks_count
        """
        
        result = await session.run(stats_query, repo_name=repo_name)
        record = await result.single()
        
        if record:
            print(f"📁 Files processed: {record['files_count']}")
            print(f"📦 Classes found: {record['classes_count']}")
            print(f"⚙️  Methods found: {record['methods_count']}")
            print(f"🔧 Functions found: {record['functions_count']}")
            print(f"⚛️  React Components: {record['components_count']}")
            print(f"🪝 React Hooks: {record['hooks_count']}")
            
            # Show some sample files
            files_query = """
            MATCH (r:Repository {name: $repo_name})-[:CONTAINS]->(f:File)
            RETURN f.path as path, f.extension as ext
            ORDER BY f.path
            LIMIT 10
            """
            files_result = await session.run(files_query, repo_name=repo_name)
            files = await files_result.data()
            
            if files:
                print(f"\n📄 Sample files (showing first 10):")
                for file in files:
                    print(f"   📝 {file['path']} ({file['ext']})")
        else:
            print("❌ No data found for repository")


if __name__ == "__main__":
    print("🚀 SCAN LOCAL REPOSITORY WITH SRC/ FOCUS")
    print("=" * 50)
    
    asyncio.run(scan_local_repository())