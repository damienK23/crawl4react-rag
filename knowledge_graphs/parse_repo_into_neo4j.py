"""
Direct Neo4j GitHub Code Repository Extractor

Creates nodes and relationships directly in Neo4j without Graphiti:
- File nodes
- Class nodes  
- Method nodes
- Function nodes
- Import relationships

Bypasses all LLM processing for maximum speed.
"""

import asyncio
import logging
import os
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
import ast

from dotenv import load_dotenv
from neo4j import AsyncGraphDatabase
from typescript_analyzer import TypeScriptAnalyzer
from supabase_analyzer import SupabaseAnalyzer, SupabaseSchemaInfo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)


class Neo4jCodeAnalyzer:
    """Analyzes code for direct Neo4j insertion"""
    
    def __init__(self):
        # Initialize TypeScript analyzer
        self.ts_analyzer = TypeScriptAnalyzer()
        
        # External modules to ignore for React/TypeScript ecosystem
        self.external_modules = {
            # React ecosystem
            'react', 'react-dom', 'react-router', 'react-router-dom', 'react-query',
            'react-hook-form', 'react-table', 'react-select', 'react-spring', 'framer-motion',
            
            # Next.js and meta-frameworks
            'next', 'gatsby', 'remix', '@remix-run', 'nuxt', 'vite', 'create-react-app',
            
            # State management
            'redux', '@reduxjs/toolkit', 'mobx', 'zustand', 'jotai', 'recoil', 'context',
            
            # UI libraries
            'antd', '@ant-design', 'material-ui', '@mui', 'chakra-ui', 'react-bootstrap',
            'semantic-ui-react', 'styled-components', '@emotion', 'tailwindcss',
            
            # Utilities
            'lodash', 'ramda', 'date-fns', 'moment', 'dayjs', 'uuid', 'classnames', 'clsx',
            
            # API and HTTP
            'axios', 'fetch', 'swr', 'apollo-client', '@apollo/client', 'graphql',
            'socket.io-client', 'ws',
            
            # TypeScript and build tools
            'typescript', '@types', 'webpack', 'rollup', 'parcel', 'babel', '@babel',
            'prettier', 'eslint', '@typescript-eslint', 'jest', '@testing-library',
            
            # Node.js standard libraries
            'fs', 'path', 'os', 'crypto', 'buffer', 'stream', 'events', 'util',
            'url', 'querystring', 'http', 'https', 'net', 'cluster', 'child_process',
            
            # Common Node.js packages
            'express', 'fastify', 'koa', 'helmet', 'cors', 'morgan', 'winston',
            'bcrypt', 'jsonwebtoken', 'passport', 'nodemailer', 'multer', 'sharp',
            'dotenv', 'config', 'yup', 'joi', 'zod', 'class-validator'
        }
    
    def analyze_typescript_file(self, file_path: Path, repo_root: Path, project_modules: Set[str]) -> Dict[str, Any]:
        """Extract React/TypeScript structure for direct Neo4j insertion"""
        try:
            # Use the TypeScript analyzer to parse the file
            analysis = self.ts_analyzer.analyze_typescript_file(file_path, repo_root, project_modules)
            if not analysis:
                return None
            
            relative_path = str(file_path.relative_to(repo_root))
            module_name = self._get_importable_module_name(file_path, repo_root, relative_path)
            
            # Convert TypeScript analysis to Neo4j format
            components = []
            functions = []
            imports = []
            
            # Process React components
            for component in analysis.components:
                component_data = {
                    'name': component.name,
                    'full_name': f"{module_name}.{component.name}",
                    'type': component.type,
                    'props': component.props,
                    'hooks': component.hooks,
                    'is_exported': component.is_exported
                }
                components.append(component_data)
            
            # Process function calls as functions
            for func_call in analysis.function_calls:
                if func_call.object_name:
                    # Method call
                    function_data = {
                        'name': func_call.function_name,
                        'full_name': f"{func_call.object_name}.{func_call.function_name}",
                        'args': func_call.args,
                        'object_name': func_call.object_name,
                        'type': 'method_call'
                    }
                else:
                    # Regular function call
                    function_data = {
                        'name': func_call.function_name,
                        'full_name': f"{module_name}.{func_call.function_name}",
                        'args': func_call.args,
                        'type': 'function_call'
                    }
                functions.append(function_data)
            
            # Process imports
            for import_info in analysis.imports:
                # Skip external modules
                if import_info.module not in self.external_modules:
                    imports.append({
                        'module': import_info.module,
                        'name': import_info.name,
                        'alias': import_info.alias,
                        'is_default': import_info.is_default_import,
                        'is_namespace': import_info.is_namespace_import
                    })
            
            return {
                'file_path': relative_path,
                'module_name': module_name,
                'components': components,
                'functions': functions,
                'imports': imports,
                'hook_calls': [
                    {
                        'name': hook.hook_name,
                        'args': hook.args,
                        'variable_name': hook.variable_name
                    }
                    for hook in analysis.hook_calls
                ],
                'exports': analysis.exports
            }
            
        except Exception as e:
            logger.error(f"Error analyzing TypeScript file {file_path}: {e}")
            return None
    
    def analyze_python_file(self, file_path: Path, repo_root: Path, project_modules: Set[str]) -> Dict[str, Any]:
        """Extract structure for direct Neo4j insertion"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            relative_path = str(file_path.relative_to(repo_root))
            module_name = self._get_importable_module_name(file_path, repo_root, relative_path)
            
            # Extract structure
            classes = []
            functions = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Extract class with its methods and attributes
                    methods = []
                    attributes = []
                    
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if not item.name.startswith('_'):  # Public methods only
                                # Extract comprehensive parameter info
                                params = self._extract_function_parameters(item)
                                
                                # Get return type annotation
                                return_type = self._get_name(item.returns) if item.returns else 'Any'
                                
                                # Create detailed parameter list for Neo4j storage
                                params_detailed = []
                                for p in params:
                                    param_str = f"{p['name']}:{p['type']}"
                                    if p['optional'] and p['default'] is not None:
                                        param_str += f"={p['default']}"
                                    elif p['optional']:
                                        param_str += "=None"
                                    if p['kind'] != 'positional':
                                        param_str = f"[{p['kind']}] {param_str}"
                                    params_detailed.append(param_str)
                                
                                methods.append({
                                    'name': item.name,
                                    'params': params,  # Full parameter objects
                                    'params_detailed': params_detailed,  # Detailed string format
                                    'return_type': return_type,
                                    'args': [arg.arg for arg in item.args.args if arg.arg != 'self']  # Keep for backwards compatibility
                                })
                        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            # Type annotated attributes
                            if not item.target.id.startswith('_'):
                                attributes.append({
                                    'name': item.target.id,
                                    'type': self._get_name(item.annotation) if item.annotation else 'Any'
                                })
                    
                    classes.append({
                        'name': node.name,
                        'full_name': f"{module_name}.{node.name}",
                        'methods': methods,
                        'attributes': attributes
                    })
                
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Only top-level functions
                    if not any(node in cls_node.body for cls_node in ast.walk(tree) if isinstance(cls_node, ast.ClassDef)):
                        if not node.name.startswith('_'):
                            # Extract comprehensive parameter info
                            params = self._extract_function_parameters(node)
                            
                            # Get return type annotation
                            return_type = self._get_name(node.returns) if node.returns else 'Any'
                            
                            # Create detailed parameter list for Neo4j storage
                            params_detailed = []
                            for p in params:
                                param_str = f"{p['name']}:{p['type']}"
                                if p['optional'] and p['default'] is not None:
                                    param_str += f"={p['default']}"
                                elif p['optional']:
                                    param_str += "=None"
                                if p['kind'] != 'positional':
                                    param_str = f"[{p['kind']}] {param_str}"
                                params_detailed.append(param_str)
                            
                            # Simple format for backwards compatibility
                            params_list = [f"{p['name']}:{p['type']}" for p in params]
                            
                            functions.append({
                                'name': node.name,
                                'full_name': f"{module_name}.{node.name}",
                                'params': params,  # Full parameter objects
                                'params_detailed': params_detailed,  # Detailed string format
                                'params_list': params_list,  # Simple string format for backwards compatibility
                                'return_type': return_type,
                                'args': [arg.arg for arg in node.args.args]  # Keep for backwards compatibility
                            })
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    # Track internal imports only
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if self._is_likely_internal(alias.name, project_modules):
                                imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        if (node.module.startswith('.') or self._is_likely_internal(node.module, project_modules)):
                            imports.append(node.module)
            
            return {
                'module_name': module_name,
                'file_path': relative_path,
                'classes': classes,
                'functions': functions,
                'imports': list(set(imports)),  # Remove duplicates
                'line_count': len(content.splitlines())
            }
            
        except Exception as e:
            logger.warning(f"Could not analyze {file_path}: {e}")
            return None
    
    def _is_likely_internal(self, import_name: str, project_modules: Set[str]) -> bool:
        """Check if an import is likely internal to the project"""
        if not import_name:
            return False
        
        # Relative imports are definitely internal
        if import_name.startswith('.'):
            return True
        
        # Check if it's a known external module
        base_module = import_name.split('.')[0]
        if base_module in self.external_modules:
            return False
        
        # Check if it matches any project module
        for project_module in project_modules:
            if import_name.startswith(project_module):
                return True
        
        # If it's not obviously external, consider it internal
        if (not any(ext in base_module.lower() for ext in ['test', 'mock', 'fake']) and
            not base_module.startswith('_') and
            len(base_module) > 2):
            return True
        
        return False
    
    def _get_importable_module_name(self, file_path: Path, repo_root: Path, relative_path: str) -> str:
        """Determine the actual importable module name for a Python file"""
        # Start with the default: convert file path to module path
        default_module = relative_path.replace('/', '.').replace('\\', '.').replace('.py', '')
        
        # Common patterns to detect the actual package root
        path_parts = Path(relative_path).parts
        
        # Look for common package indicators
        package_roots = []
        
        # Check each directory level for __init__.py to find package boundaries
        current_path = repo_root
        for i, part in enumerate(path_parts[:-1]):  # Exclude the .py file itself
            current_path = current_path / part
            if (current_path / '__init__.py').exists():
                # This is a package directory, mark it as a potential root
                package_roots.append(i)
        
        if package_roots:
            # Use the first (outermost) package as the root
            package_start = package_roots[0]
            module_parts = path_parts[package_start:]
            module_name = '.'.join(module_parts).replace('.py', '')
            return module_name
        
        # Fallback: look for common Python project structures
        # Skip common non-package directories
        skip_dirs = {'src', 'lib', 'source', 'python', 'pkg', 'packages'}
        
        # Find the first directory that's not in skip_dirs
        filtered_parts = []
        for part in path_parts:
            if part.lower() not in skip_dirs or filtered_parts:  # Once we start including, include everything
                filtered_parts.append(part)
        
        if filtered_parts:
            module_name = '.'.join(filtered_parts).replace('.py', '')
            return module_name
        
        # Final fallback: use the default
        return default_module
    
    def _extract_function_parameters(self, func_node):
        """Comprehensive parameter extraction from function definition"""
        params = []
        
        # Regular positional arguments
        for i, arg in enumerate(func_node.args.args):
            if arg.arg == 'self':
                continue
                
            param_info = {
                'name': arg.arg,
                'type': self._get_name(arg.annotation) if arg.annotation else 'Any',
                'kind': 'positional',
                'optional': False,
                'default': None
            }
            
            # Check if this argument has a default value
            defaults_start = len(func_node.args.args) - len(func_node.args.defaults)
            if i >= defaults_start:
                default_idx = i - defaults_start
                if default_idx < len(func_node.args.defaults):
                    param_info['optional'] = True
                    param_info['default'] = self._get_default_value(func_node.args.defaults[default_idx])
            
            params.append(param_info)
        
        # *args parameter
        if func_node.args.vararg:
            params.append({
                'name': f"*{func_node.args.vararg.arg}",
                'type': self._get_name(func_node.args.vararg.annotation) if func_node.args.vararg.annotation else 'Any',
                'kind': 'var_positional',
                'optional': True,
                'default': None
            })
        
        # Keyword-only arguments (after *)
        for i, arg in enumerate(func_node.args.kwonlyargs):
            param_info = {
                'name': arg.arg,
                'type': self._get_name(arg.annotation) if arg.annotation else 'Any',
                'kind': 'keyword_only',
                'optional': True,  # All kwonly args are optional unless explicitly required
                'default': None
            }
            
            # Check for default value
            if i < len(func_node.args.kw_defaults) and func_node.args.kw_defaults[i] is not None:
                param_info['default'] = self._get_default_value(func_node.args.kw_defaults[i])
            else:
                param_info['optional'] = False  # No default = required kwonly arg
            
            params.append(param_info)
        
        # **kwargs parameter
        if func_node.args.kwarg:
            params.append({
                'name': f"**{func_node.args.kwarg.arg}",
                'type': self._get_name(func_node.args.kwarg.annotation) if func_node.args.kwarg.annotation else 'Dict[str, Any]',
                'kind': 'var_keyword',
                'optional': True,
                'default': None
            })
        
        return params
    
    def _get_default_value(self, default_node):
        """Extract default value from AST node"""
        try:
            if isinstance(default_node, ast.Constant):
                return repr(default_node.value)
            elif isinstance(default_node, ast.Name):
                return default_node.id
            elif isinstance(default_node, ast.Attribute):
                return self._get_name(default_node)
            elif isinstance(default_node, ast.List):
                return "[]"
            elif isinstance(default_node, ast.Dict):
                return "{}"
            else:
                return "..."
        except Exception:
            return "..."
    
    def _get_name(self, node):
        """Extract name from AST node, handling complex types safely"""
        if node is None:
            return "Any"
        
        try:
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                if hasattr(node, 'value'):
                    return f"{self._get_name(node.value)}.{node.attr}"
                else:
                    return node.attr
            elif isinstance(node, ast.Subscript):
                # Handle List[Type], Dict[K,V], etc.
                base = self._get_name(node.value)
                if hasattr(node, 'slice'):
                    if isinstance(node.slice, ast.Name):
                        return f"{base}[{node.slice.id}]"
                    elif isinstance(node.slice, ast.Tuple):
                        elts = [self._get_name(elt) for elt in node.slice.elts]
                        return f"{base}[{', '.join(elts)}]"
                    elif isinstance(node.slice, ast.Constant):
                        return f"{base}[{repr(node.slice.value)}]"
                    elif isinstance(node.slice, ast.Attribute):
                        return f"{base}[{self._get_name(node.slice)}]"
                    elif isinstance(node.slice, ast.Subscript):
                        return f"{base}[{self._get_name(node.slice)}]"
                    else:
                        # Try to get the name of the slice, fallback to Any if it fails
                        try:
                            slice_name = self._get_name(node.slice)
                            return f"{base}[{slice_name}]"
                        except:
                            return f"{base}[Any]"
                return base
            elif isinstance(node, ast.Constant):
                return str(node.value)
            elif isinstance(node, ast.Str):  # Python < 3.8
                return f'"{node.s}"'
            elif isinstance(node, ast.Tuple):
                elts = [self._get_name(elt) for elt in node.elts]
                return f"({', '.join(elts)})"
            elif isinstance(node, ast.List):
                elts = [self._get_name(elt) for elt in node.elts]
                return f"[{', '.join(elts)}]"
            else:
                # Fallback for complex types - return a simple string representation
                return "Any"
        except Exception:
            # If anything goes wrong, return a safe default
            return "Any"


class DirectNeo4jExtractor:
    """Creates nodes and relationships directly in Neo4j"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.driver = None
        self.analyzer = Neo4jCodeAnalyzer()
        self.supabase_analyzer = None
    
    async def initialize(self):
        """Initialize Neo4j connection"""
        logger.info("Initializing Neo4j connection...")
        self.driver = AsyncGraphDatabase.driver(
            self.neo4j_uri, 
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
        # Clear existing data
        # logger.info("Clearing existing data...")
        # async with self.driver.session() as session:
        #     await session.run("MATCH (n) DETACH DELETE n")
        
        # Create constraints and indexes
        logger.info("Creating constraints and indexes...")
        async with self.driver.session() as session:
            # Create constraints - using MERGE-friendly approach
            await session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE")
            await session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Class) REQUIRE c.full_name IS UNIQUE")
            # Add constraints for React/TypeScript components
            await session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (comp:Component) REQUIRE comp.comp_id IS UNIQUE")
            await session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (hook:Hook) REQUIRE hook.hook_id IS UNIQUE")
            # Remove unique constraints for methods/attributes since they can be duplicated across classes
            # await session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (m:Method) REQUIRE m.full_name IS UNIQUE")
            # await session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (f:Function) REQUIRE f.full_name IS UNIQUE")
            # await session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Attribute) REQUIRE a.full_name IS UNIQUE")
            
            # Create indexes for performance
            await session.run("CREATE INDEX IF NOT EXISTS FOR (f:File) ON (f.name)")
            await session.run("CREATE INDEX IF NOT EXISTS FOR (c:Class) ON (c.name)")
            await session.run("CREATE INDEX IF NOT EXISTS FOR (m:Method) ON (m.name)")
            # Add indexes for React/TypeScript components
            await session.run("CREATE INDEX IF NOT EXISTS FOR (comp:Component) ON (comp.name)")
            await session.run("CREATE INDEX IF NOT EXISTS FOR (hook:Hook) ON (hook.name)")
            
            # Add constraints and indexes for Supabase schema
            await session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (t:SupabaseTable) REQUIRE t.table_id IS UNIQUE")
            await session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (f:SupabaseFunction) REQUIRE f.function_id IS UNIQUE")
            await session.run("CREATE INDEX IF NOT EXISTS FOR (t:SupabaseTable) ON (t.name)")
            await session.run("CREATE INDEX IF NOT EXISTS FOR (c:SupabaseColumn) ON (c.name)")
            await session.run("CREATE INDEX IF NOT EXISTS FOR (f:SupabaseFunction) ON (f.name)")
        
        logger.info("Neo4j initialized successfully")
    
    async def clear_repository_data(self, repo_name: str):
        """Clear all data for a specific repository"""
        logger.info(f"Clearing existing data for repository: {repo_name}")
        async with self.driver.session() as session:
            # Delete in specific order to avoid constraint issues
            
            # 1. Delete methods and attributes (they depend on classes)
            await session.run("""
                MATCH (r:Repository {name: $repo_name})-[:CONTAINS]->(f:File)-[:DEFINES]->(c:Class)-[:HAS_METHOD]->(m:Method)
                DETACH DELETE m
            """, repo_name=repo_name)
            
            await session.run("""
                MATCH (r:Repository {name: $repo_name})-[:CONTAINS]->(f:File)-[:DEFINES]->(c:Class)-[:HAS_ATTRIBUTE]->(a:Attribute)
                DETACH DELETE a
            """, repo_name=repo_name)
            
            # 2. Delete React/TypeScript components and hooks
            await session.run("""
                MATCH (r:Repository {name: $repo_name})-[:CONTAINS]->(f:File)-[:DEFINES]->(comp:Component)
                DETACH DELETE comp
            """, repo_name=repo_name)
            
            await session.run("""
                MATCH (r:Repository {name: $repo_name})-[:CONTAINS]->(f:File)-[:USES]->(hook:Hook)
                DETACH DELETE hook
            """, repo_name=repo_name)
            
            # 3. Delete functions (they depend on files)
            await session.run("""
                MATCH (r:Repository {name: $repo_name})-[:CONTAINS]->(f:File)-[:DEFINES]->(func:Function)
                DETACH DELETE func
            """, repo_name=repo_name)
            
            # 4. Delete classes (they depend on files)
            await session.run("""
                MATCH (r:Repository {name: $repo_name})-[:CONTAINS]->(f:File)-[:DEFINES]->(c:Class)
                DETACH DELETE c
            """, repo_name=repo_name)
            
            # 5. Delete files (they depend on repository)
            await session.run("""
                MATCH (r:Repository {name: $repo_name})-[:CONTAINS]->(f:File)
                DETACH DELETE f
            """, repo_name=repo_name)
            
            # 6. Finally delete the repository
            await session.run("""
                MATCH (r:Repository {name: $repo_name})
                DETACH DELETE r
            """, repo_name=repo_name)
            
        logger.info(f"Cleared data for repository: {repo_name}")
    
    async def close(self):
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()
    
    async def analyze_supabase_schema(self, supabase_url: str, supabase_key: str, project_name: str = None) -> bool:
        """Analyze Supabase schema and store in Neo4j"""
        try:
            logger.info("Analyzing Supabase schema...")
            
            # Initialize Supabase analyzer
            self.supabase_analyzer = SupabaseAnalyzer(supabase_url, supabase_key)
            
            if not self.supabase_analyzer.connect():
                logger.error("Failed to connect to Supabase")
                return False
            
            # Analyze schema
            schema_info = await self.supabase_analyzer.analyze_schema()
            
            # Store in Neo4j
            await self._store_supabase_schema(schema_info, project_name or "supabase_project")
            
            logger.info(f"Successfully analyzed Supabase schema: {len(schema_info.tables)} tables, {len(schema_info.functions)} functions")
            return True
            
        except Exception as e:
            logger.error(f"Error analyzing Supabase schema: {e}")
            return False
    
    async def _store_supabase_schema(self, schema_info: SupabaseSchemaInfo, project_name: str):
        """Store Supabase schema information in Neo4j"""
        async with self.driver.session() as session:
            # Create project node
            await session.run("""
                MERGE (p:SupabaseProject {name: $project_name})
                SET p.url = $url,
                    p.analyzed_at = datetime(),
                    p.table_count = $table_count,
                    p.function_count = $function_count
            """, project_name=project_name, url=schema_info.project_url,
                table_count=len(schema_info.tables), function_count=len(schema_info.functions))
            
            # Store tables
            for table in schema_info.tables:
                await self._store_supabase_table(session, table, project_name)
            
            # Store functions
            for function in schema_info.functions:
                await self._store_supabase_function(session, function, project_name)
            
            # Store enums
            for enum in schema_info.enums:
                await self._store_supabase_enum(session, enum, project_name)
    
    async def _store_supabase_table(self, session, table_info, project_name: str):
        """Store a Supabase table in Neo4j"""
        table_id = f"{project_name}_{table_info.schema}_{table_info.name}"
        
        # Create table node
        await session.run("""
            MATCH (p:SupabaseProject {name: $project_name})
            MERGE (t:SupabaseTable {table_id: $table_id})
            SET t.name = $name,
                t.schema = $schema,
                t.rls_enabled = $rls_enabled,
                t.estimated_rows = $estimated_rows,
                t.primary_keys = $primary_keys
            MERGE (p)-[:CONTAINS_TABLE]->(t)
        """, project_name=project_name, table_id=table_id, name=table_info.name,
            schema=table_info.schema, rls_enabled=table_info.rls_enabled,
            estimated_rows=table_info.estimated_rows, primary_keys=table_info.primary_keys)
        
        # Store columns
        for column in table_info.columns:
            await self._store_supabase_column(session, column, table_id)
        
        # Store foreign key relationships
        for fk in table_info.foreign_keys:
            await self._store_foreign_key_relationship(session, fk, table_id, project_name)
        
        # Store RLS policies
        for policy in table_info.policies:
            await self._store_rls_policy(session, policy, table_id)
    
    async def _store_supabase_column(self, session, column_info, table_id: str):
        """Store a Supabase column in Neo4j"""
        column_id = f"{table_id}_{column_info.name}"
        
        await session.run("""
            MATCH (t:SupabaseTable {table_id: $table_id})
            MERGE (c:SupabaseColumn {column_id: $column_id})
            SET c.name = $name,
                c.data_type = $data_type,
                c.is_nullable = $is_nullable,
                c.default_value = $default_value,
                c.is_primary_key = $is_primary_key,
                c.is_foreign_key = $is_foreign_key,
                c.max_length = $max_length,
                c.constraints = $constraints
            MERGE (t)-[:HAS_COLUMN]->(c)
        """, table_id=table_id, column_id=column_id, name=column_info.name,
            data_type=column_info.data_type, is_nullable=column_info.is_nullable,
            default_value=column_info.default_value, is_primary_key=column_info.is_primary_key,
            is_foreign_key=column_info.is_foreign_key, max_length=column_info.max_length,
            constraints=column_info.constraints)
    
    async def _store_foreign_key_relationship(self, session, fk_info, table_id: str, project_name: str):
        """Store foreign key relationships in Neo4j"""
        foreign_table_id = f"{project_name}_{fk_info['foreign_table_schema']}_{fk_info['foreign_table_name']}"
        
        await session.run("""
            MATCH (source_table:SupabaseTable {table_id: $source_table_id})
            MATCH (target_table:SupabaseTable {table_id: $target_table_id})
            MERGE (source_table)-[r:REFERENCES]->(target_table)
            SET r.source_column = $source_column,
                r.target_column = $target_column,
                r.constraint_name = $constraint_name
        """, source_table_id=table_id, target_table_id=foreign_table_id,
            source_column=fk_info['column_name'], target_column=fk_info['foreign_column_name'],
            constraint_name=fk_info['constraint_name'])
    
    async def _store_rls_policy(self, session, policy_info, table_id: str):
        """Store RLS policies in Neo4j"""
        policy_id = f"{table_id}_{policy_info['name']}"
        
        await session.run("""
            MATCH (t:SupabaseTable {table_id: $table_id})
            MERGE (p:RLSPolicy {policy_id: $policy_id})
            SET p.name = $name,
                p.permissive = $permissive,
                p.roles = $roles,
                p.command = $command,
                p.qualifier = $qualifier,
                p.with_check = $with_check
            MERGE (t)-[:HAS_POLICY]->(p)
        """, table_id=table_id, policy_id=policy_id, name=policy_info['name'],
            permissive=policy_info['permissive'], roles=policy_info['roles'],
            command=policy_info['command'], qualifier=policy_info['qualifier'],
            with_check=policy_info['with_check'])
    
    async def _store_supabase_function(self, session, function_info, project_name: str):
        """Store a Supabase function in Neo4j"""
        function_id = f"{project_name}_{function_info.schema}_{function_info.name}"
        
        await session.run("""
            MATCH (p:SupabaseProject {name: $project_name})
            MERGE (f:SupabaseFunction {function_id: $function_id})
            SET f.name = $name,
                f.schema = $schema,
                f.return_type = $return_type,
                f.language = $language,
                f.security_definer = $security_definer,
                f.description = $description,
                f.parameters = $parameters
            MERGE (p)-[:CONTAINS_FUNCTION]->(f)
        """, project_name=project_name, function_id=function_id, name=function_info.name,
            schema=function_info.schema, return_type=function_info.return_type,
            language=function_info.language, security_definer=function_info.security_definer,
            description=function_info.description, parameters=[
                {
                    'name': param.get('name'),
                    'type': param.get('type'),
                    'mode': param.get('mode'),
                    'position': param.get('position')
                } for param in function_info.parameters
            ])
    
    async def _store_supabase_enum(self, session, enum_info, project_name: str):
        """Store a Supabase enum in Neo4j"""
        enum_id = f"{project_name}_{enum_info['name']}"
        
        await session.run("""
            MATCH (p:SupabaseProject {name: $project_name})
            MERGE (e:SupabaseEnum {enum_id: $enum_id})
            SET e.name = $name,
                e.values = $values
            MERGE (p)-[:CONTAINS_ENUM]->(e)
        """, project_name=project_name, enum_id=enum_id, 
            name=enum_info['name'], values=enum_info['values'])
    
    def clone_repo(self, repo_url: str, target_dir: str) -> str:
        """Clone repository with shallow clone"""
        logger.info(f"Cloning repository to: {target_dir}")
        if os.path.exists(target_dir):
            logger.info(f"Removing existing directory: {target_dir}")
            try:
                def handle_remove_readonly(func, path, exc):
                    try:
                        if os.path.exists(path):
                            os.chmod(path, 0o777)
                            func(path)
                    except PermissionError:
                        logger.warning(f"Could not remove {path} - file in use, skipping")
                        pass
                shutil.rmtree(target_dir, onerror=handle_remove_readonly)
            except Exception as e:
                logger.warning(f"Could not fully remove {target_dir}: {e}. Proceeding anyway...")
        
        logger.info(f"Running git clone from {repo_url}")
        subprocess.run(['git', 'clone', '--depth', '1', repo_url, target_dir], check=True)
        logger.info("Repository cloned successfully")
        return target_dir
    
    def get_python_files(self, repo_path: str) -> List[Path]:
        """Get Python files, focusing only on src/ directory for local repositories"""
        source_files = []
        
        # For local analysis, focus only on src/ directory
        src_path = Path(repo_path) / 'src'
        if not src_path.exists():
            logger.warning(f"No src/ directory found in {repo_path}")
            return source_files
        
        # Only process files in src/ and its subdirectories
        for root, dirs, files in os.walk(str(src_path)):
            # Skip hidden directories and common non-source dirs within src/
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'__pycache__', 'test', 'tests'}]
            
            for file in files:
                if (file.endswith('.py') and 
                    not file.startswith('test') and 
                    not file.endswith(('_test.py', '_tests.py', 'test_.py'))):
                    file_path = Path(root) / file
                    if file_path.stat().st_size < 500_000:
                        source_files.append(file_path)
        
        return source_files
    
    def get_react_typescript_files(self, repo_path: str) -> List[Path]:
        """Get React/TypeScript files, focusing only on src/ directory for local repositories"""
        source_files = []
        
        # For local analysis, focus only on src/ directory
        src_path = Path(repo_path) / 'src'
        if not src_path.exists():
            logger.warning(f"No src/ directory found in {repo_path}")
            return source_files
        
        # Only process files in src/ and its subdirectories
        for root, dirs, files in os.walk(str(src_path)):
            # Skip hidden directories and common non-source dirs within src/
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'__pycache__', 'test', 'tests', '__tests__'}]
            
            for file in files:
                if (file.endswith(('.ts', '.tsx', '.js', '.jsx')) and 
                    not file.startswith('test') and 
                    not file.endswith(('.test.ts', '.test.tsx', '.test.js', '.test.jsx', 
                                     '.spec.ts', '.spec.tsx', '.spec.js', '.spec.jsx'))):
                    file_path = Path(root) / file
                    if (file_path.stat().st_size < 500_000 and 
                        file not in ['webpack.config.js', 'vite.config.ts', 'next.config.js',
                                   'tailwind.config.js', 'jest.config.js', 'babel.config.js']):
                        source_files.append(file_path)
        
        return source_files
    
    async def analyze_repository(self, repo_url: str, temp_dir: str = None):
        """Analyze repository and create nodes/relationships in Neo4j"""
        # Safely extract repo name, handling both strings and potential tuples
        if isinstance(repo_url, str):
            repo_name = repo_url.split('/')[-1].replace('.git', '')
        else:
            # If repo_url is somehow not a string, convert it first
            repo_name = str(repo_url).split('/')[-1].replace('.git', '')
        logger.info(f"Analyzing repository: {repo_name}")
        
        # Clear existing data for this repository before re-processing
        await self.clear_repository_data(repo_name)
        
        # Set default temp_dir to repos folder at script level
        if temp_dir is None:
            script_dir = Path(__file__).parent
            temp_dir = str(script_dir / "repos" / repo_name)
        
        # Clone and analyze
        repo_path = Path(self.clone_repo(repo_url, temp_dir))
        
        try:
            logger.info("Getting React/TypeScript files...")
            source_files = self.get_react_typescript_files(str(repo_path))
            logger.info(f"Found {len(source_files)} React/TypeScript files to analyze")
            
            # Also get Python files for mixed projects
            python_files = self.get_python_files(str(repo_path))
            logger.info(f"Found {len(python_files)} Python files to analyze")
            
            # First pass: identify project modules
            logger.info("Identifying project modules...")
            project_modules = set()
            for file_path in source_files:
                relative_path = str(file_path.relative_to(repo_path))
                module_parts = relative_path.replace('/', '.')
                # Remove file extensions one by one
                for ext in ['.ts', '.tsx', '.js', '.jsx']:
                    module_parts = module_parts.replace(ext, '')
                module_parts = module_parts.split('.')
                if len(module_parts) > 0 and not module_parts[0].startswith('.'):
                    project_modules.add(module_parts[0])
            
            logger.info(f"Identified project modules: {sorted(project_modules)}")
            
            # Second pass: analyze files and collect data
            logger.info("Analyzing React/TypeScript files...")
            modules_data = []
            for i, file_path in enumerate(source_files):
                if i % 20 == 0:
                    logger.info(f"Analyzing file {i+1}/{len(source_files)}: {file_path.name}")
                
                analysis = self.analyzer.analyze_typescript_file(file_path, repo_path, project_modules)
                if analysis:
                    modules_data.append(analysis)
            
            # Analyze Python files too
            logger.info("Analyzing Python files...")
            for i, file_path in enumerate(python_files):
                if i % 20 == 0:
                    logger.info(f"Analyzing Python file {i+1}/{len(python_files)}: {file_path.name}")
                
                analysis = self.analyzer.analyze_python_file(file_path, repo_path, project_modules)
                if analysis:
                    modules_data.append(analysis)
            
            logger.info(f"Found {len(modules_data)} files with content")
            
            # Create nodes and relationships in Neo4j
            logger.info("Creating nodes and relationships in Neo4j...")
            await self._create_graph(repo_name, modules_data)
            
            # Print summary
            total_classes = sum(len(mod['classes']) for mod in modules_data)
            total_methods = sum(len(cls['methods']) for mod in modules_data for cls in mod['classes'])
            total_functions = sum(len(mod['functions']) for mod in modules_data)
            total_imports = sum(len(mod['imports']) for mod in modules_data)
            
            print(f"\\n=== Direct Neo4j Repository Analysis for {repo_name} ===")
            print(f"Files processed: {len(modules_data)}")
            print(f"Classes created: {total_classes}")
            print(f"Methods created: {total_methods}")
            print(f"Functions created: {total_functions}")
            print(f"Import relationships: {total_imports}")
            
            logger.info(f"Successfully created Neo4j graph for {repo_name}")
            
        finally:
            if os.path.exists(temp_dir):
                logger.info(f"Cleaning up temporary directory: {temp_dir}")
                try:
                    def handle_remove_readonly(func, path, exc):
                        try:
                            if os.path.exists(path):
                                os.chmod(path, 0o777)
                                func(path)
                        except PermissionError:
                            logger.warning(f"Could not remove {path} - file in use, skipping")
                            pass
                    
                    shutil.rmtree(temp_dir, onerror=handle_remove_readonly)
                    logger.info("Cleanup completed")
                except Exception as e:
                    logger.warning(f"Cleanup failed: {e}. Directory may remain at {temp_dir}")
                    # Don't fail the whole process due to cleanup issues
    
    async def _create_graph(self, repo_name: str, modules_data: List[Dict]):
        """Create all nodes and relationships in Neo4j with proper error handling"""
        
        async with self.driver.session() as session:
            try:
                # Create Repository node
                await session.run(
                    "CREATE (r:Repository {name: $repo_name, created_at: datetime()})",
                    repo_name=repo_name
                )
                logger.info(f"Created Repository node for {repo_name}")
                
                nodes_created = 0
                relationships_created = 0
                
                for i, mod in enumerate(modules_data):
                    try:
                        # 1. Create File node
                        await session.run("""
                            CREATE (f:File {
                                name: $name,
                                path: $path,
                                module_name: $module_name,
                                line_count: $line_count,
                                created_at: datetime()
                            })
                        """, 
                            name=str(mod['file_path']).split('/')[-1],
                            path=mod['file_path'],
                            module_name=mod['module_name'],
                            line_count=mod.get('line_count', 0)
                        )
                        nodes_created += 1
                        
                        # 2. Connect File to Repository
                        await session.run("""
                            MATCH (r:Repository {name: $repo_name})
                            MATCH (f:File {path: $file_path})
                            CREATE (r)-[:CONTAINS]->(f)
                        """, repo_name=repo_name, file_path=mod['file_path'])
                        relationships_created += 1
                        
                        # 3. Create Class nodes and relationships
                        for cls in mod.get('classes', []):
                            # Create Class node
                            await session.run("""
                                MERGE (c:Class {full_name: $full_name})
                                ON CREATE SET c.name = $name, c.created_at = datetime()
                            """, name=cls['name'], full_name=cls['full_name'])
                            nodes_created += 1
                            
                            # Connect File to Class
                            await session.run("""
                                MATCH (f:File {path: $file_path})
                                MATCH (c:Class {full_name: $class_full_name})
                                MERGE (f)-[:DEFINES]->(c)
                            """, file_path=mod['file_path'], class_full_name=cls['full_name'])
                            relationships_created += 1
                            
                            # Create Method nodes with enhanced parameters
                            for method in cls.get('methods', []):
                                method_id = f"{cls['full_name']}::{method['name']}"
                                await session.run("""
                                    MERGE (m:Method {method_id: $method_id})
                                    ON CREATE SET m.name = $name, 
                                                 m.full_name = $full_name,
                                                 m.args = $args,
                                                 m.params_list = $params_list,
                                                 m.params_detailed = $params_detailed,
                                                 m.return_type = $return_type,
                                                 m.created_at = datetime()
                                """, 
                                    name=method['name'], 
                                    full_name=f"{cls['full_name']}.{method['name']}",
                                    method_id=method_id,
                                    args=method.get('args', []),
                                    params_list=method.get('params_list', []),
                                    params_detailed=method.get('params_detailed', []),
                                    return_type=method.get('return_type', 'Any')
                                )
                                nodes_created += 1
                                
                                # Connect Class to Method
                                await session.run("""
                                    MATCH (c:Class {full_name: $class_full_name})
                                    MATCH (m:Method {method_id: $method_id})
                                    MERGE (c)-[:HAS_METHOD]->(m)
                                """, 
                                    class_full_name=cls['full_name'], 
                                    method_id=method_id
                                )
                                relationships_created += 1
                            
                            # Create Attribute nodes for Python classes
                            for attr in cls.get('attributes', []):
                                attr_id = f"{cls['full_name']}::{attr['name']}"
                                await session.run("""
                                    MERGE (a:Attribute {attr_id: $attr_id})
                                    ON CREATE SET a.name = $name,
                                                 a.full_name = $full_name,
                                                 a.type = $type,
                                                 a.created_at = datetime()
                                """,
                                    name=attr['name'],
                                    full_name=f"{cls['full_name']}.{attr['name']}",
                                    attr_id=attr_id,
                                    type=attr.get('type', 'Any')
                                )
                                nodes_created += 1
                                
                                # Connect Class to Attribute
                                await session.run("""
                                    MATCH (c:Class {full_name: $class_full_name})
                                    MATCH (a:Attribute {attr_id: $attr_id})
                                    MERGE (c)-[:HAS_ATTRIBUTE]->(a)
                                """,
                                    class_full_name=cls['full_name'],
                                    attr_id=attr_id
                                )
                                relationships_created += 1
                        
                        # 4. Create Function nodes with enhanced parameters
                        for func in mod.get('functions', []):
                            func_id = f"{mod['file_path']}::{func['name']}"
                            await session.run("""
                                MERGE (f:Function {func_id: $func_id})
                                ON CREATE SET f.name = $name,
                                             f.full_name = $full_name,
                                             f.args = $args,
                                             f.params_list = $params_list,
                                             f.params_detailed = $params_detailed,
                                             f.return_type = $return_type,
                                             f.created_at = datetime()
                            """, 
                                name=func['name'], 
                                full_name=func['full_name'],
                                func_id=func_id,
                                args=func.get('args', []),
                                params_list=func.get('params_list', []),
                                params_detailed=func.get('params_detailed', []),
                                return_type=func.get('return_type', 'Any')
                            )
                            nodes_created += 1
                            
                            # Connect File to Function
                            await session.run("""
                                MATCH (file:File {path: $file_path})
                                MATCH (func:Function {func_id: $func_id})
                                MERGE (file)-[:DEFINES]->(func)
                            """, file_path=mod['file_path'], func_id=func_id)
                            relationships_created += 1
                        
                        # 5. Create React Component nodes (for TypeScript/JavaScript files)
                        for comp in mod.get('components', []):
                            comp_id = f"{mod['file_path']}::{comp['name']}"
                            await session.run("""
                                MERGE (c:Component {comp_id: $comp_id})
                                ON CREATE SET c.name = $name,
                                             c.full_name = $full_name,
                                             c.type = $type,
                                             c.props = $props,
                                             c.hooks = $hooks,
                                             c.is_exported = $is_exported,
                                             c.created_at = datetime()
                            """,
                                name=comp['name'],
                                full_name=comp['full_name'],
                                comp_id=comp_id,
                                type=comp.get('type', 'function'),
                                props=comp.get('props', []),
                                hooks=comp.get('hooks', []),
                                is_exported=comp.get('is_exported', False)
                            )
                            nodes_created += 1
                            
                            # Connect File to Component
                            await session.run("""
                                MATCH (file:File {path: $file_path})
                                MATCH (comp:Component {comp_id: $comp_id})
                                MERGE (file)-[:DEFINES]->(comp)
                            """, file_path=mod['file_path'], comp_id=comp_id)
                            relationships_created += 1
                        
                        # 6. Create Hook usage nodes (for TypeScript/JavaScript files)
                        for hook in mod.get('hook_calls', []):
                            hook_id = f"{mod['file_path']}::{hook['name']}::{hash(str(hook))}"
                            await session.run("""
                                MERGE (h:Hook {hook_id: $hook_id})
                                ON CREATE SET h.name = $name,
                                             h.args = $args,
                                             h.variable_name = $variable_name,
                                             h.created_at = datetime()
                            """,
                                name=hook['name'],
                                hook_id=hook_id,
                                args=hook.get('args', []),
                                variable_name=hook.get('variable_name')
                            )
                            nodes_created += 1
                            
                            # Connect File to Hook
                            await session.run("""
                                MATCH (file:File {path: $file_path})
                                MATCH (hook:Hook {hook_id: $hook_id})
                                MERGE (file)-[:USES]->(hook)
                            """, file_path=mod['file_path'], hook_id=hook_id)
                            relationships_created += 1
                        
                        if (i + 1) % 10 == 0:
                            logger.info(f"Processed {i + 1}/{len(modules_data)} files...")
                    
                    except Exception as e:
                        logger.error(f"Failed to process file {mod.get('file_path', 'unknown')}: {e}")
                        continue
                
                logger.info(f"Created {nodes_created} nodes and {relationships_created} relationships")
            
            except Exception as e:
                logger.error(f"Failed to create graph for {repo_name}: {e}")
                raise
    
    async def search_graph(self, query_type: str, **kwargs):
        """Search the Neo4j graph directly"""
        async with self.driver.session() as session:
            if query_type == "files_importing":
                target = kwargs.get('target')
                result = await session.run("""
                    MATCH (source:File)-[:IMPORTS]->(target:File)
                    WHERE target.module_name CONTAINS $target
                    RETURN source.path as file, target.module_name as imports
                """, target=target)
                return [{"file": record["file"], "imports": record["imports"]} async for record in result]
            
            elif query_type == "classes_in_file":
                file_path = kwargs.get('file_path')
                result = await session.run("""
                    MATCH (f:File {path: $file_path})-[:DEFINES]->(c:Class)
                    RETURN c.name as class_name, c.full_name as full_name
                """, file_path=file_path)
                return [{"class_name": record["class_name"], "full_name": record["full_name"]} async for record in result]
            
            elif query_type == "methods_of_class":
                class_name = kwargs.get('class_name')
                result = await session.run("""
                    MATCH (c:Class)-[:HAS_METHOD]->(m:Method)
                    WHERE c.name CONTAINS $class_name OR c.full_name CONTAINS $class_name
                    RETURN m.name as method_name, m.args as args
                """, class_name=class_name)
                return [{"method_name": record["method_name"], "args": record["args"]} async for record in result]


async def main():
    """Example usage"""
    load_dotenv()
    
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')
    
    extractor = DirectNeo4jExtractor(neo4j_uri, neo4j_user, neo4j_password)
    
    try:
        await extractor.initialize()
        
        # Analyze repository - direct Neo4j, no LLM processing!
        # repo_url = "https://github.com/pydantic/pydantic-ai.git"
        repo_url = "https://github.com/getzep/graphiti.git"
        await extractor.analyze_repository(repo_url)
        
        # Direct graph queries
        print("\\n=== Direct Neo4j Queries ===")
        
        # Which files import from models?
        results = await extractor.search_graph("files_importing", target="models")
        print(f"\\nFiles importing from 'models': {len(results)}")
        for result in results[:3]:
            print(f"- {result['file']} imports {result['imports']}")
        
        # What classes are in a specific file?
        results = await extractor.search_graph("classes_in_file", file_path="pydantic_ai/models/openai.py")
        print(f"\\nClasses in openai.py: {len(results)}")
        for result in results:
            print(f"- {result['class_name']}")
        
        # What methods does OpenAIModel have?
        results = await extractor.search_graph("methods_of_class", class_name="OpenAIModel")
        print(f"\\nMethods of OpenAIModel: {len(results)}")
        for result in results[:5]:
            print(f"- {result['method_name']}({', '.join(result['args'])})")
    
    finally:
        await extractor.close()


if __name__ == "__main__":
    asyncio.run(main())