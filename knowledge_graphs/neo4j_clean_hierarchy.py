#!/usr/bin/env python3
"""
Neo4j Clean Hierarchy Parser - Version optimisée pour une arborescence lisible

Crée une hiérarchie claire :
Repository
├── File
│   ├── Class
│   │   ├── Method
│   │   ├── Attribute
│   │   └── Property
│   ├── Component (React)
│   │   ├── Hook
│   │   ├── Props
│   │   └── State
│   ├── Function
│   └── Interface/Type
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, timezone

from neo4j import AsyncGraphDatabase
from typescript_analyzer import TypeScriptAnalyzer
from supabase_analyzer import SupabaseAnalyzer, SupabaseSchemaInfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CleanHierarchyParser:
    """Parser Neo4j avec hiérarchie claire et lisible"""
    
    def __init__(self):
        self.driver = None
        self.neo4j_uri = None
        self.neo4j_user = None
        self.neo4j_password = None
        self.ts_analyzer = TypeScriptAnalyzer()
        
        # Modules externes à ignorer
        self.external_modules = {
            'react', 'react-dom', 'next', 'lodash', 'axios', 'moment',
            'typescript', 'webpack', 'babel', 'eslint', 'prettier'
        }
    
    async def initialize(self):
        """Initialize Neo4j connection"""
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_user = os.getenv("NEO4J_USER")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        if not all([self.neo4j_uri, self.neo4j_user, self.neo4j_password]):
            raise ValueError("Neo4j credentials missing")
        
        self.driver = AsyncGraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
        await self._create_clean_schema()
    
    async def _create_clean_schema(self):
        """Créer un schéma Neo4j propre et optimisé"""
        logger.info("Creating clean Neo4j schema...")
        
        async with self.driver.session() as session:
            # === CONTRAINTES UNIQUES ===
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Repository) REQUIRE r.name IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (f:File) REQUIRE f.file_id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Class) REQUIRE c.class_id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Method) REQUIRE m.method_id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (comp:Component) REQUIRE comp.component_id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (func:Function) REQUIRE func.function_id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (t:TypeDefinition) REQUIRE t.type_id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Interface) REQUIRE i.interface_id IS UNIQUE"
            ]
            
            for constraint in constraints:
                await session.run(constraint)
            
            # === INDEX POUR PERFORMANCE ===
            indexes = [
                "CREATE INDEX IF NOT EXISTS FOR (f:File) ON (f.name, f.path)",
                "CREATE INDEX IF NOT EXISTS FOR (c:Class) ON (c.name)",
                "CREATE INDEX IF NOT EXISTS FOR (m:Method) ON (m.name)",
                "CREATE INDEX IF NOT EXISTS FOR (comp:Component) ON (comp.name)",
                "CREATE INDEX IF NOT EXISTS FOR (func:Function) ON (func.name)",
                "CREATE INDEX IF NOT EXISTS FOR (t:TypeDefinition) ON (t.name)",
                "CREATE INDEX IF NOT EXISTS FOR (i:Interface) ON (i.name)"
            ]
            
            for index in indexes:
                await session.run(index)
        
        logger.info("✅ Clean schema created")
    
    async def clear_repository(self, repo_name: str):
        """Effacer complètement un repository avec hiérarchie"""
        logger.info(f"🗑️  Clearing repository: {repo_name}")
        
        async with self.driver.session() as session:
            # Effacer en ordre hiérarchique inverse
            delete_queries = [
                # 1. Éléments de base (feuilles de l'arbre)
                "MATCH (r:Repository {name: $repo_name})-[:CONTAINS*]->(m:Method) DETACH DELETE m",
                "MATCH (r:Repository {name: $repo_name})-[:CONTAINS*]->(a:Attribute) DETACH DELETE a",
                "MATCH (r:Repository {name: $repo_name})-[:CONTAINS*]->(p:Property) DETACH DELETE p",
                "MATCH (r:Repository {name: $repo_name})-[:CONTAINS*]->(h:Hook) DETACH DELETE h",
                "MATCH (r:Repository {name: $repo_name})-[:CONTAINS*]->(pr:Props) DETACH DELETE pr",
                "MATCH (r:Repository {name: $repo_name})-[:CONTAINS*]->(s:State) DETACH DELETE s",
                
                # 2. Définitions de types
                "MATCH (r:Repository {name: $repo_name})-[:CONTAINS*]->(t:TypeDefinition) DETACH DELETE t",
                "MATCH (r:Repository {name: $repo_name})-[:CONTAINS*]->(i:Interface) DETACH DELETE i",
                
                # 3. Fonctions et composants
                "MATCH (r:Repository {name: $repo_name})-[:CONTAINS*]->(func:Function) DETACH DELETE func",
                "MATCH (r:Repository {name: $repo_name})-[:CONTAINS*]->(comp:Component) DETACH DELETE comp",
                "MATCH (r:Repository {name: $repo_name})-[:CONTAINS*]->(c:Class) DETACH DELETE c",
                
                # 4. Fichiers
                "MATCH (r:Repository {name: $repo_name})-[:CONTAINS]->(f:File) DETACH DELETE f",
                
                # 5. Repository
                "MATCH (r:Repository {name: $repo_name}) DETACH DELETE r"
            ]
            
            for query in delete_queries:
                await session.run(query, repo_name=repo_name)
        
        logger.info(f"✅ Repository '{repo_name}' cleared")
    
    async def parse_repository(self, repo_url: str, repo_name: str = None, local_path: str = None):
        """Parser un repository avec hiérarchie propre"""
        
        if not repo_name:
            repo_name = repo_url.split('/')[-1].replace('.git', '')
        
        logger.info(f"📦 Parsing repository: {repo_name}")
        
        # Créer le noeud Repository
        await self._create_repository_node(repo_name, repo_url)
        
        # Déterminer le chemin à analyser
        if local_path:
            target_path = Path(local_path)
        else:
            # Clone logic here if needed
            target_path = Path(f"/tmp/{repo_name}")
        
        if not target_path.exists():
            logger.error(f"Path does not exist: {target_path}")
            return
        
        # Parser tous les fichiers
        await self._parse_directory(target_path, repo_name)
        
        logger.info(f"✅ Repository parsing complete: {repo_name}")
    
    async def _create_repository_node(self, repo_name: str, repo_url: str):
        """Créer le noeud Repository racine"""
        async with self.driver.session() as session:
            await session.run("""
                MERGE (r:Repository {name: $repo_name})
                SET r.url = $repo_url,
                    r.created_at = datetime(),
                    r.updated_at = datetime(),
                    r.hierarchy_version = "clean_v1"
                RETURN r
            """, repo_name=repo_name, repo_url=repo_url)
    
    async def _parse_directory(self, directory: Path, repo_name: str):
        """Parser récursivement un répertoire"""
        
        for file_path in directory.rglob("*"):
            if not file_path.is_file():
                continue
            
            # Filtrer les fichiers non pertinents
            if self._should_skip_file(file_path):
                continue
            
            try:
                await self._parse_file(file_path, repo_name)
            except Exception as e:
                logger.debug(f"Error parsing {file_path}: {e}")
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Déterminer si un fichier doit être ignoré"""
        
        skip_dirs = {'.git', 'node_modules', '__pycache__', '.next', 'dist', 'build'}
        skip_extensions = {'.pyc', '.pyo', '.log', '.tmp', '.cache'}
        
        # Vérifier les répertoires à ignorer
        for part in file_path.parts:
            if part in skip_dirs:
                return True
        
        # Vérifier les extensions à ignorer
        if file_path.suffix in skip_extensions:
            return True
        
        return False
    
    async def _parse_file(self, file_path: Path, repo_name: str):
        """Parser un fichier individuel avec hiérarchie claire"""
        
        # Créer l'ID unique du fichier  
        relative_path = str(file_path).replace(f"/Users/kwenji/mcp-crawl4ai-rag/", "")
        file_id = f"{repo_name}::{relative_path}"
        
        async with self.driver.session() as session:
            # Créer le noeud File
            await session.run("""
                MATCH (r:Repository {name: $repo_name})
                MERGE (f:File {file_id: $file_id})
                SET f.name = $name,
                    f.path = $path,
                    f.relative_path = $relative_path,
                    f.extension = $extension,
                    f.size = $size,
                    f.created_at = datetime()
                MERGE (r)-[:CONTAINS]->(f)
            """, 
            repo_name=repo_name,
            file_id=file_id,
            name=file_path.name,
            path=str(file_path),
            relative_path=relative_path,
            extension=file_path.suffix,
            size=file_path.stat().st_size if file_path.exists() else 0
            )
        
        # Parser selon le type de fichier
        if file_path.suffix in {'.ts', '.tsx', '.js', '.jsx'}:
            await self._parse_typescript_file(file_path, file_id, repo_name)
        elif file_path.suffix == '.py':
            await self._parse_python_file(file_path, file_id, repo_name)
    
    async def _parse_typescript_file(self, file_path: Path, file_id: str, repo_name: str):
        """Parser un fichier TypeScript/JavaScript avec hiérarchie"""
        
        try:
            analysis = self.ts_analyzer.analyze_typescript_file(
                file_path, file_path.parent, set()
            )
            
            if not analysis:
                return
            
            async with self.driver.session() as session:
                # === COMPOSANTS REACT ===
                for component in analysis.components:
                    await self._create_component_hierarchy(
                        session, component, file_id, repo_name
                    )
                
                # === CLASSES ===
                for class_info in analysis.classes:
                    await self._create_class_hierarchy(
                        session, class_info, file_id, repo_name
                    )
                
                # === FONCTIONS ===
                for function in analysis.functions:
                    await self._create_function_node(
                        session, function, file_id, repo_name
                    )
                
                # === INTERFACES ET TYPES ===
                for interface in analysis.interfaces:
                    await self._create_interface_node(
                        session, interface, file_id, repo_name
                    )
                
                for type_def in analysis.types:
                    await self._create_type_definition_node(
                        session, type_def, file_id, repo_name
                    )
        
        except Exception as e:
            logger.debug(f"Error analyzing TypeScript file {file_path}: {e}")
    
    async def _create_component_hierarchy(self, session, component, file_id: str, repo_name: str):
        """Créer la hiérarchie d'un composant React"""
        
        component_id = f"{file_id}::{component.name}"
        
        # Créer le composant
        await session.run("""
            MATCH (f:File {file_id: $file_id})
            MERGE (comp:Component {component_id: $component_id})
            SET comp.name = $name,
                comp.type = $type,
                comp.line_number = $line_number,
                comp.is_exported = $is_exported,
                comp.is_default_export = $is_default_export,
                comp.created_at = datetime()
            MERGE (f)-[:DEFINES]->(comp)
        """,
        file_id=file_id,
        component_id=component_id,
        name=component.name,
        type=component.type,
        line_number=component.line_number,
        is_exported=component.is_exported,
        is_default_export=component.is_default_export
        )
        
        # Créer les Props du composant
        if component.props:
            props_id = f"{component_id}::props"
            await session.run("""
                MATCH (comp:Component {component_id: $component_id})
                MERGE (props:Props {props_id: $props_id})
                SET props.properties = $properties,
                    props.count = $count
                MERGE (comp)-[:HAS_PROPS]->(props)
            """,
            component_id=component_id,
            props_id=props_id,
            properties=component.props,
            count=len(component.props)
            )
        
        # Créer les Hooks utilisés
        if component.hooks:
            for hook_name in component.hooks:
                hook_id = f"{component_id}::hook::{hook_name}"
                await session.run("""
                    MATCH (comp:Component {component_id: $component_id})
                    MERGE (hook:Hook {hook_id: $hook_id})
                    SET hook.name = $hook_name,
                        hook.is_custom = $is_custom
                    MERGE (comp)-[:USES_HOOK]->(hook)
                """,
                component_id=component_id,
                hook_id=hook_id,
                hook_name=hook_name,
                is_custom=hook_name.startswith('use') and not hook_name.startswith('useState')
                )
    
    async def _create_class_hierarchy(self, session, class_info, file_id: str, repo_name: str):
        """Créer la hiérarchie d'une classe"""
        
        class_id = f"{file_id}::{class_info.name}"
        
        # Créer la classe
        await session.run("""
            MATCH (f:File {file_id: $file_id})
            MERGE (c:Class {class_id: $class_id})
            SET c.name = $name,
                c.type = $type,
                c.line_number = $line_number,
                c.is_exported = $is_exported,
                c.extends = $extends,
                c.implements = $implements,
                c.created_at = datetime()
            MERGE (f)-[:DEFINES]->(c)
        """,
        file_id=file_id,
        class_id=class_id,
        name=class_info.name,
        type=class_info.type,
        line_number=getattr(class_info, 'line_number', 0),
        is_exported=getattr(class_info, 'is_exported', False),
        extends=getattr(class_info, 'extends', []),
        implements=getattr(class_info, 'implements', [])
        )
        
        # Créer les méthodes
        if hasattr(class_info, 'methods'):
            for method in class_info.methods:
                method_id = f"{class_id}::method::{method.name}"
                await session.run("""
                    MATCH (c:Class {class_id: $class_id})
                    MERGE (m:Method {method_id: $method_id})
                    SET m.name = $name,
                        m.visibility = $visibility,
                        m.is_static = $is_static,
                        m.is_async = $is_async,
                        m.line_number = $line_number,
                        m.parameters = $parameters,
                        m.return_type = $return_type
                    MERGE (c)-[:HAS_METHOD]->(m)
                """,
                class_id=class_id,
                method_id=method_id,
                name=method.name,
                visibility=getattr(method, 'visibility', 'public'),
                is_static=getattr(method, 'is_static', False),
                is_async=getattr(method, 'is_async', False),
                line_number=getattr(method, 'line_number', 0),
                parameters=getattr(method, 'parameters', []),
                return_type=getattr(method, 'return_type', 'void')
                )
        
        # Créer les attributs
        if hasattr(class_info, 'attributes'):
            for attr in class_info.attributes:
                attr_id = f"{class_id}::attr::{attr.name}"
                await session.run("""
                    MATCH (c:Class {class_id: $class_id})
                    MERGE (a:Attribute {attribute_id: $attr_id})
                    SET a.name = $name,
                        a.type = $type,
                        a.visibility = $visibility,
                        a.is_static = $is_static,
                        a.line_number = $line_number
                    MERGE (c)-[:HAS_ATTRIBUTE]->(a)
                """,
                class_id=class_id,
                attr_id=attr_id,
                name=attr.name,
                type=getattr(attr, 'type', 'any'),
                visibility=getattr(attr, 'visibility', 'public'),
                is_static=getattr(attr, 'is_static', False),
                line_number=getattr(attr, 'line_number', 0)
                )
    
    async def _create_function_node(self, session, function, file_id: str, repo_name: str):
        """Créer un noeud Function"""
        
        function_id = f"{file_id}::func::{function.name}"
        
        await session.run("""
            MATCH (f:File {file_id: $file_id})
            MERGE (func:Function {function_id: $function_id})
            SET func.name = $name,
                func.is_exported = $is_exported,
                func.is_async = $is_async,
                func.line_number = $line_number,
                func.parameters = $parameters,
                func.return_type = $return_type,
                func.created_at = datetime()
            MERGE (f)-[:DEFINES]->(func)
        """,
        file_id=file_id,
        function_id=function_id,
        name=function.name,
        is_exported=getattr(function, 'is_exported', False),
        is_async=getattr(function, 'is_async', False),
        line_number=getattr(function, 'line_number', 0),
        parameters=getattr(function, 'parameters', []),
        return_type=getattr(function, 'return_type', 'void')
        )
    
    async def _create_interface_node(self, session, interface, file_id: str, repo_name: str):
        """Créer un noeud Interface"""
        
        interface_id = f"{file_id}::interface::{interface.name}"
        
        await session.run("""
            MATCH (f:File {file_id: $file_id})
            MERGE (i:Interface {interface_id: $interface_id})
            SET i.name = $name,
                i.properties = $properties,
                i.extends = $extends,
                i.line_number = $line_number,
                i.is_exported = $is_exported,
                i.created_at = datetime()
            MERGE (f)-[:DEFINES]->(i)
        """,
        file_id=file_id,
        interface_id=interface_id,
        name=interface.name,
        properties=getattr(interface, 'properties', []),
        extends=getattr(interface, 'extends', []),
        line_number=getattr(interface, 'line_number', 0),
        is_exported=getattr(interface, 'is_exported', False)
        )
    
    async def _create_type_definition_node(self, session, type_def, file_id: str, repo_name: str):
        """Créer un noeud TypeDefinition"""
        
        type_id = f"{file_id}::type::{type_def.name}"
        
        await session.run("""
            MATCH (f:File {file_id: $file_id})
            MERGE (t:TypeDefinition {type_id: $type_id})
            SET t.name = $name,
                t.definition = $definition,
                t.kind = $kind,
                t.line_number = $line_number,
                t.is_exported = $is_exported,
                t.created_at = datetime()
            MERGE (f)-[:DEFINES]->(t)
        """,
        file_id=file_id,
        type_id=type_id,
        name=type_def.name,
        definition=getattr(type_def, 'definition', ''),
        kind=getattr(type_def, 'kind', 'type'),
        line_number=getattr(type_def, 'line_number', 0),
        is_exported=getattr(type_def, 'is_exported', False)
        )
    
    async def _parse_python_file(self, file_path: Path, file_id: str, repo_name: str):
        """Parser un fichier Python (basique)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parsing Python basique avec AST
            tree = ast.parse(content)
            
            async with self.driver.session() as session:
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        await self._create_python_class(session, node, file_id)
                    elif isinstance(node, ast.FunctionDef):
                        await self._create_python_function(session, node, file_id)
        
        except Exception as e:
            logger.debug(f"Error parsing Python file {file_path}: {e}")
    
    async def _create_python_class(self, session, class_node, file_id: str):
        """Créer une classe Python"""
        class_id = f"{file_id}::class::{class_node.name}"
        
        await session.run("""
            MATCH (f:File {file_id: $file_id})
            MERGE (c:Class {class_id: $class_id})
            SET c.name = $name,
                c.type = "python_class",
                c.line_number = $line_number,
                c.language = "python",
                c.created_at = datetime()
            MERGE (f)-[:DEFINES]->(c)
        """,
        file_id=file_id,
        class_id=class_id,
        name=class_node.name,
        line_number=class_node.lineno
        )
    
    async def _create_python_function(self, session, func_node, file_id: str):
        """Créer une fonction Python"""
        func_id = f"{file_id}::func::{func_node.name}"
        
        # Extraire les paramètres
        params = [arg.arg for arg in func_node.args.args]
        
        await session.run("""
            MATCH (f:File {file_id: $file_id})
            MERGE (func:Function {function_id: $func_id})
            SET func.name = $name,
                func.line_number = $line_number,
                func.language = "python",
                func.parameters = $parameters,
                func.is_async = $is_async,
                func.created_at = datetime()
            MERGE (f)-[:DEFINES]->(func)
        """,
        file_id=file_id,
        func_id=func_id,
        name=func_node.name,
        line_number=func_node.lineno,
        parameters=params,
        is_async=isinstance(func_node, ast.AsyncFunctionDef)
        )
    
    async def close(self):
        """Fermer la connexion Neo4j"""
        if self.driver:
            await self.driver.close()


# === FONCTION UTILITAIRE ===
async def clean_parse_repository(repo_url: str, repo_name: str = None, local_path: str = None):
    """Fonction utilitaire pour parser un repository avec hiérarchie propre"""
    
    parser = CleanHierarchyParser()
    
    try:
        await parser.initialize()
        
        # Effacer si le repository existe déjà
        if repo_name:
            await parser.clear_repository(repo_name)
        
        # Parser avec hiérarchie propre
        await parser.parse_repository(repo_url, repo_name, local_path)
        
        logger.info("✅ Clean repository parsing completed")
        
    except Exception as e:
        logger.error(f"❌ Error during clean parsing: {e}")
        raise
    finally:
        await parser.close()


if __name__ == "__main__":
    # Test avec le repository local
    asyncio.run(clean_parse_repository(
        repo_url="local",
        repo_name="mcp-crawl4ai-rag", 
        local_path="/Users/kwenji/mcp-crawl4ai-rag"
    ))