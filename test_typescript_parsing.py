#!/usr/bin/env python3
"""
Test du parsing TypeScript avec @babel/parser installé
"""

import os
import sys
from pathlib import Path

# Add knowledge_graphs to path
knowledge_graphs_path = Path(__file__).parent / 'knowledge_graphs'
sys.path.insert(0, str(knowledge_graphs_path))

from typescript_analyzer import TypeScriptAnalyzer


def test_typescript_parsing():
    """Test du parsing sur les exemples TypeScript"""
    print("🧪 TEST DU PARSING TYPESCRIPT")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = TypeScriptAnalyzer()
    
    # Test files in /exemple
    exemple_dir = Path(__file__).parent / 'exemple'
    
    if not exemple_dir.exists():
        print("❌ Dossier /exemple introuvable")
        return
    
    tsx_files = list(exemple_dir.glob("*.tsx"))
    
    if not tsx_files:
        print("❌ Aucun fichier .tsx trouvé dans /exemple")
        return
    
    print(f"📄 Fichiers .tsx trouvés: {len(tsx_files)}")
    
    for tsx_file in tsx_files:
        print(f"\n🔍 Test parsing: {tsx_file.name}")
        print("-" * 30)
        
        try:
            # Test the TypeScript analysis
            repo_root = Path(__file__).parent
            project_modules = {'example', 'src'}
            
            result = analyzer.analyze_typescript_file(
                tsx_file, repo_root, project_modules
            )
            
            if result:
                print(f"✅ Parsing réussi!")
                print(f"   📄 File path: {result.file_path}")
                print(f"   ⚛️  Components: {len(result.components)}")
                print(f"   🪝 Hook calls: {len(result.hook_calls)}")
                print(f"   🔧 Function calls: {len(result.function_calls)}")
                print(f"   📥 Imports: {len(result.imports)}")
                print(f"   📤 Exports: {len(result.exports)}")
                print(f"   ❌ Errors: {len(result.errors)}")
                
                # Show some details
                if result.components:
                    print(f"   🎯 Premier component: {result.components[0].name}")
                
                if result.function_calls:
                    print(f"   🎯 Premier function call: {result.function_calls[0].function_name}")
                    
                if result.imports:
                    print(f"   🎯 Premier import: {result.imports[0].name} from '{result.imports[0].module}'")
                    
                if result.errors:
                    print(f"   ⚠️  Première erreur: {result.errors[0]}")
                    
            else:
                print(f"⚠️  Parsing échoué - Aucun résultat retourné")
                
        except Exception as e:
            print(f"❌ Erreur lors du parsing:")
            print(f"   {str(e)}")
    
    print(f"\n🎯 Test terminé!")


if __name__ == "__main__":
    test_typescript_parsing()