"""
Validateur IA Complet pour Détection d'Hallucinations

Ce module implémente un validateur complet qui combine:
- Analyseur React/TypeScript pour composants, hooks, types
- Analyseur Supabase pour schéma de base de données
- Base de connaissances Neo4j pour validation
- Détection d'hallucinations avec IA avancée

Détections possibles:
❌ Composants React inexistants
❌ Hooks personnalisés introuvables
❌ Tables Supabase qui n'existent pas
❌ Fonctions RPC Supabase inexistantes
❌ Signatures incorrectes
❌ Types TypeScript invalides
⚠️ Mauvaises pratiques
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Set, Any, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime, timezone
from enum import Enum

from .typescript_analyzer import TypeScriptAnalyzer, AnalysisResult
from .supabase_analyzer import SupabaseAnalyzer, SupabaseSchemaInfo
from .parse_repo_into_neo4j import DirectNeo4jExtractor
from .ts_knowledge_graph_validator import TSKnowledgeGraphValidator, TSScriptValidationResult, ValidationStatus
from .signature_validator import SignatureValidator, ValidationIssue as SignatureIssue
from .advanced_patterns_detector import AdvancedPatternsDetector, PatternDetection
from .rpc_parameter_validator import RPCParameterValidator, ParameterValidationError, parse_rpc_parameters

logger = logging.getLogger(__name__)


class DetectionType(Enum):
    """Types de détections possibles"""
    COMPONENT_NOT_FOUND = "COMPONENT_NOT_FOUND"
    HOOK_NOT_FOUND = "HOOK_NOT_FOUND"
    SUPABASE_TABLE_NOT_FOUND = "SUPABASE_TABLE_NOT_FOUND"
    SUPABASE_FUNCTION_NOT_FOUND = "SUPABASE_FUNCTION_NOT_FOUND"
    RPC_PARAMETER_TYPE_MISMATCH = "RPC_PARAMETER_TYPE_MISMATCH"
    RPC_MISSING_REQUIRED_PARAM = "RPC_MISSING_REQUIRED_PARAM"
    RPC_INVALID_ENUM_VALUE = "RPC_INVALID_ENUM_VALUE"
    RPC_INVALID_JSON_STRUCTURE = "RPC_INVALID_JSON_STRUCTURE"
    RPC_PARAMETER_COUNT_MISMATCH = "RPC_PARAMETER_COUNT_MISMATCH"
    INCORRECT_SIGNATURE = "INCORRECT_SIGNATURE"
    INVALID_TYPE = "INVALID_TYPE"
    BAD_PRACTICE = "BAD_PRACTICE"
    IMPORT_NOT_FOUND = "IMPORT_NOT_FOUND"
    METHOD_NOT_FOUND = "METHOD_NOT_FOUND"
    ATTRIBUTE_NOT_FOUND = "ATTRIBUTE_NOT_FOUND"


class Severity(Enum):
    """Niveaux de sévérité"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class Detection:
    """Une détection d'hallucination ou de problème"""
    type: DetectionType
    severity: Severity
    message: str
    location: str
    line_number: int
    confidence: float
    suggestion: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Rapport complet de validation"""
    script_path: str
    language: str
    analysis_timestamp: datetime
    overall_confidence: float
    detections: List[Detection] = field(default_factory=list)
    frameworks_detected: List[str] = field(default_factory=list)
    supabase_info: Optional[Dict[str, Any]] = None
    statistics: Dict[str, int] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class ComprehensiveValidator:
    """Validateur complet avec toutes les fonctionnalités"""
    
    def __init__(self, neo4j_uri: str = None, neo4j_user: str = None, neo4j_password: str = None,
                 supabase_url: str = None, supabase_key: str = None):
        self.neo4j_extractor = None
        self.ts_validator = None
        self.supabase_analyzer = None
        self.supabase_schema = None
        
        # Initialize Neo4j if credentials provided
        if neo4j_uri and neo4j_user and neo4j_password:
            self.neo4j_extractor = DirectNeo4jExtractor(neo4j_uri, neo4j_user, neo4j_password)
            self.ts_validator = TSKnowledgeGraphValidator(neo4j_uri, neo4j_user, neo4j_password)
        
        # Initialize Supabase if credentials provided
        self.rpc_validator = None
        if supabase_url and supabase_key:
            self.supabase_analyzer = SupabaseAnalyzer(supabase_url, supabase_key)
        
        # Initialize additional validators
        self.signature_validator = SignatureValidator()
        self.patterns_detector = AdvancedPatternsDetector()
        
        # React/JavaScript patterns for validation
        self.react_patterns = {
            'hooks': {
                'useState': {'returns': 'array', 'args': ['initialValue?']},
                'useEffect': {'returns': 'void', 'args': ['effect', 'deps?']},
                'useContext': {'returns': 'any', 'args': ['context']},
                'useReducer': {'returns': 'array', 'args': ['reducer', 'initialState', 'init?']},
                'useCallback': {'returns': 'function', 'args': ['callback', 'deps']},
                'useMemo': {'returns': 'any', 'args': ['factory', 'deps']},
                'useRef': {'returns': 'RefObject', 'args': ['initialValue?']},
                'useImperativeHandle': {'returns': 'void', 'args': ['ref', 'createHandle', 'deps?']},
                'useLayoutEffect': {'returns': 'void', 'args': ['effect', 'deps?']},
                'useDebugValue': {'returns': 'void', 'args': ['value', 'format?']},
                'useDeferredValue': {'returns': 'any', 'args': ['value']},
                'useTransition': {'returns': 'array', 'args': []},
                'useId': {'returns': 'string', 'args': []}
            },
            'component_props': {
                'required_patterns': ['children?', 'className?', 'style?'],
                'react_props': ['key', 'ref', 'dangerouslySetInnerHTML']
            },
            'lifecycle_methods': {
                'componentDidMount', 'componentDidUpdate', 'componentWillUnmount',
                'shouldComponentUpdate', 'getSnapshotBeforeUpdate', 'componentDidCatch'
            }
        }
        
        # Common framework patterns
        self.framework_signatures = {
            'next': {
                'getServerSideProps': {'returns': 'GetServerSidePropsResult', 'args': ['context']},
                'getStaticProps': {'returns': 'GetStaticPropsResult', 'args': ['context']},
                'getStaticPaths': {'returns': 'GetStaticPathsResult', 'args': []},
                'getInitialProps': {'returns': 'any', 'args': ['context']}
            },
            'express': {
                'app.get': {'returns': 'void', 'args': ['path', 'handler']},
                'app.post': {'returns': 'void', 'args': ['path', 'handler']},
                'app.put': {'returns': 'void', 'args': ['path', 'handler']},
                'app.delete': {'returns': 'void', 'args': ['path', 'handler']},
                'app.use': {'returns': 'void', 'args': ['middleware']}
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize all components"""
        success = True
        
        # Initialize Neo4j
        if self.neo4j_extractor:
            try:
                await self.neo4j_extractor.initialize()
                if self.ts_validator:
                    await self.ts_validator.initialize()
                logger.info("Neo4j components initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Neo4j: {e}")
                success = False
        
        # Initialize Supabase
        if self.supabase_analyzer:
            try:
                if self.supabase_analyzer.connect():
                    self.supabase_schema = await self.supabase_analyzer.analyze_schema()
                    # Initialize RPC parameter validator
                    self.rpc_validator = RPCParameterValidator(self.supabase_schema)
                    logger.info(f"Supabase schema loaded: {len(self.supabase_schema.tables)} tables, {len(self.supabase_schema.functions)} functions")
                else:
                    logger.error("Failed to connect to Supabase")
                    success = False
            except Exception as e:
                logger.error(f"Failed to initialize Supabase: {e}")
                success = False
        
        return success
    
    async def validate_script(self, script_path: str) -> ValidationReport:
        """Validation complète d'un script TypeScript/JavaScript"""
        logger.info(f"Starting comprehensive validation of: {script_path}")
        
        report = ValidationReport(
            script_path=script_path,
            language=self._detect_language(script_path),
            analysis_timestamp=datetime.now(timezone.utc),
            overall_confidence=0.0
        )
        
        try:
            # 1. Analyse TypeScript/JavaScript de base
            ts_analyzer = TypeScriptAnalyzer()
            analysis = ts_analyzer.analyze_typescript_file(
                Path(script_path), Path(script_path).parent, set()
            )
            
            if not analysis:
                report.detections.append(Detection(
                    type=DetectionType.INVALID_TYPE,
                    severity=Severity.CRITICAL,
                    message="Could not parse TypeScript/JavaScript file",
                    location=script_path,
                    line_number=1,
                    confidence=1.0
                ))
                return report
            
            # 2. Détections React/Framework spécifiques
            await self._detect_react_issues(analysis, report)
            
            # 3. Validation avec Neo4j si disponible
            if self.ts_validator:
                await self._validate_with_neo4j(script_path, report)
            
            # 4. Validation Supabase si disponible
            if self.supabase_schema:
                await self._validate_supabase_usage(analysis, report)
            
            # 5. Validation des signatures complètes
            await self._validate_signatures(script_path, report)
            
            # 6. Détection de patterns avancés
            await self._detect_advanced_patterns(script_path, report)
            
            # 7. Détection de mauvaises pratiques
            await self._detect_bad_practices(analysis, report)
            
            # 8. Calcul de la confiance globale
            report.overall_confidence = self._calculate_overall_confidence(report)
            
            # 7. Génération des recommandations
            report.recommendations = self._generate_recommendations(report)
            
            # 8. Statistiques
            report.statistics = self._calculate_statistics(report)
            
            logger.info(f"Validation completed. Found {len(report.detections)} issues with {report.overall_confidence:.1%} confidence")
            
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            report.detections.append(Detection(
                type=DetectionType.INVALID_TYPE,
                severity=Severity.CRITICAL,
                message=f"Validation failed: {str(e)}",
                location=script_path,
                line_number=1,
                confidence=1.0
            ))
        
        return report
    
    async def _detect_react_issues(self, analysis: AnalysisResult, report: ValidationReport):
        """Détecter les problèmes spécifiques à React"""
        # Détecter les frameworks utilisés
        frameworks = set()
        
        for import_info in analysis.imports:
            if 'react' in import_info.module.lower():
                frameworks.add('react')
            elif 'next' in import_info.module.lower():
                frameworks.add('next')
            elif 'vue' in import_info.module.lower():
                frameworks.add('vue')
        
        report.frameworks_detected = list(frameworks)
        
        # Valider les hooks React
        await self._validate_react_hooks(analysis, report)
        
        # Valider les composants React
        await self._validate_react_components(analysis, report)
        
        # Valider les signatures de framework
        await self._validate_framework_signatures(analysis, report, frameworks)
    
    async def _validate_react_hooks(self, analysis: AnalysisResult, report: ValidationReport):
        """Valider l'utilisation des hooks React"""
        for hook_call in analysis.hook_calls:
            hook_name = hook_call.hook_name
            
            # Vérifier si c'est un hook React standard
            if hook_name in self.react_patterns['hooks']:
                expected = self.react_patterns['hooks'][hook_name]
                provided_args = len(hook_call.args)
                expected_args = len(expected['args'])
                
                # Vérifier le nombre d'arguments
                if provided_args > expected_args:
                    report.detections.append(Detection(
                        type=DetectionType.INCORRECT_SIGNATURE,
                        severity=Severity.MEDIUM,
                        message=f"Hook '{hook_name}' expects at most {expected_args} arguments, got {provided_args}",
                        location=f"line {hook_call.line_number}",
                        line_number=hook_call.line_number,
                        confidence=0.8,
                        suggestion=f"Expected signature: {hook_name}({', '.join(expected['args'])})",
                        context={'hook_name': hook_name, 'expected_args': expected['args'], 'provided_args': hook_call.args}
                    ))
            
            # Vérifier les hooks personnalisés (doivent commencer par 'use')
            elif hook_name.startswith('use') and len(hook_name) > 3:
                if hook_name[3].islower():
                    report.detections.append(Detection(
                        type=DetectionType.BAD_PRACTICE,
                        severity=Severity.LOW,
                        message=f"Custom hook '{hook_name}' should start with 'use' followed by a capital letter",
                        location=f"line {hook_call.line_number}",
                        line_number=hook_call.line_number,
                        confidence=0.9,
                        suggestion=f"Rename to 'use{hook_name[3:].capitalize()}'",
                        context={'hook_name': hook_name}
                    ))
    
    async def _validate_react_components(self, analysis: AnalysisResult, report: ValidationReport):
        """Valider les composants React"""
        for component in analysis.components:
            # Vérifier les conventions de nommage
            if not component.name[0].isupper():
                report.detections.append(Detection(
                    type=DetectionType.BAD_PRACTICE,
                    severity=Severity.MEDIUM,
                    message=f"React component '{component.name}' should start with a capital letter",
                    location=f"line {component.line_number}",
                    line_number=component.line_number,
                    confidence=0.95,
                    suggestion=f"Rename to '{component.name.capitalize()}'",
                    context={'component_name': component.name, 'component_type': component.type}
                ))
            
            # Vérifier l'utilisation des hooks dans les composants de classe
            if component.type == 'class' and component.hooks:
                report.detections.append(Detection(
                    type=DetectionType.BAD_PRACTICE,
                    severity=Severity.HIGH,
                    message=f"Class component '{component.name}' cannot use hooks",
                    location=f"line {component.line_number}",
                    line_number=component.line_number,
                    confidence=1.0,
                    suggestion="Convert to function component or use class lifecycle methods",
                    context={'component_name': component.name, 'hooks_used': component.hooks}
                ))
    
    async def _validate_framework_signatures(self, analysis: AnalysisResult, report: ValidationReport, frameworks: Set[str]):
        """Valider les signatures des fonctions de framework"""
        for func_call in analysis.function_calls:
            # Vérifier les fonctions Next.js
            if 'next' in frameworks and func_call.function_name in self.framework_signatures['next']:
                expected = self.framework_signatures['next'][func_call.function_name]
                provided_args = len(func_call.args)
                expected_args = len(expected['args'])
                
                if provided_args != expected_args:
                    report.detections.append(Detection(
                        type=DetectionType.INCORRECT_SIGNATURE,
                        severity=Severity.HIGH,
                        message=f"Next.js function '{func_call.function_name}' expects {expected_args} arguments, got {provided_args}",
                        location=f"line {func_call.line_number}",
                        line_number=func_call.line_number,
                        confidence=0.9,
                        suggestion=f"Expected signature: {func_call.function_name}({', '.join(expected['args'])})",
                        context={'function_name': func_call.function_name, 'expected': expected, 'provided_args': func_call.args}
                    ))
    
    async def _validate_with_neo4j(self, script_path: str, report: ValidationReport):
        """Valider avec la base de connaissances Neo4j"""
        try:
            if self.ts_validator:
                # Utiliser le validateur TypeScript existant
                from ts_knowledge_graph_validator import validate_ts_script
                
                ts_result = await validate_ts_script(script_path)
                
                # Convertir les résultats du validateur TS vers notre format
                for hallucination in ts_result.hallucinations_detected:
                    detection_type = self._map_ts_detection_type(hallucination['type'])
                    severity = self._map_severity(hallucination['severity'])
                    
                    report.detections.append(Detection(
                        type=detection_type,
                        severity=severity,
                        message=hallucination['description'],
                        location=hallucination['location'],
                        line_number=self._extract_line_number(hallucination['location']),
                        confidence=0.8,
                        suggestion=hallucination.get('suggestion'),
                        context={'source': 'neo4j_validator', 'original_type': hallucination['type']}
                    ))
                
        except Exception as e:
            logger.error(f"Error during Neo4j validation: {e}")
    
    async def _validate_supabase_usage(self, analysis: AnalysisResult, report: ValidationReport):
        """Valider l'utilisation de Supabase"""
        if not self.supabase_schema:
            return
        
        # Créer des maps pour recherche rapide
        table_names = {table.name for table in self.supabase_schema.tables}
        function_names = {func.name for func in self.supabase_schema.functions}
        
        # Analyser les imports Supabase
        supabase_imports = [imp for imp in analysis.imports if 'supabase' in imp.module.lower()]
        if supabase_imports:
            report.supabase_info = {
                'tables_available': list(table_names),
                'functions_available': list(function_names),
                'imports_found': [imp.module for imp in supabase_imports]
            }
        
        # Vérifier les appels de méthodes qui pourraient être des tables Supabase
        for func_call in analysis.function_calls:
            # Rechercher des patterns comme .from('table_name')
            if func_call.object_name and func_call.function_name == 'from':
                if func_call.args:
                    table_arg = func_call.args[0].strip('\'"')
                    if table_arg and table_arg not in table_names:
                        report.detections.append(Detection(
                            type=DetectionType.SUPABASE_TABLE_NOT_FOUND,
                            severity=Severity.HIGH,
                            message=f"Supabase table '{table_arg}' not found in database schema",
                            location=f"line {func_call.line_number}",
                            line_number=func_call.line_number,
                            confidence=0.85,
                            suggestion=f"Available tables: {', '.join(sorted(list(table_names)[:5]))}{'...' if len(table_names) > 5 else ''}",
                            context={'table_name': table_arg, 'available_tables': list(table_names)}
                        ))
            
            # Rechercher des patterns comme .rpc('function_name')
            elif func_call.function_name == 'rpc':
                if func_call.args:
                    func_arg = func_call.args[0].strip('\'"')
                    if func_arg and func_arg not in function_names:
                        report.detections.append(Detection(
                            type=DetectionType.SUPABASE_FUNCTION_NOT_FOUND,
                            severity=Severity.HIGH,
                            message=f"Supabase RPC function '{func_arg}' not found in database schema",
                            location=f"line {func_call.line_number}",
                            line_number=func_call.line_number,
                            confidence=0.85,
                            suggestion=f"Available functions: {', '.join(sorted(list(function_names)[:5]))}{'...' if len(function_names) > 5 else ''}",
                            context={'function_name': func_arg, 'available_functions': list(function_names)}
                        ))
                    
                    # Validation avancée des paramètres RPC si le validateur est disponible
                    elif func_arg in function_names and self.rpc_validator:
                        await self._validate_rpc_parameters(
                            analysis, func_call, func_arg, report
                        )
    
    async def _validate_rpc_parameters(self, analysis: AnalysisResult, func_call, 
                                     function_name: str, report: ValidationReport):
        """Validation avancée des paramètres RPC"""
        try:
            # Lire le contenu du fichier pour extraire les paramètres
            with open(analysis.file_path if hasattr(analysis, 'file_path') else report.script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extraire les paramètres fournis dans l'appel RPC
            provided_params = parse_rpc_parameters(content, function_name, func_call.line_number)
            
            if provided_params:
                # Valider avec le validateur RPC avancé
                param_errors = self.rpc_validator.validate_rpc_call(
                    function_name, provided_params, func_call.line_number
                )
                
                # Convertir les erreurs en détections
                for error in param_errors:
                    detection_type = self._map_rpc_validation_type(error.validation_type)
                    severity = self._map_rpc_severity(error.severity)
                    
                    report.detections.append(Detection(
                        type=detection_type,
                        severity=severity,
                        message=error.message,
                        location=f"line {error.line_number}",
                        line_number=error.line_number,
                        confidence=0.9,
                        suggestion=error.suggestion,
                        context={
                            'function_name': function_name,
                            'parameter_name': error.parameter_name,
                            'validation_type': error.validation_type.value,
                            'expected': error.expected,
                            'actual': error.actual
                        }
                    ))
        
        except Exception as e:
            logger.debug(f"Error during RPC parameter validation: {e}")
    
    def _map_rpc_validation_type(self, validation_type) -> DetectionType:
        """Mapper les types de validation RPC vers DetectionType"""
        from rpc_parameter_validator import ParameterValidationType
        
        mapping = {
            ParameterValidationType.TYPE_MISMATCH: DetectionType.RPC_PARAMETER_TYPE_MISMATCH,
            ParameterValidationType.MISSING_REQUIRED: DetectionType.RPC_MISSING_REQUIRED_PARAM,
            ParameterValidationType.INVALID_ENUM: DetectionType.RPC_INVALID_ENUM_VALUE,
            ParameterValidationType.INVALID_JSON_STRUCTURE: DetectionType.RPC_INVALID_JSON_STRUCTURE,
            ParameterValidationType.PARAMETER_COUNT_MISMATCH: DetectionType.RPC_PARAMETER_COUNT_MISMATCH,
            ParameterValidationType.OPTIONAL_NOT_PROVIDED: DetectionType.BAD_PRACTICE
        }
        
        return mapping.get(validation_type, DetectionType.INCORRECT_SIGNATURE)
    
    def _map_rpc_severity(self, severity_str: str) -> Severity:
        """Mapper les sévérités RPC"""
        mapping = {
            'CRITICAL': Severity.CRITICAL,
            'HIGH': Severity.HIGH,
            'MEDIUM': Severity.MEDIUM,
            'LOW': Severity.LOW,
            'INFO': Severity.INFO
        }
        return mapping.get(severity_str.upper(), Severity.MEDIUM)
    
    async def _validate_signatures(self, script_path: str, report: ValidationReport):
        """Valider toutes les signatures de fonction et types"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Utiliser le validateur de signatures
            signature_issues = self.signature_validator.validate_typescript_file(script_path, content)
            
            # Convertir les issues en détections
            for issue in signature_issues:
                severity = self._map_signature_severity(issue.severity)
                detection_type = self._map_signature_type(issue.type)
                
                report.detections.append(Detection(
                    type=detection_type,
                    severity=severity,
                    message=issue.message,
                    location=issue.location,
                    line_number=self._extract_line_number(issue.location),
                    confidence=0.8,
                    suggestion=issue.suggestion,
                    context={'source': 'signature_validator', 'expected': issue.expected, 'actual': issue.actual}
                ))
                
        except Exception as e:
            logger.error(f"Error during signature validation: {e}")
    
    async def _detect_advanced_patterns(self, script_path: str, report: ValidationReport):
        """Détecter les patterns avancés et anti-patterns"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Utiliser le détecteur de patterns
            pattern_detections = self.patterns_detector.detect_patterns(content, script_path)
            
            # Convertir les détections de patterns
            for pattern in pattern_detections:
                severity = self._map_pattern_severity(pattern.severity)
                detection_type = self._map_pattern_type(pattern.pattern_type)
                
                report.detections.append(Detection(
                    type=detection_type,
                    severity=severity,
                    message=pattern.message,
                    location=pattern.location,
                    line_number=pattern.line_number,
                    confidence=pattern.confidence,
                    suggestion=pattern.fix_suggestion,
                    context={
                        'source': 'patterns_detector',
                        'rule_name': pattern.rule_name,
                        'code_snippet': pattern.code_snippet,
                        'references': pattern.references
                    }
                ))
                
        except Exception as e:
            logger.error(f"Error during pattern detection: {e}")
    
    async def _detect_bad_practices(self, analysis: AnalysisResult, report: ValidationReport):
        """Détecter les mauvaises pratiques"""
        # Détecter les imports non utilisés
        imported_names = {imp.name for imp in analysis.imports if not imp.is_namespace_import}
        # Note: Une vraie détection nécessiterait une analyse plus approfondie du code
        
        # Détecter les composants sans export
        non_exported_components = [comp for comp in analysis.components if not comp.is_exported]
        for component in non_exported_components:
            if component.name[0].isupper():  # Seulement pour les vrais composants React
                report.detections.append(Detection(
                    type=DetectionType.BAD_PRACTICE,
                    severity=Severity.LOW,
                    message=f"React component '{component.name}' is not exported",
                    location=f"line {component.line_number}",
                    line_number=component.line_number,
                    confidence=0.7,
                    suggestion="Consider exporting the component if it should be reusable",
                    context={'component_name': component.name}
                ))
        
        # Détecter les fonctions avec trop de paramètres
        for component in analysis.components:
            if len(component.props) > 10:
                report.detections.append(Detection(
                    type=DetectionType.BAD_PRACTICE,
                    severity=Severity.MEDIUM,
                    message=f"Component '{component.name}' has too many props ({len(component.props)})",
                    location=f"line {component.line_number}",
                    line_number=component.line_number,
                    confidence=0.8,
                    suggestion="Consider grouping related props into objects or using composition",
                    context={'component_name': component.name, 'props_count': len(component.props)}
                ))
    
    def _detect_language(self, script_path: str) -> str:
        """Détecter le langage du script"""
        if script_path.endswith(('.ts', '.tsx')):
            return 'typescript'
        elif script_path.endswith(('.js', '.jsx')):
            return 'javascript'
        else:
            return 'unknown'
    
    def _map_ts_detection_type(self, ts_type: str) -> DetectionType:
        """Mapper les types de détection TypeScript vers notre enum"""
        mapping = {
            'INVALID_IMPORT': DetectionType.IMPORT_NOT_FOUND,
            'INVALID_METHOD_CALL': DetectionType.METHOD_NOT_FOUND,
            'INVALID_FUNCTION_CALL': DetectionType.HOOK_NOT_FOUND,
            'INVALID_ATTRIBUTE_ACCESS': DetectionType.ATTRIBUTE_NOT_FOUND,
        }
        return mapping.get(ts_type, DetectionType.INVALID_TYPE)
    
    def _map_severity(self, severity_str: str) -> Severity:
        """Mapper les chaînes de sévérité vers notre enum"""
        mapping = {
            'CRITICAL': Severity.CRITICAL,
            'HIGH': Severity.HIGH,
            'MEDIUM': Severity.MEDIUM,
            'LOW': Severity.LOW,
            'INFO': Severity.INFO
        }
        return mapping.get(severity_str.upper(), Severity.MEDIUM)
    
    def _extract_line_number(self, location: str) -> int:
        """Extraire le numéro de ligne d'une chaîne de localisation"""
        try:
            if 'line' in location:
                return int(location.split('line')[1].strip().split()[0])
            elif ':' in location:
                return int(location.split(':')[-1])
            return 1
        except:
            return 1
    
    def _map_signature_severity(self, severity: str) -> Severity:
        """Mapper les sévérités des signatures"""
        mapping = {
            'CRITICAL': Severity.CRITICAL,
            'HIGH': Severity.HIGH,
            'MEDIUM': Severity.MEDIUM,
            'LOW': Severity.LOW,
            'INFO': Severity.INFO
        }
        return mapping.get(severity.upper(), Severity.MEDIUM)
    
    def _map_signature_type(self, sig_type: str) -> DetectionType:
        """Mapper les types de validation de signature"""
        mapping = {
            'TYPE_NOT_DEFINED': DetectionType.INVALID_TYPE,
            'MISSING_ARGUMENTS': DetectionType.INCORRECT_SIGNATURE,
            'TOO_MANY_ARGUMENTS': DetectionType.INCORRECT_SIGNATURE,
            'UNUSED_TYPE': DetectionType.BAD_PRACTICE,
            'UNUSED_FUNCTION': DetectionType.BAD_PRACTICE,
            'PARSE_ERROR': DetectionType.INVALID_TYPE,
            'FILE_ERROR': DetectionType.INVALID_TYPE
        }
        return mapping.get(sig_type, DetectionType.INVALID_TYPE)
    
    def _map_pattern_severity(self, severity: str) -> Severity:
        """Mapper les sévérités des patterns"""
        mapping = {
            'CRITICAL': Severity.CRITICAL,
            'HIGH': Severity.HIGH,
            'MEDIUM': Severity.MEDIUM,
            'LOW': Severity.LOW,
            'INFO': Severity.INFO
        }
        return mapping.get(severity.upper(), Severity.MEDIUM)
    
    def _map_pattern_type(self, pattern_type) -> DetectionType:
        """Mapper les types de patterns détectés"""
        from advanced_patterns_detector import PatternType
        
        mapping = {
            PatternType.IMPORT_INCONSISTENCY: DetectionType.IMPORT_NOT_FOUND,
            PatternType.HOOK_VIOLATION: DetectionType.HOOK_NOT_FOUND,
            PatternType.PERFORMANCE_ISSUE: DetectionType.BAD_PRACTICE,
            PatternType.SECURITY_RISK: DetectionType.BAD_PRACTICE,
            PatternType.ANTI_PATTERN: DetectionType.BAD_PRACTICE,
            PatternType.MEMORY_LEAK: DetectionType.BAD_PRACTICE,
            PatternType.TYPE_SAFETY: DetectionType.INVALID_TYPE,
            PatternType.ACCESSIBILITY: DetectionType.BAD_PRACTICE
        }
        return mapping.get(pattern_type, DetectionType.BAD_PRACTICE)
    
    def _calculate_overall_confidence(self, report: ValidationReport) -> float:
        """Calculer la confiance globale du rapport"""
        if not report.detections:
            return 1.0
        
        # Pondérer par sévérité
        weights = {
            Severity.CRITICAL: 1.0,
            Severity.HIGH: 0.8,
            Severity.MEDIUM: 0.6,
            Severity.LOW: 0.4,
            Severity.INFO: 0.2
        }
        
        total_weight = sum(weights[det.severity] * det.confidence for det in report.detections)
        max_possible = len(report.detections)
        
        if max_possible == 0:
            return 1.0
        
        # Plus il y a de problèmes graves, plus la confiance diminue
        confidence = max(0.0, 1.0 - (total_weight / (max_possible * 2)))
        return confidence
    
    def _generate_recommendations(self, report: ValidationReport) -> List[str]:
        """Générer des recommandations basées sur les détections"""
        recommendations = []
        
        # Compter les types de problèmes
        type_counts = {}
        for detection in report.detections:
            type_counts[detection.type] = type_counts.get(detection.type, 0) + 1
        
        # Recommandations spécifiques
        if DetectionType.COMPONENT_NOT_FOUND in type_counts:
            recommendations.append(
                f"Found {type_counts[DetectionType.COMPONENT_NOT_FOUND]} unknown components. "
                "Verify component imports and check if they exist in your codebase."
            )
        
        if DetectionType.SUPABASE_TABLE_NOT_FOUND in type_counts:
            recommendations.append(
                f"Found {type_counts[DetectionType.SUPABASE_TABLE_NOT_FOUND]} references to non-existent Supabase tables. "
                "Update your database schema or fix table names in your code."
            )
        
        if DetectionType.INCORRECT_SIGNATURE in type_counts:
            recommendations.append(
                f"Found {type_counts[DetectionType.INCORRECT_SIGNATURE]} functions with incorrect signatures. "
                "Check framework documentation for correct function parameters."
            )
        
        if DetectionType.BAD_PRACTICE in type_counts:
            recommendations.append(
                f"Found {type_counts[DetectionType.BAD_PRACTICE]} code style issues. "
                "Consider following React and TypeScript best practices."
            )
        
        # Recommandations générales
        if 'react' in report.frameworks_detected:
            recommendations.append("Use React DevTools and ESLint React plugin for additional validation.")
            recommendations.append("Follow React Hooks rules and best practices.")
        
        if report.language == 'typescript':
            recommendations.append("Enable TypeScript strict mode for better type checking.")
        else:
            recommendations.append("Consider migrating to TypeScript for better static analysis.")
        
        if not recommendations:
            recommendations.append("No major issues detected. Code appears to follow good practices.")
        
        return recommendations
    
    def _calculate_statistics(self, report: ValidationReport) -> Dict[str, int]:
        """Calculer les statistiques du rapport"""
        stats = {
            'total_detections': len(report.detections),
            'critical_issues': sum(1 for d in report.detections if d.severity == Severity.CRITICAL),
            'high_issues': sum(1 for d in report.detections if d.severity == Severity.HIGH),
            'medium_issues': sum(1 for d in report.detections if d.severity == Severity.MEDIUM),
            'low_issues': sum(1 for d in report.detections if d.severity == Severity.LOW),
            'frameworks_detected': len(report.frameworks_detected),
        }
        
        if report.supabase_info:
            stats['supabase_tables'] = len(report.supabase_info.get('tables_available', []))
            stats['supabase_functions'] = len(report.supabase_info.get('functions_available', []))
        
        return stats
    
    async def close(self):
        """Fermer toutes les connexions"""
        if self.neo4j_extractor:
            await self.neo4j_extractor.close()
        if self.ts_validator:
            await self.ts_validator.close()


async def main():
    """Test du validateur complet"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Configuration
    neo4j_uri = os.getenv('NEO4J_URI')
    neo4j_user = os.getenv('NEO4J_USER') 
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    validator = ComprehensiveValidator(
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password,
        supabase_url=supabase_url,
        supabase_key=supabase_key
    )
    
    if await validator.initialize():
        print("Validator initialized successfully")
        
        # Test avec un fichier exemple
        test_file = "test_component.tsx"
        if os.path.exists(test_file):
            report = await validator.validate_script(test_file)
            
            print(f"\nValidation Report for {test_file}:")
            print(f"Language: {report.language}")
            print(f"Overall Confidence: {report.overall_confidence:.1%}")
            print(f"Detections: {len(report.detections)}")
            print(f"Frameworks: {', '.join(report.frameworks_detected)}")
            
            for detection in report.detections[:5]:  # Show first 5
                print(f"- {detection.severity.value}: {detection.message}")
    
    await validator.close()


if __name__ == "__main__":
    asyncio.run(main())