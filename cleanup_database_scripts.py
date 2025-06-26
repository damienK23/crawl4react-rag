#!/usr/bin/env python3
"""
Script de nettoyage pour supprimer les scripts de création/migration de base de données
et autres éléments non nécessaires pour l'analyse directe de la base.
"""

import os
import shutil
from pathlib import Path


def cleanup_database_scripts():
    """Nettoyer les scripts de base de données non nécessaires"""
    
    base_path = Path("/Users/kwenji/mcp-crawl4ai-rag")
    
    print("🧹 NETTOYAGE DES SCRIPTS DE BASE DE DONNÉES")
    print("=" * 60)
    
    # Répertoires à supprimer complètement
    directories_to_remove = [
        "supabase/migrations",
        "supabase/functions", 
        "supabase/buckets",
        "supabase/seed.sql",
        "supabase/config.toml",
        "crawled_pages.sql",
        "schema.sql"
    ]
    
    # Scripts spécifiques à supprimer
    files_to_remove = [
        "supabase/seed.sql",
        "crawled_pages.sql",
        "schema.sql",
        "supabase/config.toml",
        # Scripts de test de création
        "test_neo4j_data.py",
        "test_neo4j_queries.py", 
        "test_query_commands.py",
        # Fichiers de backup/versions
        "knowledge_graphs/parse_repo_into_neo4j_backup.py",
        "knowledge_graphs/parse_repo_into_neo4j_fixed.py",
        "knowledge_graphs/test_script.py",
        "knowledge_graphs/query_knowledge_graph.py",
        "knowledge_graphs/hallucination_reporter.py",
        "knowledge_graphs/knowledge_graph_validator.py",
        "knowledge_graphs/ai_hallucination_detector.py",
        # Scripts obsolètes
        "src/ts_script_analyzer.py",
        "src/typescript-hallucination-detector.ts",
        # Tests redondants
        "simple_validation_test.py",
        "test_mcp_validation.py",
        "test_supabase_schema.py",
        "test_column_detection.py",
        "test_typescript_integration.py"
    ]
    
    removed_count = 0
    
    # Supprimer les répertoires
    for dir_path in directories_to_remove:
        full_path = base_path / dir_path
        if full_path.exists():
            if full_path.is_dir():
                print(f"🗑️  Suppression du répertoire: {dir_path}")
                shutil.rmtree(full_path)
                removed_count += 1
            elif full_path.is_file():
                print(f"🗑️  Suppression du fichier: {dir_path}")
                full_path.unlink()
                removed_count += 1
    
    # Supprimer les fichiers spécifiques
    for file_path in files_to_remove:
        full_path = base_path / file_path
        if full_path.exists() and full_path.is_file():
            print(f"🗑️  Suppression du fichier: {file_path}")
            full_path.unlink()
            removed_count += 1
    
    # Supprimer le répertoire supabase/migrations complètement
    migrations_path = base_path / "supabase"
    if migrations_path.exists():
        print(f"🗑️  Suppression complète du répertoire supabase/")
        shutil.rmtree(migrations_path)
        removed_count += 1
    
    # Nettoyer les scripts de Node.js non nécessaires
    node_scripts_to_remove = [
        "package.json",
        "package-lock.json", 
        "node_modules"
    ]
    
    for item in node_scripts_to_remove:
        full_path = base_path / item
        if full_path.exists():
            if full_path.is_dir():
                print(f"🗑️  Suppression du répertoire Node.js: {item}")
                shutil.rmtree(full_path)
                removed_count += 1
            else:
                print(f"🗑️  Suppression du fichier Node.js: {item}")
                full_path.unlink()
                removed_count += 1
    
    print(f"\n✅ Nettoyage terminé: {removed_count} éléments supprimés")
    
    return removed_count


def cleanup_test_files():
    """Nettoyer les fichiers de test redondants"""
    
    base_path = Path("/Users/kwenji/mcp-crawl4ai-rag")
    
    print("\n🧪 NETTOYAGE DES FICHIERS DE TEST REDONDANTS")
    print("=" * 60)
    
    # Garder seulement les tests essentiels
    tests_to_keep = [
        "test_advanced_rpc_validation.py",
        "test_realistic_validation.py", 
        "test_clean_hierarchy.py"
    ]
    
    # Supprimer les autres tests
    test_files = list(base_path.glob("test_*.py"))
    removed_tests = 0
    
    for test_file in test_files:
        if test_file.name not in tests_to_keep:
            print(f"🗑️  Suppression du test: {test_file.name}")
            test_file.unlink()
            removed_tests += 1
    
    print(f"\n✅ Tests nettoyés: {removed_tests} fichiers supprimés")
    print(f"📁 Tests conservés: {', '.join(tests_to_keep)}")
    
    return removed_tests


def cleanup_documentation():
    """Nettoyer la documentation redondante"""
    
    base_path = Path("/Users/kwenji/mcp-crawl4ai-rag")
    
    print("\n📚 NETTOYAGE DE LA DOCUMENTATION REDONDANTE")
    print("=" * 60)
    
    docs_to_remove = [
        "REACT_TYPESCRIPT_INTEGRATION.md",
        "README-hallucination-checker.md"
    ]
    
    removed_docs = 0
    
    for doc in docs_to_remove:
        doc_path = base_path / doc
        if doc_path.exists():
            print(f"🗑️  Suppression de la documentation: {doc}")
            doc_path.unlink()
            removed_docs += 1
    
    print(f"\n✅ Documentation nettoyée: {removed_docs} fichiers supprimés")
    
    return removed_docs


def show_final_structure():
    """Afficher la structure finale nettoyée"""
    
    base_path = Path("/Users/kwenji/mcp-crawl4ai-rag")
    
    print("\n📁 STRUCTURE FINALE NETTOYÉE")
    print("=" * 50)
    
    important_files = [
        "src/crawl4ai_mcp.py",
        "knowledge_graphs/comprehensive_validator.py",
        "knowledge_graphs/rpc_parameter_validator.py",
        "knowledge_graphs/typescript_analyzer.py",
        "knowledge_graphs/supabase_analyzer.py",
        "knowledge_graphs/neo4j_clean_hierarchy.py",
        "clear_neo4j_repository.py",
        "show_neo4j_clear_commands.py"
    ]
    
    print("🔧 FICHIERS PRINCIPAUX CONSERVÉS:")
    for file_path in important_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (manquant)")
    
    print("\n📂 RÉPERTOIRES CONSERVÉS:")
    important_dirs = ["src", "knowledge_graphs", "test_files"]
    for dir_name in important_dirs:
        dir_path = base_path / dir_name
        if dir_path.exists():
            file_count = len(list(dir_path.rglob("*")))
            print(f"   ✅ {dir_name}/ ({file_count} éléments)")
        else:
            print(f"   ❌ {dir_name}/ (manquant)")


def create_minimal_package_json():
    """Créer un package.json minimal si nécessaire pour certains outils"""
    
    base_path = Path("/Users/kwenji/mcp-crawl4ai-rag")
    
    minimal_package = {
        "name": "mcp-crawl4ai-rag",
        "version": "1.0.0",
        "description": "MCP Crawl4AI RAG with AI hallucination detection",
        "private": True,
        "scripts": {
            "test": "echo 'No Node.js tests defined'"
        },
        "devDependencies": {
            "typescript": "^5.0.0"
        }
    }
    
    package_json_path = base_path / "package.json"
    
    # Seulement créer si des outils TypeScript sont nécessaires
    print("\n📦 PACKAGE.JSON MINIMAL")
    print("=" * 30)
    print("💡 Package.json minimal non créé - pas nécessaire pour le projet Python")
    print("   Si TypeScript est nécessaire, installer manuellement avec:")
    print("   npm init -y && npm install -D typescript")


if __name__ == "__main__":
    print("🚀 NETTOYAGE COMPLET DU PROJET MCP-CRAWL4AI-RAG")
    print("=" * 70)
    
    total_removed = 0
    
    # Demander confirmation
    print("⚠️  Ce script va supprimer:")
    print("   • Scripts de migrations Supabase")
    print("   • Fichiers de configuration de base de données")
    print("   • Tests redondants") 
    print("   • Documentation en double")
    print("   • Node.js modules non utilisés")
    print()
    
    confirm = input("Continuer le nettoyage ? (y/N): ").lower().strip()
    
    if confirm != 'y':
        print("❌ Nettoyage annulé")
        exit(0)
    
    # Exécuter le nettoyage
    total_removed += cleanup_database_scripts()
    total_removed += cleanup_test_files() 
    total_removed += cleanup_documentation()
    
    # Afficher la structure finale
    show_final_structure()
    create_minimal_package_json()
    
    print(f"\n🎉 NETTOYAGE TERMINÉ!")
    print(f"📊 Total supprimé: {total_removed} éléments")
    print("\n✅ PROJET OPTIMISÉ POUR:")
    print("   • Analyse directe de base de données Supabase")
    print("   • Validation d'hallucinations IA")
    print("   • Intégration MCP")
    print("   • Parser Neo4j avec hiérarchie propre")
    print("\n📋 FICHIERS PRINCIPAUX CONSERVÉS:")
    print("   • src/crawl4ai_mcp.py - Serveur MCP principal")
    print("   • knowledge_graphs/comprehensive_validator.py - Validation complète")
    print("   • knowledge_graphs/rpc_parameter_validator.py - Validation RPC avancée")
    print("   • test_files/ - Exemples de test")
    print("   • clear_neo4j_repository.py - Outils de nettoyage Neo4j")