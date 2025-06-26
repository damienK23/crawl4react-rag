#!/usr/bin/env python3
"""
Script pour effacer complètement un repository dans Neo4j et recréer une arborescence propre

Usage:
    python clear_neo4j_repository.py --repo-name "nom_du_repo" --clear-all
"""

import asyncio
import argparse
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


class Neo4jRepositoryCleaner:
    """Nettoyeur de repositories Neo4j avec arborescence optimisée"""
    
    def __init__(self):
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_user = os.getenv("NEO4J_USER") 
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        if not all([self.neo4j_uri, self.neo4j_user, self.neo4j_password]):
            raise ValueError("Neo4j credentials not found in environment variables")
    
    async def clear_repository(self, repo_name: str):
        """Effacer complètement un repository"""
        print(f"🗑️  CLEARING REPOSITORY: {repo_name}")
        print("=" * 50)
        
        parser = DirectNeo4jExtractor(
            self.neo4j_uri, self.neo4j_user, self.neo4j_password
        )
        
        try:
            # Initialize connection
            await parser.initialize()
            
            # Clear the repository data
            await parser.clear_repository_data(repo_name)
            
            print(f"✅ Repository '{repo_name}' cleared successfully")
            
        except Exception as e:
            print(f"❌ Error clearing repository: {e}")
            raise
        finally:
            await parser.close()
    
    async def clear_all_data(self):
        """Effacer TOUTES les données Neo4j"""
        print("🧨 CLEARING ALL NEO4J DATA")
        print("=" * 50)
        print("⚠️  WARNING: This will delete EVERYTHING in your Neo4j database!")
        
        confirmation = input("Type 'DELETE ALL' to confirm: ")
        if confirmation != "DELETE ALL":
            print("❌ Operation cancelled")
            return
        
        parser = DirectNeo4jExtractor(
            self.neo4j_uri, self.neo4j_user, self.neo4j_password
        )
        
        try:
            await parser.initialize()
            
            # Clear everything
            async with parser.driver.session() as session:
                print("🗑️  Deleting all nodes and relationships...")
                await session.run("MATCH (n) DETACH DELETE n")
                
                print("🔧 Recreating constraints and indexes...")
                # Recreate constraints
                await session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE")
                await session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Class) REQUIRE c.full_name IS UNIQUE")
                await session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (comp:Component) REQUIRE comp.comp_id IS UNIQUE")
                await session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (hook:Hook) REQUIRE hook.hook_id IS UNIQUE")
                await session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (r:Repository) REQUIRE r.name IS UNIQUE")
                
                # Recreate indexes
                await session.run("CREATE INDEX IF NOT EXISTS FOR (f:File) ON (f.name)")
                await session.run("CREATE INDEX IF NOT EXISTS FOR (c:Class) ON (c.name)")
                await session.run("CREATE INDEX IF NOT EXISTS FOR (m:Method) ON (m.name)")
                await session.run("CREATE INDEX IF NOT EXISTS FOR (comp:Component) ON (comp.name)")
                await session.run("CREATE INDEX IF NOT EXISTS FOR (hook:Hook) ON (hook.name)")
            
            print("✅ All data cleared and database reset")
            
        except Exception as e:
            print(f"❌ Error clearing all data: {e}")
            raise
        finally:
            await parser.close()
    
    async def show_repository_structure(self, repo_name: str = None):
        """Afficher la structure actuelle"""
        print("📊 NEO4J DATABASE STRUCTURE")
        print("=" * 50)
        
        parser = DirectNeo4jExtractor(
            self.neo4j_uri, self.neo4j_user, self.neo4j_password
        )
        
        try:
            await parser.initialize()
            
            async with parser.driver.session() as session:
                # Show repositories
                if repo_name:
                    repos_query = "MATCH (r:Repository {name: $repo_name}) RETURN r.name as name, r.url as url"
                    result = await session.run(repos_query, repo_name=repo_name)
                else:
                    repos_query = "MATCH (r:Repository) RETURN r.name as name, r.url as url"
                    result = await session.run(repos_query)
                
                repos = await result.data()
                
                if not repos:
                    if repo_name:
                        print(f"❌ Repository '{repo_name}' not found")
                    else:
                        print("❌ No repositories found")
                    return
                
                for repo in repos:
                    print(f"📦 Repository: {repo['name']}")
                    if repo['url']:
                        print(f"   URL: {repo['url']}")
                    
                    # Show files for this repository
                    files_query = """
                    MATCH (r:Repository {name: $repo_name})-[:CONTAINS]->(f:File)
                    RETURN f.path as path, f.name as name, f.extension as ext
                    ORDER BY f.path
                    """
                    files_result = await session.run(files_query, repo_name=repo['name'])
                    files = await files_result.data()
                    
                    print(f"   📁 Files: {len(files)}")
                    
                    for file in files[:10]:  # Show first 10 files
                        print(f"      📄 {file['path']}")
                        
                        # Show classes/components in this file
                        classes_query = """
                        MATCH (f:File {path: $file_path})-[:DEFINES]->(c:Class)
                        RETURN c.name as name, c.type as type
                        """
                        classes_result = await session.run(classes_query, file_path=file['path'])
                        classes = await classes_result.data()
                        
                        for cls in classes:
                            print(f"         🏛️  Class: {cls['name']} ({cls['type']})")
                        
                        # Show React components
                        components_query = """
                        MATCH (f:File {path: $file_path})-[:DEFINES]->(comp:Component)
                        RETURN comp.name as name, comp.type as type
                        """
                        components_result = await session.run(components_query, file_path=file['path'])
                        components = await components_result.data()
                        
                        for comp in components:
                            print(f"         ⚛️  Component: {comp['name']} ({comp['type']})")
                        
                        # Show functions
                        functions_query = """
                        MATCH (f:File {path: $file_path})-[:DEFINES]->(func:Function)
                        RETURN func.name as name, func.type as type
                        """
                        functions_result = await session.run(functions_query, file_path=file['path'])
                        functions = await functions_result.data()
                        
                        for func in functions:
                            print(f"         🔧 Function: {func['name']} ({func['type']})")
                    
                    if len(files) > 10:
                        print(f"      ... and {len(files) - 10} more files")
                    
                    print()
                
                # Show summary statistics
                stats_queries = [
                    ("Repositories", "MATCH (r:Repository) RETURN count(r) as count"),
                    ("Files", "MATCH (f:File) RETURN count(f) as count"),
                    ("Classes", "MATCH (c:Class) RETURN count(c) as count"),
                    ("Components", "MATCH (comp:Component) RETURN count(comp) as count"),
                    ("Functions", "MATCH (func:Function) RETURN count(func) as count"),
                    ("Methods", "MATCH (m:Method) RETURN count(m) as count"),
                    ("Hooks", "MATCH (h:Hook) RETURN count(h) as count"),
                ]
                
                print("📈 SUMMARY STATISTICS:")
                for name, query in stats_queries:
                    result = await session.run(query)
                    data = await result.single()
                    print(f"   {name}: {data['count']}")
            
        except Exception as e:
            print(f"❌ Error showing structure: {e}")
            raise
        finally:
            await parser.close()


async def main():
    parser = argparse.ArgumentParser(description="Neo4j Repository Cleaner")
    parser.add_argument("--repo-name", help="Name of repository to clear")
    parser.add_argument("--clear-all", action="store_true", help="Clear ALL data in Neo4j")
    parser.add_argument("--show-structure", action="store_true", help="Show current database structure")
    
    args = parser.parse_args()
    
    cleaner = Neo4jRepositoryCleaner()
    
    try:
        if args.clear_all:
            await cleaner.clear_all_data()
        elif args.repo_name:
            await cleaner.clear_repository(args.repo_name)
        elif args.show_structure:
            repo = args.repo_name if hasattr(args, 'repo_name') else None
            await cleaner.show_repository_structure(repo)
        else:
            # Show help and current structure
            parser.print_help()
            print("\n")
            await cleaner.show_repository_structure()
    
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("🧹 NEO4J REPOSITORY CLEANER")
    print("=" * 50)
    
    # Check environment
    required_vars = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file")
        sys.exit(1)
    
    print(f"🔗 Neo4j URI: {os.getenv('NEO4J_URI')}")
    print(f"👤 Neo4j User: {os.getenv('NEO4J_USER')}")
    print()
    
    asyncio.run(main())