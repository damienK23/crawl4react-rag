"""
Analyseur Supabase pour extraction du schéma de base de données

Analyse la structure de la base de données Supabase pour:
- Tables et leurs colonnes
- Types de données
- Contraintes et relations
- Fonctions RPC Supabase
- Politiques de sécurité (RLS)
- Index et triggers
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Set, Any, Optional, Tuple
from supabase import Client, create_client
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class ColumnInfo:
    """Information sur une colonne de table"""
    name: str
    data_type: str
    is_nullable: bool
    default_value: Optional[str] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_table: Optional[str] = None
    foreign_column: Optional[str] = None
    constraints: List[str] = field(default_factory=list)
    max_length: Optional[int] = None


@dataclass
class TableInfo:
    """Information sur une table Supabase"""
    name: str
    schema: str
    columns: List[ColumnInfo] = field(default_factory=list)
    primary_keys: List[str] = field(default_factory=list)
    foreign_keys: List[Dict[str, Any]] = field(default_factory=list)
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    rls_enabled: bool = False
    policies: List[Dict[str, Any]] = field(default_factory=list)
    estimated_rows: int = 0


@dataclass
class FunctionInfo:
    """Information sur une fonction RPC Supabase"""
    name: str
    schema: str
    return_type: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    language: str = 'plpgsql'
    security_definer: bool = False
    description: Optional[str] = None


@dataclass
class SupabaseSchemaInfo:
    """Schéma complet de la base de données Supabase"""
    project_url: str
    tables: List[TableInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    views: List[Dict[str, Any]] = field(default_factory=list)
    enums: List[Dict[str, Any]] = field(default_factory=list)
    extensions: List[str] = field(default_factory=list)
    schemas: List[str] = field(default_factory=list)


class SupabaseAnalyzer:
    """Analyseur pour extraire le schéma d'une base de données Supabase"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.client: Optional[Client] = None
        
    def connect(self) -> bool:
        """Établit la connexion à Supabase"""
        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            # Test de connexion basique
            self.client.table('_realtime_schema').select('*').limit(1).execute()
            logger.info("Connexion Supabase établie avec succès")
            return True
        except Exception as e:
            logger.error(f"Échec de connexion à Supabase: {e}")
            return False
    
    async def analyze_schema(self) -> SupabaseSchemaInfo:
        """Analyse complète du schéma Supabase"""
        if not self.client:
            if not self.connect():
                raise RuntimeError("Impossible de se connecter à Supabase")
        
        schema_info = SupabaseSchemaInfo(project_url=self.supabase_url)
        
        # Analyser les tables
        schema_info.tables = await self._analyze_tables()
        
        # Analyser les fonctions RPC
        schema_info.functions = await self._analyze_functions()
        
        # Analyser les vues
        schema_info.views = await self._analyze_views()
        
        # Analyser les enums
        schema_info.enums = await self._analyze_enums()
        
        # Analyser les extensions
        schema_info.extensions = await self._analyze_extensions()
        
        # Analyser les schémas
        schema_info.schemas = await self._analyze_schemas()
        
        return schema_info
    
    async def _analyze_tables(self) -> List[TableInfo]:
        """Analyse toutes les tables de la base de données"""
        tables = []
        
        try:
            # Requête pour obtenir les informations des tables
            query = """
            SELECT 
                table_schema,
                table_name,
                table_type
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            ORDER BY table_schema, table_name
            """
            
            result = self.client.rpc('execute_sql', {'query': query}).execute()
            
            if result.data:
                for row in result.data:
                    table_info = TableInfo(
                        name=row['table_name'],
                        schema=row['table_schema']
                    )
                    
                    # Analyser les colonnes de cette table
                    table_info.columns = await self._analyze_table_columns(
                        table_info.schema, table_info.name
                    )
                    
                    # Analyser les clés primaires
                    table_info.primary_keys = await self._analyze_primary_keys(
                        table_info.schema, table_info.name
                    )
                    
                    # Analyser les clés étrangères
                    table_info.foreign_keys = await self._analyze_foreign_keys(
                        table_info.schema, table_info.name
                    )
                    
                    # Analyser les index
                    table_info.indexes = await self._analyze_indexes(
                        table_info.schema, table_info.name
                    )
                    
                    # Vérifier RLS
                    table_info.rls_enabled = await self._check_rls_enabled(
                        table_info.schema, table_info.name
                    )
                    
                    # Analyser les politiques RLS
                    if table_info.rls_enabled:
                        table_info.policies = await self._analyze_rls_policies(
                            table_info.schema, table_info.name
                        )
                    
                    tables.append(table_info)
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des tables: {e}")
            # Fallback: utiliser les tables accessibles via l'API REST
            tables = await self._analyze_tables_fallback()
        
        return tables
    
    async def _analyze_table_columns(self, schema: str, table_name: str) -> List[ColumnInfo]:
        """Analyse les colonnes d'une table spécifique"""
        columns = []
        
        try:
            query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns 
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
            """
            
            result = self.client.rpc('execute_sql', {
                'query': query,
                'params': [schema, table_name]
            }).execute()
            
            if result.data:
                for row in result.data:
                    column = ColumnInfo(
                        name=row['column_name'],
                        data_type=row['data_type'],
                        is_nullable=row['is_nullable'] == 'YES',
                        default_value=row['column_default'],
                        max_length=row['character_maximum_length']
                    )
                    columns.append(column)
                    
        except Exception as e:
            logger.debug(f"Erreur lors de l'analyse des colonnes pour {table_name}: {e}")
        
        return columns
    
    async def _analyze_primary_keys(self, schema: str, table_name: str) -> List[str]:
        """Analyse les clés primaires d'une table"""
        try:
            query = """
            SELECT column_name
            FROM information_schema.key_column_usage k
            JOIN information_schema.table_constraints t
                ON k.constraint_name = t.constraint_name
            WHERE t.constraint_type = 'PRIMARY KEY'
                AND t.table_schema = $1
                AND t.table_name = $2
            ORDER BY k.ordinal_position
            """
            
            result = self.client.rpc('execute_sql', {
                'query': query,
                'params': [schema, table_name]
            }).execute()
            
            if result.data:
                return [row['column_name'] for row in result.data]
                
        except Exception as e:
            logger.debug(f"Erreur lors de l'analyse des clés primaires pour {table_name}: {e}")
        
        return []
    
    async def _analyze_foreign_keys(self, schema: str, table_name: str) -> List[Dict[str, Any]]:
        """Analyse les clés étrangères d'une table"""
        try:
            query = """
            SELECT 
                kcu.column_name,
                ccu.table_schema AS foreign_table_schema,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                tc.constraint_name
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = $1
                AND tc.table_name = $2
            """
            
            result = self.client.rpc('execute_sql', {
                'query': query,
                'params': [schema, table_name]
            }).execute()
            
            if result.data:
                return [{
                    'column_name': row['column_name'],
                    'foreign_table_schema': row['foreign_table_schema'],
                    'foreign_table_name': row['foreign_table_name'],
                    'foreign_column_name': row['foreign_column_name'],
                    'constraint_name': row['constraint_name']
                } for row in result.data]
                
        except Exception as e:
            logger.debug(f"Erreur lors de l'analyse des clés étrangères pour {table_name}: {e}")
        
        return []
    
    async def _analyze_indexes(self, schema: str, table_name: str) -> List[Dict[str, Any]]:
        """Analyse les index d'une table"""
        try:
            query = """
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = $1 AND tablename = $2
            """
            
            result = self.client.rpc('execute_sql', {
                'query': query,
                'params': [schema, table_name]
            }).execute()
            
            if result.data:
                return [{
                    'name': row['indexname'],
                    'definition': row['indexdef']
                } for row in result.data]
                
        except Exception as e:
            logger.debug(f"Erreur lors de l'analyse des index pour {table_name}: {e}")
        
        return []
    
    async def _check_rls_enabled(self, schema: str, table_name: str) -> bool:
        """Vérifie si RLS est activé sur une table"""
        try:
            query = """
            SELECT relrowsecurity
            FROM pg_class c
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = $1 AND c.relname = $2
            """
            
            result = self.client.rpc('execute_sql', {
                'query': query,
                'params': [schema, table_name]
            }).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]['relrowsecurity']
                
        except Exception as e:
            logger.debug(f"Erreur lors de la vérification RLS pour {table_name}: {e}")
        
        return False
    
    async def _analyze_rls_policies(self, schema: str, table_name: str) -> List[Dict[str, Any]]:
        """Analyse les politiques RLS d'une table"""
        try:
            query = """
            SELECT 
                policyname,
                permissive,
                roles,
                cmd,
                qual,
                with_check
            FROM pg_policies
            WHERE schemaname = $1 AND tablename = $2
            """
            
            result = self.client.rpc('execute_sql', {
                'query': query,
                'params': [schema, table_name]
            }).execute()
            
            if result.data:
                return [{
                    'name': row['policyname'],
                    'permissive': row['permissive'],
                    'roles': row['roles'],
                    'command': row['cmd'],
                    'qualifier': row['qual'],
                    'with_check': row['with_check']
                } for row in result.data]
                
        except Exception as e:
            logger.debug(f"Erreur lors de l'analyse des politiques RLS pour {table_name}: {e}")
        
        return []
    
    async def _analyze_functions(self) -> List[FunctionInfo]:
        """Analyse les fonctions RPC Supabase"""
        functions = []
        
        try:
            query = """
            SELECT 
                routine_schema,
                routine_name,
                data_type as return_type,
                routine_definition,
                external_language,
                security_type
            FROM information_schema.routines
            WHERE routine_schema NOT IN ('information_schema', 'pg_catalog')
                AND routine_type = 'FUNCTION'
            ORDER BY routine_schema, routine_name
            """
            
            result = self.client.rpc('execute_sql', {'query': query}).execute()
            
            if result.data:
                for row in result.data:
                    function_info = FunctionInfo(
                        name=row['routine_name'],
                        schema=row['routine_schema'],
                        return_type=row['return_type'],
                        language=row['external_language'] or 'plpgsql',
                        security_definer=row['security_type'] == 'DEFINER'
                    )
                    
                    # Analyser les paramètres de la fonction
                    function_info.parameters = await self._analyze_function_parameters(
                        function_info.schema, function_info.name
                    )
                    
                    functions.append(function_info)
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des fonctions: {e}")
        
        return functions
    
    async def _analyze_function_parameters(self, schema: str, function_name: str) -> List[Dict[str, Any]]:
        """Analyse les paramètres d'une fonction"""
        try:
            query = """
            SELECT 
                parameter_name,
                data_type,
                parameter_mode,
                ordinal_position
            FROM information_schema.parameters
            WHERE specific_schema = $1 AND specific_name LIKE $2
            ORDER BY ordinal_position
            """
            
            result = self.client.rpc('execute_sql', {
                'query': query,
                'params': [schema, f'%{function_name}%']
            }).execute()
            
            if result.data:
                return [{
                    'name': row['parameter_name'],
                    'type': row['data_type'],
                    'mode': row['parameter_mode'],
                    'position': row['ordinal_position']
                } for row in result.data]
                
        except Exception as e:
            logger.debug(f"Erreur lors de l'analyse des paramètres pour {function_name}: {e}")
        
        return []
    
    async def _analyze_views(self) -> List[Dict[str, Any]]:
        """Analyse les vues de la base de données"""
        try:
            query = """
            SELECT 
                table_schema,
                table_name,
                view_definition
            FROM information_schema.views
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_schema, table_name
            """
            
            result = self.client.rpc('execute_sql', {'query': query}).execute()
            
            if result.data:
                return [{
                    'schema': row['table_schema'],
                    'name': row['table_name'],
                    'definition': row['view_definition']
                } for row in result.data]
                
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des vues: {e}")
        
        return []
    
    async def _analyze_enums(self) -> List[Dict[str, Any]]:
        """Analyse les types enum de la base de données"""
        try:
            query = """
            SELECT 
                t.typname as enum_name,
                array_agg(e.enumlabel ORDER BY e.enumsortorder) as enum_values
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            JOIN pg_namespace n ON t.typnamespace = n.oid
            WHERE n.nspname NOT IN ('information_schema', 'pg_catalog')
            GROUP BY t.typname
            ORDER BY t.typname
            """
            
            result = self.client.rpc('execute_sql', {'query': query}).execute()
            
            if result.data:
                return [{
                    'name': row['enum_name'],
                    'values': row['enum_values']
                } for row in result.data]
                
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des enums: {e}")
        
        return []
    
    async def _analyze_extensions(self) -> List[str]:
        """Analyse les extensions PostgreSQL installées"""
        try:
            query = "SELECT extname FROM pg_extension ORDER BY extname"
            
            result = self.client.rpc('execute_sql', {'query': query}).execute()
            
            if result.data:
                return [row['extname'] for row in result.data]
                
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des extensions: {e}")
        
        return []
    
    async def _analyze_schemas(self) -> List[str]:
        """Analyse les schémas de la base de données"""
        try:
            query = """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            ORDER BY schema_name
            """
            
            result = self.client.rpc('execute_sql', {'query': query}).execute()
            
            if result.data:
                return [row['schema_name'] for row in result.data]
                
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des schémas: {e}")
        
        return []
    
    async def _analyze_tables_fallback(self) -> List[TableInfo]:
        """Méthode de fallback pour analyser les tables via l'API REST"""
        tables = []
        
        try:
            # Essayer d'accéder aux tables publiques via l'API REST
            common_tables = ['users', 'profiles', 'posts', 'comments', 'logs', 'settings']
            
            for table_name in common_tables:
                try:
                    # Test d'accès à la table
                    result = self.client.table(table_name).select('*').limit(1).execute()
                    
                    # Si succès, créer une entrée basique
                    table_info = TableInfo(
                        name=table_name,
                        schema='public'
                    )
                    tables.append(table_info)
                    
                except Exception:
                    # Table n'existe pas ou pas d'accès
                    continue
                    
        except Exception as e:
            logger.debug(f"Erreur dans la méthode fallback: {e}")
        
        return tables
    
    def export_schema_to_json(self, schema_info: SupabaseSchemaInfo, output_path: str):
        """Exporte le schéma vers un fichier JSON"""
        schema_dict = {
            'project_url': schema_info.project_url,
            'export_timestamp': asyncio.get_event_loop().time(),
            'tables': [
                {
                    'name': table.name,
                    'schema': table.schema,
                    'columns': [
                        {
                            'name': col.name,
                            'data_type': col.data_type,
                            'is_nullable': col.is_nullable,
                            'default_value': col.default_value,
                            'is_primary_key': col.is_primary_key,
                            'is_foreign_key': col.is_foreign_key,
                            'foreign_table': col.foreign_table,
                            'foreign_column': col.foreign_column,
                            'max_length': col.max_length
                        } for col in table.columns
                    ],
                    'primary_keys': table.primary_keys,
                    'foreign_keys': table.foreign_keys,
                    'rls_enabled': table.rls_enabled,
                    'policies': table.policies
                } for table in schema_info.tables
            ],
            'functions': [
                {
                    'name': func.name,
                    'schema': func.schema,
                    'return_type': func.return_type,
                    'parameters': func.parameters,
                    'language': func.language,
                    'security_definer': func.security_definer
                } for func in schema_info.functions
            ],
            'views': schema_info.views,
            'enums': schema_info.enums,
            'extensions': schema_info.extensions,
            'schemas': schema_info.schemas
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schema_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Schéma Supabase exporté vers: {output_path}")


async def main():
    """Test de l'analyseur Supabase"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("Variables d'environnement Supabase manquantes")
        return
    
    analyzer = SupabaseAnalyzer(supabase_url, supabase_key)
    
    if analyzer.connect():
        schema_info = await analyzer.analyze_schema()
        
        print(f"Analyse terminée:")
        print(f"- Tables: {len(schema_info.tables)}")
        print(f"- Fonctions: {len(schema_info.functions)}")
        print(f"- Vues: {len(schema_info.views)}")
        print(f"- Enums: {len(schema_info.enums)}")
        
        # Exporter le schéma
        analyzer.export_schema_to_json(schema_info, 'supabase_schema.json')


if __name__ == "__main__":
    asyncio.run(main())