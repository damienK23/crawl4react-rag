"""
TypeScript/JavaScript Knowledge Graph Validator

Validates TypeScript/JavaScript code against a knowledge graph containing
React, TypeScript, and JavaScript patterns for hallucination detection.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Import the TS analyzer we created
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from .typescript_analyzer import (
    AnalysisResult as TSAnalysisResult, ImportInfo, TypeScriptAnalyzer as TSScriptAnalyzer,
    FunctionCall
)

logger = logging.getLogger(__name__)

# Temporary stub classes for missing types
@dataclass
class MethodCall:
    object_name: str
    method_name: str
    args: List[str]
    line_number: int

@dataclass
class ClassInstantiation:
    class_name: str
    args: List[str]
    line_number: int

@dataclass
class AttributeAccess:
    object_name: str
    attribute_name: str
    line_number: int

class ValidationStatus(Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    UNCERTAIN = "UNCERTAIN"
    NOT_FOUND = "NOT_FOUND"

@dataclass
class ValidationResult:
    status: ValidationStatus
    confidence: float
    message: str
    details: Dict[str, Any]
    suggestions: List[str] = None

    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []

@dataclass
class TSValidationResult:
    """Results from validating an import"""
    item_info: Any  # ImportInfo, MethodCall, etc.
    validation: ValidationResult
    expected_params: List[str] = None
    available_methods: List[str] = None

@dataclass
class TSScriptValidationResult:
    """Complete validation results for a TypeScript/JavaScript script"""
    script_path: str
    language: str
    import_validations: List[TSValidationResult]
    class_validations: List[TSValidationResult]
    method_validations: List[TSValidationResult]
    function_validations: List[TSValidationResult]
    attribute_validations: List[TSValidationResult]
    overall_confidence: float
    hallucinations_detected: List[Dict[str, Any]]

class TSKnowledgeGraphValidator:
    """Validates TypeScript/JavaScript code against known patterns"""
    
    def __init__(self):
        self.analyzer = TSScriptAnalyzer()
        self.known_libraries = self._initialize_known_libraries()
        self.react_patterns = self._initialize_react_patterns()
        self.js_patterns = self._initialize_js_patterns()
        self.ts_patterns = self._initialize_ts_patterns()
    
    def _initialize_known_libraries(self) -> Dict[str, Dict[str, Any]]:
        """Initialize known npm libraries and their patterns"""
        return {
            'react': {
                'type': 'framework',
                'hooks': [
                    'useState', 'useEffect', 'useContext', 'useReducer',
                    'useCallback', 'useMemo', 'useRef', 'useImperativeHandle',
                    'useLayoutEffect', 'useDebugValue', 'useDeferredValue',
                    'useTransition', 'useId', 'useSyncExternalStore'
                ],
                'components': ['Component', 'PureComponent', 'Fragment', 'StrictMode'],
                'methods': ['createElement', 'cloneElement', 'createContext', 'lazy', 'Suspense', 'memo'],
                'confidence': 0.95
            },
            'react-dom': {
                'type': 'library',
                'methods': ['render', 'hydrate', 'unmountComponentAtNode', 'findDOMNode'],
                'confidence': 0.95
            },
            'react-router': {
                'type': 'library',
                'components': ['Router', 'Route', 'Switch', 'Link', 'NavLink'],
                'hooks': ['useHistory', 'useLocation', 'useParams', 'useRouteMatch'],
                'confidence': 0.90
            },
            'react-router-dom': {
                'type': 'library',
                'components': ['BrowserRouter', 'HashRouter', 'MemoryRouter', 'Link', 'NavLink'],
                'hooks': ['useNavigate', 'useLocation', 'useParams'],
                'confidence': 0.90
            },
            'axios': {
                'type': 'library',
                'methods': ['get', 'post', 'put', 'delete', 'patch', 'head', 'options'],
                'static_methods': ['create', 'all', 'spread'],
                'confidence': 0.95
            },
            'lodash': {
                'type': 'utility',
                'methods': ['map', 'filter', 'reduce', 'find', 'some', 'every', 'forEach'],
                'confidence': 0.90
            },
            '@types/react': {
                'type': 'types',
                'confidence': 0.95
            },
            '@types/node': {
                'type': 'types',
                'confidence': 0.95
            },
            'typescript': {
                'type': 'language',
                'confidence': 0.95
            }
        }
    
    def _initialize_react_patterns(self) -> Dict[str, Any]:
        """Initialize React-specific patterns and validations"""
        return {
            'component_patterns': [
                'function.*Component',
                'const.*=.*\\(.*\\).*=>',
                'class.*extends.*Component'
            ],
            'jsx_patterns': [
                '<\\w+.*>',
                '</\\w+>',
                '<\\w+.*/>',
                '{.*}'
            ],
            'lifecycle_methods': [
                'componentDidMount', 'componentDidUpdate', 'componentWillUnmount',
                'shouldComponentUpdate', 'getSnapshotBeforeUpdate',
                'componentDidCatch', 'getDerivedStateFromError'
            ],
            'prop_types': ['PropTypes.string', 'PropTypes.number', 'PropTypes.bool']
        }
    
    def _initialize_js_patterns(self) -> Dict[str, Any]:
        """Initialize JavaScript built-in patterns"""
        return {
            'global_objects': ['window', 'document', 'navigator', 'console', 'localStorage', 'sessionStorage'],
            'array_methods': [
                'map', 'filter', 'reduce', 'forEach', 'find', 'some', 'every',
                'push', 'pop', 'shift', 'unshift', 'slice', 'splice', 'sort'
            ],
            'object_methods': ['keys', 'values', 'entries', 'assign', 'freeze', 'seal'],
            'promise_methods': ['then', 'catch', 'finally', 'resolve', 'reject', 'all', 'race'],
            'json_methods': ['parse', 'stringify'],
            'math_methods': ['floor', 'ceil', 'round', 'random', 'max', 'min'],
            'date_methods': ['now', 'getTime', 'toISOString', 'getFullYear']
        }
    
    def _initialize_ts_patterns(self) -> Dict[str, Any]:
        """Initialize TypeScript-specific patterns"""
        return {
            'utility_types': [
                'Partial', 'Required', 'Readonly', 'Record', 'Pick', 'Omit',
                'Exclude', 'Extract', 'NonNullable', 'Parameters', 'ReturnType'
            ],
            'decorators': ['@Component', '@Injectable', '@Input', '@Output'],
            'type_assertions': ['as', 'satisfies'],
            'generic_patterns': ['<T>', '<K, V>', '<T extends']
        }
    
    async def validate_script(self, analysis_result: TSAnalysisResult) -> TSScriptValidationResult:
        """
        Validate a TypeScript/JavaScript script analysis against known patterns
        
        Args:
            analysis_result: Results from TSScriptAnalyzer
            
        Returns:
            TSScriptValidationResult with validation results
        """
        # Validate imports
        import_validations = []
        for import_info in analysis_result.imports:
            validation = await self._validate_import(import_info)
            import_validations.append(TSValidationResult(
                item_info=import_info,
                validation=validation
            ))
        
        # Validate class instantiations
        class_validations = []
        for class_inst in analysis_result.class_instantiations:
            validation = await self._validate_class_instantiation(class_inst)
            class_validations.append(TSValidationResult(
                item_info=class_inst,
                validation=validation
            ))
        
        # Validate method calls
        method_validations = []
        for method_call in analysis_result.method_calls:
            validation = await self._validate_method_call(method_call)
            method_validations.append(TSValidationResult(
                item_info=method_call,
                validation=validation
            ))
        
        # Validate function calls
        function_validations = []
        for function_call in analysis_result.function_calls:
            validation = await self._validate_function_call(function_call)
            function_validations.append(TSValidationResult(
                item_info=function_call,
                validation=validation
            ))
        
        # Validate attribute accesses
        attribute_validations = []
        for attr_access in analysis_result.attribute_accesses:
            validation = await self._validate_attribute_access(attr_access)
            attribute_validations.append(TSValidationResult(
                item_info=attr_access,
                validation=validation
            ))
        
        # Calculate overall confidence
        all_validations = (import_validations + class_validations + 
                          method_validations + function_validations + attribute_validations)
        
        if all_validations:
            overall_confidence = sum(v.validation.confidence for v in all_validations) / len(all_validations)
        else:
            overall_confidence = 0.0
        
        # Detect hallucinations
        hallucinations = self._detect_hallucinations(all_validations)
        
        return TSScriptValidationResult(
            script_path=analysis_result.script_path,
            language=analysis_result.language,
            import_validations=import_validations,
            class_validations=class_validations,
            method_validations=method_validations,
            function_validations=function_validations,
            attribute_validations=attribute_validations,
            overall_confidence=overall_confidence,
            hallucinations_detected=hallucinations
        )
    
    async def _validate_import(self, import_info: ImportInfo) -> ValidationResult:
        """Validate an import statement"""
        module = import_info.module
        
        # Check against known libraries
        if module in self.known_libraries:
            lib_info = self.known_libraries[module]
            return ValidationResult(
                status=ValidationStatus.VALID,
                confidence=lib_info['confidence'],
                message=f"Known {lib_info['type']}: {module}",
                details={
                    'library_type': lib_info['type'],
                    'in_knowledge_graph': True
                }
            )
        
        # Check for relative imports
        if module.startswith('.'):
            return ValidationResult(
                status=ValidationStatus.UNCERTAIN,
                confidence=0.7,
                message=f"Local module import: {module}",
                details={
                    'import_type': 'local',
                    'in_knowledge_graph': False
                },
                suggestions=['Verify the local module exists']
            )
        
        # Check for scoped packages
        if module.startswith('@'):
            return ValidationResult(
                status=ValidationStatus.UNCERTAIN,
                confidence=0.6,
                message=f"Scoped package: {module}",
                details={
                    'import_type': 'scoped_package',
                    'in_knowledge_graph': False
                },
                suggestions=['Verify the scoped package is installed']
            )
        
        # Unknown library
        return ValidationResult(
            status=ValidationStatus.UNCERTAIN,
            confidence=0.4,
            message=f"Unknown library: {module}",
            details={
                'import_type': 'unknown',
                'in_knowledge_graph': False
            },
            suggestions=[f'Verify {module} is a valid npm package']
        )
    
    async def _validate_method_call(self, method_call: MethodCall) -> ValidationResult:
        """Validate a method call"""
        method_name = method_call.method_name
        object_name = method_call.object_name
        
        # Check React hooks
        if method_name in self.known_libraries['react']['hooks']:
            return ValidationResult(
                status=ValidationStatus.VALID,
                confidence=0.95,
                message=f"Valid React hook: {method_name}",
                details={'framework': 'react', 'type': 'hook'}
            )
        
        # Check array methods
        if method_name in self.js_patterns['array_methods']:
            return ValidationResult(
                status=ValidationStatus.VALID,
                confidence=0.90,
                message=f"Valid array method: {method_name}",
                details={'type': 'array_method'}
            )
        
        # Check object methods
        if object_name == 'Object' and method_name in self.js_patterns['object_methods']:
            return ValidationResult(
                status=ValidationStatus.VALID,
                confidence=0.95,
                message=f"Valid Object method: {method_name}",
                details={'type': 'object_method'}
            )
        
        # Check console methods
        if object_name == 'console' and method_name in ['log', 'error', 'warn', 'info']:
            return ValidationResult(
                status=ValidationStatus.VALID,
                confidence=0.98,
                message=f"Valid console method: {method_name}",
                details={'type': 'console_method'}
            )
        
        # Check Promise methods
        if method_name in self.js_patterns['promise_methods']:
            return ValidationResult(
                status=ValidationStatus.VALID,
                confidence=0.85,
                message=f"Valid Promise method: {method_name}",
                details={'type': 'promise_method'}
            )
        
        # Check common React lifecycle methods
        if method_name in self.react_patterns['lifecycle_methods']:
            return ValidationResult(
                status=ValidationStatus.VALID,
                confidence=0.90,
                message=f"Valid React lifecycle method: {method_name}",
                details={'framework': 'react', 'type': 'lifecycle'}
            )
        
        # Check for potential typos in React hooks
        react_hooks = self.known_libraries['react']['hooks']
        for hook in react_hooks:
            if self._calculate_similarity(method_name, hook) > 0.8:
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    confidence=0.7,
                    message=f"Possible typo in React hook: {method_name}",
                    details={'type': 'potential_typo'},
                    suggestions=[f'Did you mean {hook}?']
                )
        
        return ValidationResult(
            status=ValidationStatus.UNCERTAIN,
            confidence=0.3,
            message=f"Unknown method: {method_name}",
            details={'method': method_name, 'object': object_name}
        )
    
    async def _validate_function_call(self, function_call: FunctionCall) -> ValidationResult:
        """Validate a function call"""
        function_name = function_call.function_name
        
        # Check React functions
        if function_name in self.known_libraries['react']['methods']:
            return ValidationResult(
                status=ValidationStatus.VALID,
                confidence=0.95,
                message=f"Valid React function: {function_name}",
                details={'framework': 'react', 'type': 'function'}
            )
        
        # Check global functions
        global_functions = ['setTimeout', 'clearTimeout', 'setInterval', 'clearInterval']
        if function_name in global_functions:
            return ValidationResult(
                status=ValidationStatus.VALID,
                confidence=0.95,
                message=f"Valid global function: {function_name}",
                details={'type': 'global_function'}
            )
        
        # Check if it's a React component (capitalized)
        if function_name[0].isupper():
            return ValidationResult(
                status=ValidationStatus.UNCERTAIN,
                confidence=0.6,
                message=f"Possible React component: {function_name}",
                details={'type': 'possible_component'},
                suggestions=['Verify this component is defined or imported']
            )
        
        return ValidationResult(
            status=ValidationStatus.UNCERTAIN,
            confidence=0.4,
            message=f"Unknown function: {function_name}",
            details={'function': function_name}
        )
    
    async def _validate_class_instantiation(self, class_inst: ClassInstantiation) -> ValidationResult:
        """Validate a class instantiation"""
        class_name = class_inst.class_name
        
        # Check built-in JavaScript classes
        builtin_classes = ['Date', 'Array', 'Object', 'Promise', 'Map', 'Set', 'Error']
        if class_name in builtin_classes:
            return ValidationResult(
                status=ValidationStatus.VALID,
                confidence=0.95,
                message=f"Valid JavaScript built-in class: {class_name}",
                details={'type': 'builtin_class'}
            )
        
        # Check DOM classes
        dom_classes = ['Element', 'HTMLElement', 'Document', 'XMLHttpRequest']
        if class_name in dom_classes:
            return ValidationResult(
                status=ValidationStatus.VALID,
                confidence=0.90,
                message=f"Valid DOM class: {class_name}",
                details={'type': 'dom_class'}
            )
        
        return ValidationResult(
            status=ValidationStatus.UNCERTAIN,
            confidence=0.5,
            message=f"Unknown class: {class_name}",
            details={'class': class_name}
        )
    
    async def _validate_attribute_access(self, attr_access: AttributeAccess) -> ValidationResult:
        """Validate an attribute access"""
        attr_name = attr_access.attribute_name
        object_name = attr_access.object_name
        
        # Check global object properties
        if object_name in self.js_patterns['global_objects']:
            # Common properties for each global object
            common_props = {
                'window': ['location', 'document', 'localStorage', 'sessionStorage'],
                'document': ['body', 'head', 'title', 'cookie'],
                'console': ['log', 'error', 'warn', 'info'],
                'localStorage': ['getItem', 'setItem', 'removeItem', 'clear'],
                'sessionStorage': ['getItem', 'setItem', 'removeItem', 'clear']
            }
            
            if attr_name in common_props.get(object_name, []):
                return ValidationResult(
                    status=ValidationStatus.VALID,
                    confidence=0.90,
                    message=f"Valid {object_name} property: {attr_name}",
                    details={'type': 'global_property'}
                )
        
        return ValidationResult(
            status=ValidationStatus.UNCERTAIN,
            confidence=0.4,
            message=f"Unknown attribute: {attr_name}",
            details={'attribute': attr_name, 'object': object_name}
        )
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity (simple Levenshtein distance)"""
        if not str1 or not str2:
            return 0.0
        
        # Simple similarity based on common characters
        common_chars = set(str1.lower()) & set(str2.lower())
        max_len = max(len(str1), len(str2))
        
        if max_len == 0:
            return 1.0
        
        return len(common_chars) / max_len
    
    def _detect_hallucinations(self, all_validations: List[TSValidationResult]) -> List[Dict[str, Any]]:
        """Detect hallucinations from validation results"""
        hallucinations = []
        
        for validation in all_validations:
            if validation.validation.status == ValidationStatus.INVALID:
                item = validation.item_info
                
                if isinstance(item, MethodCall):
                    hallucinations.append({
                        'type': 'INVALID_METHOD_CALL',
                        'location': f"Line {item.line_number}",
                        'description': f"Method '{item.method_name}' may not exist on '{item.object_name}'",
                        'severity': 'high',
                        'suggestion': validation.validation.suggestions[0] if validation.validation.suggestions else None
                    })
                elif isinstance(item, FunctionCall):
                    hallucinations.append({
                        'type': 'INVALID_FUNCTION_CALL',
                        'location': f"Line {item.line_number}",
                        'description': f"Function '{item.function_name}' may not exist",
                        'severity': 'high',
                        'suggestion': validation.validation.suggestions[0] if validation.validation.suggestions else None
                    })
                elif isinstance(item, ImportInfo):
                    hallucinations.append({
                        'type': 'INVALID_IMPORT',
                        'location': f"Line {item.line_number}",
                        'description': f"Import '{item.module}' may not exist",
                        'severity': 'medium',
                        'suggestion': validation.validation.suggestions[0] if validation.validation.suggestions else None
                    })
        
        return hallucinations

# Helper function for MCP integration
async def validate_ts_script(script_path: str) -> TSScriptValidationResult:
    """
    Convenience function to analyze and validate a TypeScript/JavaScript script
    
    Args:
        script_path: Path to the script file
        
    Returns:
        TSScriptValidationResult with validation results
    """
    analyzer = TSScriptAnalyzer()
    analysis_result = analyzer.analyze_script(script_path)
    
    validator = TSKnowledgeGraphValidator()
    validation_result = await validator.validate_script(analysis_result)
    
    return validation_result