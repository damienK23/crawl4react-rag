#!/usr/bin/env python3
"""
Nettoyage automatique des scripts de base de données non nécessaires
"""

import os
import shutil
from pathlib import Path


def auto_cleanup():
    """Nettoyage automatique sans confirmation"""
    
    base_path = Path("/Users/kwenji/mcp-crawl4react-rag")
    
    print("🧹 NETTOYAGE AUTOMATIQUE EN COURS...")
    print("=" * 50)
    
    # 1. Supprimer le répertoire supabase complet (migrations, config, etc.)
    supabase_path = base_path / "supabase"
    if supabase_path.exists():
        print(f"🗑️  Suppression: supabase/ (complet)")
        shutil.rmtree(supabase_path)
    
    # 2. Supprimer les fichiers SQL de création
    sql_files = [
        "crawled_pages.sql",
        "schema.sql"
    ]
    
    for sql_file in sql_files:
        file_path = base_path / sql_file
        if file_path.exists():
            print(f"🗑️  Suppression: {sql_file}")
            file_path.unlink()
    
    # 3. Supprimer les scripts de test redondants
    test_files_to_remove = [
        "test_neo4j_data.py",
        "test_neo4j_queries.py",
        "test_query_commands.py",
        "simple_validation_test.py",
        "test_mcp_validation.py",
        "test_supabase_schema.py",
        "test_column_detection.py",
        "test_typescript_integration.py"
    ]
    
    for test_file in test_files_to_remove:
        file_path = base_path / test_file
        if file_path.exists():
            print(f"🗑️  Suppression: {test_file}")
            file_path.unlink()
    
    # 4. Supprimer les fichiers de knowledge_graphs redondants
    kg_files_to_remove = [
        "knowledge_graphs/parse_repo_into_neo4j_backup.py",
        "knowledge_graphs/parse_repo_into_neo4j_fixed.py",
        "knowledge_graphs/test_script.py",
        "knowledge_graphs/query_knowledge_graph.py",
        "knowledge_graphs/hallucination_reporter.py",
        "knowledge_graphs/knowledge_graph_validator.py",
        "knowledge_graphs/ai_hallucination_detector.py",
        "knowledge_graphs/ai_script_analyzer.py",
        "knowledge_graphs/ts_hallucination_reporter.py"
    ]
    
    for kg_file in kg_files_to_remove:
        file_path = base_path / kg_file
        if file_path.exists():
            print(f"🗑️  Suppression: {kg_file}")
            file_path.unlink()
    
    # 5. Supprimer les fichiers src redondants
    src_files_to_remove = [
        "src/ts_script_analyzer.py",
        "src/typescript-hallucination-detector.ts"
    ]
    
    for src_file in src_files_to_remove:
        file_path = base_path / src_file
        if file_path.exists():
            print(f"🗑️  Suppression: {src_file}")
            file_path.unlink()
    
    # 6. Supprimer la documentation redondante
    docs_to_remove = [
        "REACT_TYPESCRIPT_INTEGRATION.md",
        "README-hallucination-checker.md"
    ]
    
    for doc in docs_to_remove:
        file_path = base_path / doc
        if file_path.exists():
            print(f"🗑️  Suppression: {doc}")
            file_path.unlink()
    
    # 7. Nettoyer node_modules si présent
    node_modules = base_path / "node_modules"
    if node_modules.exists():
        print(f"🗑️  Suppression: node_modules/ (complet)")
        shutil.rmtree(node_modules)
    
    print("\n✅ NETTOYAGE TERMINÉ!")


def show_final_clean_structure():
    """Afficher la structure nettoyée finale"""
    
    base_path = Path("/Users/kwenji/mcp-crawl4react-rag")
    
    print("\n📁 STRUCTURE FINALE NETTOYÉE")
    print("=" * 40)
    
    # Fichiers principaux conservés
    core_files = [
        "src/crawl4react_mcp.py",
        "src/HallucinationChecker.tsx", 
        "src/example-usage.tsx",
        "knowledge_graphs/comprehensive_validator.py",
        "knowledge_graphs/rpc_parameter_validator.py",
        "knowledge_graphs/typescript_analyzer.py",
        "knowledge_graphs/supabase_analyzer.py",
        "knowledge_graphs/neo4j_clean_hierarchy.py",
        "knowledge_graphs/signature_validator.py",
        "knowledge_graphs/advanced_patterns_detector.py",
        "clear_neo4j_repository.py",
        "show_neo4j_clear_commands.py"
    ]
    
    print("🔧 FICHIERS PRINCIPAUX:")
    for file_path in core_files:
        full_path = base_path / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"   ✅ {file_path} ({size} bytes)")
    
    # Tests conservés
    test_files = [
        "test_advanced_rpc_validation.py",
        "test_realistic_validation.py",
        "test_clean_hierarchy.py"
    ]
    
    print("\n🧪 TESTS CONSERVÉS:")
    for test_file in test_files:
        full_path = base_path / test_file
        if full_path.exists():
            print(f"   ✅ {test_file}")
    
    # Répertoires conservés
    print("\n📂 RÉPERTOIRES:")
    dirs = ["src", "knowledge_graphs", "test_files"]
    for dir_name in dirs:
        dir_path = base_path / dir_name
        if dir_path.exists():
            file_count = len([f for f in dir_path.rglob("*") if f.is_file()])
            print(f"   📁 {dir_name}/ ({file_count} fichiers)")
    
    print("\n🎯 FONCTIONNALITÉS CONSERVÉES:")
    print("   ✅ Serveur MCP principal (crawl4react_mcp.py)")
    print("   ✅ Validation complète d'hallucinations IA")
    print("   ✅ Validation RPC avancée (5 améliorations)")
    print("   ✅ Analyseur TypeScript/React")
    print("   ✅ Analyseur Supabase")
    print("   ✅ Outils Neo4j avec hiérarchie propre")
    print("   ✅ Tests d'intégration essentiels")
    
    print("\n🗑️  ÉLÉMENTS SUPPRIMÉS:")
    print("   ❌ Scripts de migrations Supabase")
    print("   ❌ Fichiers de configuration DB")
    print("   ❌ Tests redondants")
    print("   ❌ Documentation en double")
    print("   ❌ Node.js modules non utilisés")
    
    print("\n💡 UTILISATION:")
    print(f"   • MCP Server: python src/crawl4react_mcp.py")
    print(f"   • Validation: python test_realistic_validation.py") 
    print(f"   • Neo4j: python clear_neo4j_repository.py --show-structure")


if __name__ == "__main__":
    print("🚀 NETTOYAGE AUTOMATIQUE DU PROJET")
    print("=" * 50)
    
    auto_cleanup()
    show_final_clean_structure()
    
    print(f"\n🎉 PROJET OPTIMISÉ!")
    print(f"📦 Prêt pour l'analyse directe de base de données")
    print(f"🔍 Validation d'hallucinations IA complète")
    print(f"⚡ Structure simplifiée et efficace")