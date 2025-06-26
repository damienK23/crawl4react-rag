#!/usr/bin/env python3
"""
Test de la hiérarchie propre sur un petit échantillon
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add knowledge_graphs to path
knowledge_graphs_path = Path(__file__).parent / 'knowledge_graphs'
sys.path.insert(0, str(knowledge_graphs_path))

from neo4j_clean_hierarchy import CleanHierarchyParser

# Load environment variables
load_dotenv()


async def test_clean_hierarchy():
    """Test la hiérarchie propre sur test_files/"""
    
    print("🧪 TESTING CLEAN HIERARCHY PARSER")
    print("=" * 50)
    
    parser = CleanHierarchyParser()
    
    try:
        await parser.initialize()
        
        # Clear any existing test data
        print("🗑️  Clearing existing test data...")
        try:
            await parser.clear_repository("test-hierarchy")
        except Exception as e:
            print(f"   Note: {e}")
        
        # Also clear manually to avoid conflicts
        async with parser.driver.session() as session:
            await session.run("MATCH (n) WHERE n.file_id CONTAINS 'test-hierarchy' DETACH DELETE n")
        
        # Test sur le dossier test_files/
        test_path = Path("/Users/kwenji/mcp-crawl4react-rag/test_files")
        
        if not test_path.exists():
            print(f"❌ Test path not found: {test_path}")
            return
        
        print(f"📁 Parsing test files from: {test_path}")
        
        # Créer le repository
        await parser._create_repository_node("test-hierarchy", "local-test")
        
        # Parser seulement les fichiers de test
        for file_path in test_path.glob("*.tsx"):
            print(f"   📄 Processing: {file_path.name}")
            await parser._parse_file(file_path, "test-hierarchy")
        
        print("✅ Test hierarchy parsing completed!")
        
        # Vérifier la structure créée
        await show_clean_structure(parser)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await parser.close()


async def show_clean_structure(parser):
    """Afficher la structure créée avec hiérarchie propre"""
    
    print("\n📊 CLEAN HIERARCHY STRUCTURE")
    print("=" * 50)
    
    async with parser.driver.session() as session:
        # Repository
        result = await session.run("""
            MATCH (r:Repository {name: 'test-hierarchy'})
            RETURN r.name as name, r.url as url, r.hierarchy_version as version
        """)
        repo_data = await result.single()
        
        if repo_data:
            print(f"📦 Repository: {repo_data['name']}")
            print(f"   URL: {repo_data['url']}")
            print(f"   Hierarchy Version: {repo_data['version']}")
        
        # Files et leur contenu
        result = await session.run("""
            MATCH (r:Repository {name: 'test-hierarchy'})-[:CONTAINS]->(f:File)
            RETURN f.file_id as file_id, f.name as name, f.relative_path as path
            ORDER BY f.name
        """)
        files = await result.data()
        
        print(f"\n📁 Files ({len(files)}):")
        
        for file in files:
            print(f"   📄 {file['name']}")
            
            # Components dans ce fichier
            comp_result = await session.run("""
                MATCH (f:File {file_id: $file_id})-[:DEFINES]->(comp:Component)
                RETURN comp.name as name, comp.type as type, comp.line_number as line
                ORDER BY comp.line_number
            """, file_id=file['file_id'])
            components = await comp_result.data()
            
            for comp in components:
                print(f"      ⚛️  Component: {comp['name']} ({comp['type']}) - line {comp['line']}")
                
                # Props du composant
                props_result = await session.run("""
                    MATCH (comp:Component {component_id: $comp_id})-[:HAS_PROPS]->(props:Props)
                    RETURN props.properties as properties, props.count as count
                """, comp_id=f"{file['file_id']}::{comp['name']}")
                props_data = await props_result.single()
                
                if props_data:
                    print(f"         📝 Props: {props_data['properties']} ({props_data['count']} total)")
                
                # Hooks utilisés
                hooks_result = await session.run("""
                    MATCH (comp:Component {component_id: $comp_id})-[:USES_HOOK]->(hook:Hook)
                    RETURN hook.name as name, hook.is_custom as custom
                    ORDER BY hook.name
                """, comp_id=f"{file['file_id']}::{comp['name']}")
                hooks = await hooks_result.data()
                
                if hooks:
                    print(f"         🪝 Hooks:")
                    for hook in hooks:
                        custom_flag = " (custom)" if hook['custom'] else ""
                        print(f"            - {hook['name']}{custom_flag}")
            
            # Functions dans ce fichier
            func_result = await session.run("""
                MATCH (f:File {file_id: $file_id})-[:DEFINES]->(func:Function)
                RETURN func.name as name, func.is_async as async, func.line_number as line
                ORDER BY func.line_number
            """, file_id=file['file_id'])
            functions = await func_result.data()
            
            for func in functions:
                async_flag = " (async)" if func['async'] else ""
                print(f"      🔧 Function: {func['name']}{async_flag} - line {func['line']}")
            
            # Classes dans ce fichier
            class_result = await session.run("""
                MATCH (f:File {file_id: $file_id})-[:DEFINES]->(c:Class)
                RETURN c.name as name, c.type as type, c.line_number as line
                ORDER BY c.line_number
            """, file_id=file['file_id'])
            classes = await class_result.data()
            
            for cls in classes:
                print(f"      🏛️  Class: {cls['name']} ({cls['type']}) - line {cls['line']}")
                
                # Methods de la classe
                method_result = await session.run("""
                    MATCH (c:Class {class_id: $class_id})-[:HAS_METHOD]->(m:Method)
                    RETURN m.name as name, m.visibility as visibility, m.is_static as static
                    ORDER BY m.name
                """, class_id=f"{file['file_id']}::{cls['name']}")
                methods = await method_result.data()
                
                for method in methods:
                    static_flag = " (static)" if method['static'] else ""
                    print(f"         🔨 Method: {method['visibility']} {method['name']}{static_flag}")
            
            # Interfaces dans ce fichier
            interface_result = await session.run("""
                MATCH (f:File {file_id: $file_id})-[:DEFINES]->(i:Interface)
                RETURN i.name as name, i.properties as properties
                ORDER BY i.name
            """, file_id=file['file_id'])
            interfaces = await interface_result.data()
            
            for interface in interfaces:
                print(f"      📋 Interface: {interface['name']}")
                if interface['properties']:
                    print(f"         Properties: {interface['properties']}")
            
            # Types dans ce fichier
            type_result = await session.run("""
                MATCH (f:File {file_id: $file_id})-[:DEFINES]->(t:TypeDefinition)
                RETURN t.name as name, t.kind as kind
                ORDER BY t.name
            """, file_id=file['file_id'])
            types = await type_result.data()
            
            for type_def in types:
                print(f"      📘 Type: {type_def['name']} ({type_def['kind']})")
        
        # Statistiques globales
        stats_queries = [
            ("Files", "MATCH (r:Repository {name: 'test-hierarchy'})-[:CONTAINS]->(f:File) RETURN count(f) as count"),
            ("Components", "MATCH (r:Repository {name: 'test-hierarchy'})-[:CONTAINS*]->(comp:Component) RETURN count(comp) as count"),
            ("Functions", "MATCH (r:Repository {name: 'test-hierarchy'})-[:CONTAINS*]->(func:Function) RETURN count(func) as count"),
            ("Classes", "MATCH (r:Repository {name: 'test-hierarchy'})-[:CONTAINS*]->(c:Class) RETURN count(c) as count"),
            ("Hooks", "MATCH (r:Repository {name: 'test-hierarchy'})-[:CONTAINS*]->(h:Hook) RETURN count(h) as count"),
            ("Methods", "MATCH (r:Repository {name: 'test-hierarchy'})-[:CONTAINS*]->(m:Method) RETURN count(m) as count"),
            ("Interfaces", "MATCH (r:Repository {name: 'test-hierarchy'})-[:CONTAINS*]->(i:Interface) RETURN count(i) as count"),
            ("Types", "MATCH (r:Repository {name: 'test-hierarchy'})-[:CONTAINS*]->(t:TypeDefinition) RETURN count(t) as count")
        ]
        
        print(f"\n📈 HIERARCHY STATISTICS:")
        for name, query in stats_queries:
            result = await session.run(query)
            data = await result.single()
            print(f"   {name}: {data['count']}")


if __name__ == "__main__":
    print("🌳 CLEAN HIERARCHY TEST")
    print("=" * 50)
    
    # Check environment
    required_vars = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    asyncio.run(test_clean_hierarchy())