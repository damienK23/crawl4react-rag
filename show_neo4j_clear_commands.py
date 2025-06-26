#!/usr/bin/env python3
"""
Script pour afficher et exécuter les commandes de nettoyage Neo4j
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("🗑️  NEO4J REPOSITORY CLEANER COMMANDS")
print("=" * 60)

print("\n📋 Pour effacer complètement un repository spécifique :")
print("python clear_neo4j_repository.py --repo-name 'nom_du_repo'")

print("\n📋 Pour afficher la structure actuelle :")
print("python clear_neo4j_repository.py --show-structure")

print("\n📋 Pour effacer TOUTES les données (⚠️  DANGEREUX) :")
print("echo 'DELETE ALL' | python clear_neo4j_repository.py --clear-all")

print("\n🔧 Commandes Neo4j Cypher directes :")
print("=" * 40)

print("\n# Effacer un repository spécifique :")
print("MATCH (r:Repository {name: 'test-hierarchy'})")
print("DETACH DELETE r")

print("\n# Effacer tous les fichiers d'un chemin spécifique :")
print("MATCH (f:File)")
print("WHERE f.path CONTAINS 'test_files'")
print("DETACH DELETE f")

print("\n# Effacer TOUT (⚠️  ATTENTION) :")
print("MATCH (n) DETACH DELETE n")

print("\n# Afficher tous les repositories :")
print("MATCH (r:Repository)")
print("RETURN r.name, count{(r)-[:CONTAINS]->()} as files")

print("\n# Afficher la hiérarchie propre d'un repository :")
print("""
MATCH (r:Repository {name: 'test-hierarchy'})-[:CONTAINS]->(f:File)
OPTIONAL MATCH (f)-[:DEFINES]->(comp:Component)
OPTIONAL MATCH (comp)-[:HAS_PROPS]->(props:Props)
OPTIONAL MATCH (comp)-[:USES_HOOK]->(hook:Hook)
OPTIONAL MATCH (f)-[:DEFINES]->(func:Function)
OPTIONAL MATCH (f)-[:DEFINES]->(c:Class)-[:HAS_METHOD]->(m:Method)
RETURN f.name as file, 
       collect(DISTINCT comp.name) as components,
       collect(DISTINCT func.name) as functions,
       collect(DISTINCT c.name) as classes,
       collect(DISTINCT m.name) as methods
ORDER BY f.name
""")

print("\n💡 EXEMPLE D'ARBORESCENCE SOUHAITÉE :")
print("=" * 50)
print("""
Repository: mcp-crawl4react-rag
├── File: src/crawl4react_mcp.py
│   ├── Class: Crawl4AIContext
│   │   ├── Method: __init__
│   │   ├── Method: initialize
│   │   └── Attribute: session
│   ├── Function: comprehensive_validation
│   └── Function: analyze_supabase_schema
├── File: test_files/database_hallucination_test.tsx
│   ├── Component: DatabaseHallucinationTest (React)
│   │   ├── Props: {}
│   │   ├── Hook: useState
│   │   ├── Hook: useEffect
│   │   └── State: users, loading
│   ├── Interface: User
│   └── Function: fetchUsers
└── File: knowledge_graphs/neo4j_clean_hierarchy.py
    ├── Class: CleanHierarchyParser
    │   ├── Method: initialize
    │   ├── Method: parse_repository
    │   └── Method: _create_component_hierarchy
    └── Function: clean_parse_repository
""")

print("\n🎯 OBJECTIFS DE LA HIÉRARCHIE PROPRE :")
print("✅ Structure claire: Repository → File → Class/Component/Function")
print("✅ IDs uniques et prévisibles")
print("✅ Relations explicites (CONTAINS, DEFINES, HAS_METHOD, etc.)")
print("✅ Métadonnées complètes (line_number, types, etc.)")
print("✅ Support React/TypeScript spécialisé")
print("✅ Navigation intuitive dans Neo4j Browser")

print(f"\n🔗 Neo4j Browser: http://localhost:7474")
print(f"🔗 Neo4j URI: {os.getenv('NEO4J_URI')}")
print(f"👤 Neo4j User: {os.getenv('NEO4J_USER')}")

print("\n🧹 POUR TOUT REMETTRE À ZÉRO :")
print("1. Ouvrir Neo4j Browser")
print("2. Exécuter: MATCH (n) DETACH DELETE n")
print("3. Puis exécuter le parser avec hiérarchie propre")

print("\n📝 VALIDATION DES ENTRÉES/SORTIES RPC :")
print("Actuellement détecté : ✅ Existence des fonctions RPC")
print("À améliorer : ❌ Validation détaillée des paramètres")
print("             ❌ Types de paramètres (string vs UUID)")
print("             ❌ Paramètres obligatoires vs optionnels")
print("             ❌ Validation des valeurs enum")
print("             ❌ Structure des objets JSON")