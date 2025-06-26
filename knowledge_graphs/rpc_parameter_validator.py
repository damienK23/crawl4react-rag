#!/usr/bin/env python3
"""
Validateur avancé des paramètres de fonctions RPC Supabase

Améliore la validation pour inclure :
1. Validation des types de paramètres (string vs UUID vs int)
2. Validation des paramètres obligatoires vs optionnels 
3. Validation des valeurs enum
4. Validation de la structure des objets JSON
5. Vérification du nombre de paramètres
"""

import re
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Union, Set
from enum import Enum

from supabase_analyzer import FunctionInfo, SupabaseSchemaInfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ParameterValidationType(Enum):
    """Types de validation des paramètres"""
    TYPE_MISMATCH = "TYPE_MISMATCH"
    MISSING_REQUIRED = "MISSING_REQUIRED"
    INVALID_ENUM = "INVALID_ENUM"
    INVALID_JSON_STRUCTURE = "INVALID_JSON_STRUCTURE"
    PARAMETER_COUNT_MISMATCH = "PARAMETER_COUNT_MISMATCH"
    OPTIONAL_NOT_PROVIDED = "OPTIONAL_NOT_PROVIDED"


class ParameterType(Enum):
    """Types de paramètres supportés"""
    STRING = "text"
    INTEGER = "bigint"
    UUID = "uuid"
    BOOLEAN = "boolean"
    JSON = "json"
    JSONB = "jsonb"
    TIMESTAMP = "timestamp"
    DATE = "date"
    NUMERIC = "numeric"
    ARRAY = "array"
    ENUM = "enum"


@dataclass
class ParameterValidationError:
    """Erreur de validation de paramètre"""
    parameter_name: str
    validation_type: ParameterValidationType
    expected: str
    actual: str
    message: str
    severity: str = "HIGH"
    line_number: int = 0
    suggestion: str = ""


@dataclass
class ExpectedParameter:
    """Paramètre attendu avec métadonnées complètes"""
    name: str
    type: ParameterType
    is_required: bool
    position: int
    enum_values: Optional[List[str]] = None
    json_schema: Optional[Dict[str, Any]] = None
    default_value: Optional[Any] = None
    description: Optional[str] = None


@dataclass
class ProvidedParameter:
    """Paramètre fourni dans le code"""
    name: str
    value: Any
    raw_value: str
    inferred_type: ParameterType
    position: int


class RPCParameterValidator:
    """Validateur avancé des paramètres RPC"""
    
    def __init__(self, supabase_schema: SupabaseSchemaInfo):
        self.supabase_schema = supabase_schema
        self.enum_cache = self._build_enum_cache()
        self.function_cache = self._build_function_cache()
        
        # Patterns de validation
        self.uuid_pattern = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.url_pattern = re.compile(r'^https?://[^\s/$.?#].[^\s]*$')
    
    def _build_function_cache(self) -> Dict[str, List[ExpectedParameter]]:
        """Construire le cache des fonctions avec paramètres détaillés"""
        cache = {}
        
        for function in self.supabase_schema.functions:
            expected_params = []
            
            for i, param in enumerate(function.parameters):
                param_type = self._map_parameter_type(param.get('type', 'text'))
                is_required = param.get('mode', 'IN') == 'IN' and not param.get('default')
                
                expected_param = ExpectedParameter(
                    name=param.get('name', f'param_{i}'),
                    type=param_type,
                    is_required=is_required,
                    position=param.get('position', i + 1),
                    enum_values=self._get_enum_values(param.get('type')),
                    json_schema=self._get_json_schema(param.get('type')),
                    default_value=param.get('default'),
                    description=param.get('description')
                )
                expected_params.append(expected_param)
            
            cache[function.name] = expected_params
        
        return cache
    
    def _build_enum_cache(self) -> Dict[str, List[str]]:
        """Construire le cache des enums"""
        cache = {}
        
        for enum_info in self.supabase_schema.enums:
            cache[enum_info['name']] = enum_info['values']
        
        return cache
    
    def _map_parameter_type(self, pg_type: str) -> ParameterType:
        """Mapper les types PostgreSQL vers nos types"""
        type_mapping = {
            'text': ParameterType.STRING,
            'varchar': ParameterType.STRING,
            'char': ParameterType.STRING,
            'bigint': ParameterType.INTEGER,
            'integer': ParameterType.INTEGER,
            'int': ParameterType.INTEGER,
            'uuid': ParameterType.UUID,
            'boolean': ParameterType.BOOLEAN,
            'bool': ParameterType.BOOLEAN,
            'json': ParameterType.JSON,
            'jsonb': ParameterType.JSONB,
            'timestamp': ParameterType.TIMESTAMP,
            'timestamptz': ParameterType.TIMESTAMP,
            'date': ParameterType.DATE,
            'numeric': ParameterType.NUMERIC,
            'decimal': ParameterType.NUMERIC,
            'array': ParameterType.ARRAY
        }
        
        # Vérifier si c'est un enum
        if pg_type in self.enum_cache:
            return ParameterType.ENUM
        
        return type_mapping.get(pg_type.lower(), ParameterType.STRING)
    
    def _get_enum_values(self, pg_type: str) -> Optional[List[str]]:
        """Obtenir les valeurs d'un enum"""
        return self.enum_cache.get(pg_type)
    
    def _get_json_schema(self, pg_type: str) -> Optional[Dict[str, Any]]:
        """Obtenir le schéma JSON pour les types JSON"""
        # Pour l'instant, schemas JSON basiques
        if pg_type in ['json', 'jsonb']:
            return {
                "type": "object",
                "properties": {},
                "additionalProperties": True
            }
        return None
    
    def validate_rpc_call(self, function_name: str, provided_params: Dict[str, Any], 
                         line_number: int = 0) -> List[ParameterValidationError]:
        """Valider un appel RPC complet"""
        errors = []
        
        # Vérifier que la fonction existe
        if function_name not in self.function_cache:
            return [ParameterValidationError(
                parameter_name="function",
                validation_type=ParameterValidationType.TYPE_MISMATCH,
                expected=f"One of: {', '.join(self.function_cache.keys())}",
                actual=function_name,
                message=f"RPC function '{function_name}' not found",
                line_number=line_number,
                suggestion=f"Available functions: {', '.join(list(self.function_cache.keys())[:3])}"
            )]
        
        expected_params = self.function_cache[function_name]
        
        # 1. Validation du nombre de paramètres
        errors.extend(self._validate_parameter_count(
            expected_params, provided_params, line_number
        ))
        
        # 2. Validation des paramètres requis
        errors.extend(self._validate_required_parameters(
            expected_params, provided_params, line_number
        ))
        
        # 3. Validation des types de paramètres
        errors.extend(self._validate_parameter_types(
            expected_params, provided_params, line_number
        ))
        
        # 4. Validation des valeurs enum
        errors.extend(self._validate_enum_values(
            expected_params, provided_params, line_number
        ))
        
        # 5. Validation des structures JSON
        errors.extend(self._validate_json_structures(
            expected_params, provided_params, line_number
        ))
        
        return errors
    
    def _validate_parameter_count(self, expected: List[ExpectedParameter], 
                                 provided: Dict[str, Any], line_number: int) -> List[ParameterValidationError]:
        """Valider le nombre de paramètres"""
        errors = []
        
        required_count = sum(1 for p in expected if p.is_required)
        total_expected = len(expected)
        provided_count = len(provided)
        
        # Trop peu de paramètres
        if provided_count < required_count:
            errors.append(ParameterValidationError(
                parameter_name="parameter_count",
                validation_type=ParameterValidationType.PARAMETER_COUNT_MISMATCH,
                expected=f"At least {required_count} parameters",
                actual=f"{provided_count} parameters",
                message=f"Missing required parameters. Expected at least {required_count}, got {provided_count}",
                line_number=line_number,
                suggestion=f"Add missing required parameters: {', '.join([p.name for p in expected if p.is_required and p.name not in provided])}"
            ))
        
        # Trop de paramètres
        if provided_count > total_expected:
            extra_params = set(provided.keys()) - set(p.name for p in expected)
            errors.append(ParameterValidationError(
                parameter_name="parameter_count",
                validation_type=ParameterValidationType.PARAMETER_COUNT_MISMATCH,
                expected=f"At most {total_expected} parameters",
                actual=f"{provided_count} parameters",
                message=f"Too many parameters. Expected at most {total_expected}, got {provided_count}",
                line_number=line_number,
                suggestion=f"Remove unexpected parameters: {', '.join(extra_params)}"
            ))
        
        return errors
    
    def _validate_required_parameters(self, expected: List[ExpectedParameter], 
                                    provided: Dict[str, Any], line_number: int) -> List[ParameterValidationError]:
        """Valider les paramètres requis"""
        errors = []
        
        for param in expected:
            if param.is_required and param.name not in provided:
                errors.append(ParameterValidationError(
                    parameter_name=param.name,
                    validation_type=ParameterValidationType.MISSING_REQUIRED,
                    expected=f"Required parameter '{param.name}' of type {param.type.value}",
                    actual="Missing",
                    message=f"Required parameter '{param.name}' is missing",
                    line_number=line_number,
                    suggestion=f"Add required parameter: {param.name}: {param.type.value}"
                ))
        
        return errors
    
    def _validate_parameter_types(self, expected: List[ExpectedParameter], 
                                provided: Dict[str, Any], line_number: int) -> List[ParameterValidationError]:
        """Valider les types de paramètres"""
        errors = []
        
        expected_by_name = {p.name: p for p in expected}
        
        for param_name, param_value in provided.items():
            if param_name not in expected_by_name:
                continue  # Déjà géré dans parameter_count
            
            expected_param = expected_by_name[param_name]
            inferred_type = self._infer_type(param_value)
            
            # Validation spécifique par type
            if expected_param.type == ParameterType.UUID:
                if not self._is_valid_uuid(param_value):
                    errors.append(ParameterValidationError(
                        parameter_name=param_name,
                        validation_type=ParameterValidationType.TYPE_MISMATCH,
                        expected="Valid UUID format",
                        actual=f"'{param_value}' ({inferred_type.value})",
                        message=f"Parameter '{param_name}' must be a valid UUID",
                        line_number=line_number,
                        suggestion="Use format: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'"
                    ))
            
            elif expected_param.type == ParameterType.INTEGER:
                if not self._is_valid_integer(param_value):
                    errors.append(ParameterValidationError(
                        parameter_name=param_name,
                        validation_type=ParameterValidationType.TYPE_MISMATCH,
                        expected="Integer",
                        actual=f"'{param_value}' ({inferred_type.value})",
                        message=f"Parameter '{param_name}' must be an integer",
                        line_number=line_number,
                        suggestion="Use an integer value like 123"
                    ))
            
            elif expected_param.type == ParameterType.BOOLEAN:
                if not self._is_valid_boolean(param_value):
                    errors.append(ParameterValidationError(
                        parameter_name=param_name,
                        validation_type=ParameterValidationType.TYPE_MISMATCH,
                        expected="Boolean",
                        actual=f"'{param_value}' ({inferred_type.value})",
                        message=f"Parameter '{param_name}' must be a boolean",
                        line_number=line_number,
                        suggestion="Use true or false"
                    ))
            
            elif expected_param.type == ParameterType.TIMESTAMP:
                if not self._is_valid_timestamp(param_value):
                    errors.append(ParameterValidationError(
                        parameter_name=param_name,
                        validation_type=ParameterValidationType.TYPE_MISMATCH,
                        expected="ISO timestamp",
                        actual=f"'{param_value}'",
                        message=f"Parameter '{param_name}' must be a valid timestamp",
                        line_number=line_number,
                        suggestion="Use ISO format: '2024-01-01T00:00:00Z'"
                    ))
        
        return errors
    
    def _validate_enum_values(self, expected: List[ExpectedParameter], 
                            provided: Dict[str, Any], line_number: int) -> List[ParameterValidationError]:
        """Valider les valeurs enum"""
        errors = []
        
        expected_by_name = {p.name: p for p in expected}
        
        for param_name, param_value in provided.items():
            if param_name not in expected_by_name:
                continue
            
            expected_param = expected_by_name[param_name]
            
            if expected_param.type == ParameterType.ENUM and expected_param.enum_values:
                if str(param_value) not in expected_param.enum_values:
                    errors.append(ParameterValidationError(
                        parameter_name=param_name,
                        validation_type=ParameterValidationType.INVALID_ENUM,
                        expected=f"One of: {', '.join(expected_param.enum_values)}",
                        actual=f"'{param_value}'",
                        message=f"Parameter '{param_name}' has invalid enum value",
                        line_number=line_number,
                        suggestion=f"Use one of: {', '.join(expected_param.enum_values[:3])}"
                    ))
        
        return errors
    
    def _validate_json_structures(self, expected: List[ExpectedParameter], 
                                provided: Dict[str, Any], line_number: int) -> List[ParameterValidationError]:
        """Valider les structures JSON"""
        errors = []
        
        expected_by_name = {p.name: p for p in expected}
        
        for param_name, param_value in provided.items():
            if param_name not in expected_by_name:
                continue
            
            expected_param = expected_by_name[param_name]
            
            if expected_param.type in [ParameterType.JSON, ParameterType.JSONB]:
                # Vérifier que c'est un objet JSON valide
                if not self._is_valid_json_object(param_value):
                    errors.append(ParameterValidationError(
                        parameter_name=param_name,
                        validation_type=ParameterValidationType.INVALID_JSON_STRUCTURE,
                        expected="Valid JSON object",
                        actual=f"'{param_value}'",
                        message=f"Parameter '{param_name}' must be a valid JSON object",
                        line_number=line_number,
                        suggestion="Use object format: {key: 'value'}"
                    ))
                
                # Validation du schéma JSON si disponible
                elif expected_param.json_schema:
                    schema_errors = self._validate_json_schema(
                        param_value, expected_param.json_schema, param_name
                    )
                    errors.extend([
                        ParameterValidationError(
                            parameter_name=param_name,
                            validation_type=ParameterValidationType.INVALID_JSON_STRUCTURE,
                            expected=error['expected'],
                            actual=error['actual'],
                            message=error['message'],
                            line_number=line_number,
                            suggestion=error['suggestion']
                        ) for error in schema_errors
                    ])
        
        return errors
    
    def _infer_type(self, value: Any) -> ParameterType:
        """Inférer le type d'une valeur"""
        if isinstance(value, bool):
            return ParameterType.BOOLEAN
        elif isinstance(value, int):
            return ParameterType.INTEGER
        elif isinstance(value, str):
            if self._is_valid_uuid(value):
                return ParameterType.UUID
            elif self._is_valid_timestamp(value):
                return ParameterType.TIMESTAMP
            else:
                return ParameterType.STRING
        elif isinstance(value, (dict, list)):
            return ParameterType.JSON
        else:
            return ParameterType.STRING
    
    def _is_valid_uuid(self, value: Any) -> bool:
        """Vérifier si une valeur est un UUID valide"""
        if not isinstance(value, str):
            return False
        return bool(self.uuid_pattern.match(value))
    
    def _is_valid_integer(self, value: Any) -> bool:
        """Vérifier si une valeur est un entier valide"""
        if isinstance(value, int):
            return True
        if isinstance(value, str):
            try:
                int(value)
                return True
            except ValueError:
                return False
        return False
    
    def _is_valid_boolean(self, value: Any) -> bool:
        """Vérifier si une valeur est un booléen valide"""
        if isinstance(value, bool):
            return True
        if isinstance(value, str):
            return value.lower() in ['true', 'false', '0', '1']
        return False
    
    def _is_valid_timestamp(self, value: Any) -> bool:
        """Vérifier si une valeur est un timestamp valide"""
        if not isinstance(value, str):
            return False
        
        # Patterns ISO 8601 basiques
        timestamp_patterns = [
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?$',
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z?$',
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
        ]
        
        return any(re.match(pattern, value) for pattern in timestamp_patterns)
    
    def _is_valid_json_object(self, value: Any) -> bool:
        """Vérifier si une valeur est un objet JSON valide"""
        if isinstance(value, (dict, list)):
            return True
        
        if isinstance(value, str):
            try:
                json.loads(value)
                return True
            except (json.JSONDecodeError, TypeError):
                return False
        
        return False
    
    def _validate_json_schema(self, value: Any, schema: Dict[str, Any], 
                            param_name: str) -> List[Dict[str, str]]:
        """Valider une valeur contre un schéma JSON basique"""
        errors = []
        
        if not isinstance(value, dict):
            errors.append({
                'expected': 'JSON object',
                'actual': f'{type(value).__name__}',
                'message': f'Parameter {param_name} must be an object',
                'suggestion': 'Use object format: {key: "value"}'
            })
            return errors
        
        # Validation basique des propriétés requises
        if 'required' in schema:
            for required_prop in schema['required']:
                if required_prop not in value:
                    errors.append({
                        'expected': f'Required property: {required_prop}',
                        'actual': 'Missing',
                        'message': f'Missing required property {required_prop}',
                        'suggestion': f'Add property: {required_prop}'
                    })
        
        # Validation des types de propriétés
        if 'properties' in schema:
            for prop_name, prop_schema in schema['properties'].items():
                if prop_name in value:
                    prop_value = value[prop_name]
                    expected_type = prop_schema.get('type', 'any')
                    
                    if expected_type == 'string' and not isinstance(prop_value, str):
                        errors.append({
                            'expected': f'{prop_name}: string',
                            'actual': f'{prop_name}: {type(prop_value).__name__}',
                            'message': f'Property {prop_name} must be a string',
                            'suggestion': f'Use string value for {prop_name}'
                        })
        
        return errors


def parse_rpc_parameters(content: str, function_name: str, line_number: int) -> Dict[str, Any]:
    """Extraire les paramètres d'un appel RPC depuis le code TypeScript"""
    
    # Pattern pour extraire les paramètres d'un appel .rpc()
    rpc_pattern = rf"\.rpc\s*\(\s*['\"]({re.escape(function_name)})['\"],\s*(\{{[^}}]*\}}|\{{[^}}]+\}})"
    
    match = re.search(rpc_pattern, content, re.DOTALL)
    if not match:
        return {}
    
    params_str = match.group(2)
    
    try:
        # Nettoyage basique pour conversion JSON
        # Remplacer les identifiants non-quotés par des chaînes
        cleaned = re.sub(r'(\w+):', r'"\1":', params_str)
        # Gérer les variables (remplacer par des chaînes de placeholder)
        cleaned = re.sub(r':\s*([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*)', r': "VARIABLE_\1"', cleaned)
        
        # Parser en JSON
        params = json.loads(cleaned)
        
        # Post-traitement pour détecter les types
        processed_params = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("VARIABLE_"):
                # C'est une variable, essayer d'inférer le type
                var_name = value.replace("VARIABLE_", "")
                if 'id' in var_name.lower() or 'uuid' in var_name.lower():
                    processed_params[key] = "00000000-0000-0000-0000-000000000000"  # UUID placeholder
                else:
                    processed_params[key] = "string_variable"
            else:
                processed_params[key] = value
        
        return processed_params
    
    except (json.JSONDecodeError, Exception):
        # Fallback : parsing manuel basique
        param_matches = re.findall(r'(\w+):\s*([^,}]+)', params_str)
        return {key: value.strip('\'"') for key, value in param_matches}


# === EXEMPLE D'UTILISATION ===
if __name__ == "__main__":
    # Test avec un schéma factice
    from supabase_analyzer import SupabaseSchemaInfo, FunctionInfo
    
    # Créer un schéma de test
    schema = SupabaseSchemaInfo(project_url="test")
    
    # Fonction de test avec paramètres typés
    test_function = FunctionInfo(
        name="get_user_analytics",
        schema="public",
        return_type="json",
        parameters=[
            {"name": "user_id", "type": "uuid", "mode": "IN", "position": 1},
            {"name": "date_range", "type": "text", "mode": "IN", "position": 2},
            {"name": "include_details", "type": "boolean", "mode": "IN", "position": 3, "default": "false"},
            {"name": "metrics_config", "type": "json", "mode": "IN", "position": 4}
        ]
    )
    
    schema.functions = [test_function]
    schema.enums = [
        {"name": "date_range_type", "values": ["7d", "30d", "90d", "1y"]}
    ]
    
    # Créer le validateur
    validator = RPCParameterValidator(schema)
    
    # Test de validation
    provided_params = {
        "user_id": "not-a-uuid",  # ❌ Invalid UUID
        "date_range": "invalid",  # ❌ Could be enum
        "include_details": "maybe",  # ❌ Invalid boolean
        "metrics_config": "not-json",  # ❌ Invalid JSON
        "extra_param": "unexpected"  # ❌ Unexpected parameter
    }
    
    errors = validator.validate_rpc_call("get_user_analytics", provided_params, 45)
    
    print("🧪 RPC PARAMETER VALIDATION TEST")
    print("=" * 50)
    print(f"Function: get_user_analytics")
    print(f"Provided parameters: {provided_params}")
    print(f"\nValidation errors found: {len(errors)}")
    
    for error in errors:
        print(f"\n❌ {error.validation_type.value}:")
        print(f"   Parameter: {error.parameter_name}")
        print(f"   Expected: {error.expected}")
        print(f"   Actual: {error.actual}")
        print(f"   Message: {error.message}")
        print(f"   Suggestion: {error.suggestion}")