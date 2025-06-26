#!/usr/bin/env python3
"""
Script pour nettoyer automatiquement tous les repositories Neo4j
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


async def clear_all_neo4j_data():
    """Effacer TOUTES les données Neo4j sans confirmation"""
    print("🧨 NETTOYAGE AUTOMATIQUE DE NEO4J")
    print("=" * 50)
    
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER") 
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    if not all([neo4j_uri, neo4j_user, neo4j_password]):
        print("❌ Neo4j credentials not found in environment variables")
        return False
    
    parser = DirectNeo4jExtractor(neo4j_uri, neo4j_user, neo4j_password)
    
    try:
        print("🔗 Connexion à Neo4j...")
        await parser.initialize()
        
        async with parser.driver.session() as session:
            print("🗑️  Suppression de tous les nodes et relations...")
            await session.run("MATCH (n) DETACH DELETE n")
            
            print("🔧 Recréation des contraintes et index...")
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
        
        print("✅ Toutes les données effacées et base reset")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")
        return False
    finally:
        await parser.close()


async def show_neo4j_status():
    """Afficher le statut de Neo4j après nettoyage"""
    print("\n📊 STATUT NEO4J APRÈS NETTOYAGE")
    print("=" * 40)
    
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER") 
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    parser = DirectNeo4jExtractor(neo4j_uri, neo4j_user, neo4j_password)
    
    try:
        await parser.initialize()
        
        async with parser.driver.session() as session:
            # Count nodes
            count_result = await session.run("MATCH (n) RETURN count(n) as total")
            record = await count_result.single()
            total_nodes = record['total'] if record else 0
            
            # Count relationships
            rel_result = await session.run("MATCH ()-[r]->() RETURN count(r) as total")
            rel_record = await rel_result.single()
            total_rels = rel_record['total'] if rel_record else 0
            
            print(f"📊 Nodes totaux: {total_nodes}")
            print(f"🔗 Relations totales: {total_rels}")
            
            if total_nodes == 0 and total_rels == 0:
                print("✅ Base de données Neo4j complètement vide")
            else:
                print(f"⚠️  Il reste encore {total_nodes} nodes et {total_rels} relations")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
    finally:
        await parser.close()


if __name__ == "__main__":
    print("🚀 NETTOYAGE AUTOMATIQUE NEO4J")
    print("=" * 50)
    
    async def main():
        success = await clear_all_neo4j_data()
        if success:
            await show_neo4j_status()
            print("\n🎯 PRÊT POUR NOUVEAU SCAN!")
        else:
            print("\n❌ ÉCHEC DU NETTOYAGE")
    
    asyncio.run(main())