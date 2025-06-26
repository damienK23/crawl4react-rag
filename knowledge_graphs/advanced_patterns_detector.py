"""
Détecteur de Patterns Avancés pour Validation

Ce module détecte des patterns complexes souvent source d'erreurs:
🔍 Patterns d'imports incohérents
🔍 Utilisations de this dans les composants fonctionnels
🔍 Hooks appelés conditionnellement
🔍 Props non destructurées/destructurées incorrectement
🔍 State mutations directes
🔍 Effets sans nettoyage
🔍 Memory leaks potentielles
🔍 Anti-patterns React/TypeScript
🔍 Problèmes de performance
🔍 Sécurité (XSS, injections)
"""

import re
import ast
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Set, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types de patterns détectés"""
    IMPORT_INCONSISTENCY = "IMPORT_INCONSISTENCY"
    HOOK_VIOLATION = "HOOK_VIOLATION"
    PERFORMANCE_ISSUE = "PERFORMANCE_ISSUE"
    SECURITY_RISK = "SECURITY_RISK"
    ANTI_PATTERN = "ANTI_PATTERN"
    MEMORY_LEAK = "MEMORY_LEAK"
    TYPE_SAFETY = "TYPE_SAFETY"
    ACCESSIBILITY = "ACCESSIBILITY"


@dataclass
class PatternDetection:
    """Détection de pattern problématique"""
    pattern_type: PatternType
    severity: str
    rule_name: str
    message: str
    location: str
    line_number: int
    confidence: float
    fix_suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    references: List[str] = field(default_factory=list)


class AdvancedPatternsDetector:
    """Détecteur de patterns avancés"""
    
    def __init__(self):
        # Règles de détection
        self.rules = {
            # Règles React Hooks
            'hooks_conditional': {
                'pattern': r'if\s*\([^)]+\)\s*{\s*use[A-Z]\w*\(',
                'type': PatternType.HOOK_VIOLATION,
                'severity': 'CRITICAL',
                'message': 'React hooks cannot be called conditionally',
                'fix': 'Move hook call outside conditional or use conditional logic inside hook'
            },
            'hooks_in_loop': {
                'pattern': r'(for|while)\s*\([^)]+\)\s*{[^}]*use[A-Z]\w*\(',
                'type': PatternType.HOOK_VIOLATION,
                'severity': 'CRITICAL',
                'message': 'React hooks cannot be called inside loops',
                'fix': 'Move hook call outside loop or restructure logic'
            },
            'hooks_in_function': {
                'pattern': r'function\s+\w+\s*\([^)]*\)\s*{[^}]*use[A-Z]\w*\(',
                'type': PatternType.HOOK_VIOLATION,
                'severity': 'HIGH',
                'message': 'React hooks should only be called in components or custom hooks',
                'fix': 'Move to component or create custom hook'
            },
            
            # Règles de performance
            'inline_object_prop': {
                'pattern': r'(\w+)=\{\{[^}]+\}\}',
                'type': PatternType.PERFORMANCE_ISSUE,
                'severity': 'MEDIUM',
                'message': 'Inline object creation causes unnecessary re-renders',
                'fix': 'Move object creation outside render or use useMemo'
            },
            'inline_function_prop': {
                'pattern': r'(\w+)=\{[^}]*=>[^}]*\}',
                'type': PatternType.PERFORMANCE_ISSUE,
                'severity': 'MEDIUM',
                'message': 'Inline function creation causes unnecessary re-renders',
                'fix': 'Use useCallback or move function outside component'
            },
            'missing_key_prop': {
                'pattern': r'\.map\s*\([^)]+\)\s*=>\s*<\w+(?![^>]*key=)',
                'type': PatternType.PERFORMANCE_ISSUE,
                'severity': 'HIGH',
                'message': 'Missing key prop in list rendering',
                'fix': 'Add unique key prop to each list item'
            },
            
            # Règles de sécurité
            'dangerous_html': {
                'pattern': r'dangerouslySetInnerHTML\s*=\s*\{\{[^}]*\}\}',
                'type': PatternType.SECURITY_RISK,
                'severity': 'HIGH',
                'message': 'Potential XSS vulnerability with dangerouslySetInnerHTML',
                'fix': 'Sanitize HTML content or use safer alternatives'
            },
            'eval_usage': {
                'pattern': r'\beval\s*\(',
                'type': PatternType.SECURITY_RISK,
                'severity': 'CRITICAL',
                'message': 'Use of eval() is dangerous and should be avoided',
                'fix': 'Use safer alternatives like JSON.parse() or proper parsing'
            },
            'document_write': {
                'pattern': r'document\.write\s*\(',
                'type': PatternType.SECURITY_RISK,
                'severity': 'HIGH',
                'message': 'document.write can cause security issues',
                'fix': 'Use modern DOM manipulation methods'
            },
            
            # Règles de state mutation
            'direct_state_mutation': {
                'pattern': r'(\w+)\.push\s*\(|(\w+)\.pop\s*\(|(\w+)\[\d+\]\s*=',
                'type': PatternType.ANTI_PATTERN,
                'severity': 'HIGH',
                'message': 'Direct state mutation detected',
                'fix': 'Use immutable update patterns or setState callback'
            },
            
            # Règles de memory leaks
            'missing_cleanup': {
                'pattern': r'useEffect\s*\([^,]+,\s*\[\]\s*\)[^}]*setTimeout|setInterval',
                'type': PatternType.MEMORY_LEAK,
                'severity': 'HIGH',
                'message': 'Potential memory leak - missing cleanup in useEffect',
                'fix': 'Return cleanup function from useEffect'
            },
            'event_listener_leak': {
                'pattern': r'addEventListener\s*\([^)]+\)(?![^}]*removeEventListener)',
                'type': PatternType.MEMORY_LEAK,
                'severity': 'MEDIUM',
                'message': 'Event listener added without cleanup',
                'fix': 'Remove event listener in cleanup function'
            },
            
            # Règles d'imports
            'unused_import': {
                'pattern': r'import\s+\{([^}]+)\}\s+from',
                'type': PatternType.IMPORT_INCONSISTENCY,
                'severity': 'LOW',
                'message': 'Potentially unused import',
                'fix': 'Remove unused imports'
            },
            'relative_import_depth': {
                'pattern': r'from\s+[\'"](\.\./){3,}',
                'type': PatternType.IMPORT_INCONSISTENCY,
                'severity': 'MEDIUM',
                'message': 'Deep relative import path',
                'fix': 'Consider using absolute imports or path mapping'
            },
            
            # Règles TypeScript
            'any_type_usage': {
                'pattern': r':\s*any\b',
                'type': PatternType.TYPE_SAFETY,
                'severity': 'MEDIUM',
                'message': 'Usage of "any" type reduces type safety',
                'fix': 'Use specific types or unknown instead of any'
            },
            'non_null_assertion': {
                'pattern': r'\w+!\.|\w+!\[',
                'type': PatternType.TYPE_SAFETY,
                'severity': 'MEDIUM',
                'message': 'Non-null assertion operator used',
                'fix': 'Add proper null checks or use optional chaining'
            },
            
            # Règles d'accessibilité
            'missing_alt_text': {
                'pattern': r'<img(?![^>]*alt=)[^>]*>',
                'type': PatternType.ACCESSIBILITY,
                'severity': 'MEDIUM',
                'message': 'Image missing alt attribute',
                'fix': 'Add alt attribute for accessibility'
            },
            'missing_aria_label': {
                'pattern': r'<button(?![^>]*aria-label=)(?![^>]*>.*?</button>)[^>]*/>',
                'type': PatternType.ACCESSIBILITY,
                'severity': 'LOW',
                'message': 'Button without accessible label',
                'fix': 'Add aria-label or text content'
            }
        }
        
        # Patterns complexes nécessitant une analyse contextuelle
        self.complex_patterns = {
            'component_this_usage': self._detect_this_in_functional_component,
            'state_mutation_complex': self._detect_complex_state_mutation,
            'effect_dependencies': self._detect_missing_effect_dependencies,
            'prop_drilling': self._detect_prop_drilling,
            'unused_variables': self._detect_unused_variables,
            'cyclic_dependencies': self._detect_cyclic_dependencies
        }
    
    def detect_patterns(self, content: str, file_path: str) -> List[PatternDetection]:
        """Détecter tous les patterns problématiques"""
        detections = []
        lines = content.split('\n')
        
        # 1. Détection par regex
        detections.extend(self._detect_regex_patterns(content, lines, file_path))
        
        # 2. Détection de patterns complexes
        detections.extend(self._detect_complex_patterns(content, lines, file_path))
        
        # 3. Analyse contextuelle
        detections.extend(self._analyze_context_patterns(content, file_path))
        
        return detections
    
    def _detect_regex_patterns(self, content: str, lines: List[str], file_path: str) -> List[PatternDetection]:
        """Détecter les patterns avec des regex simples"""
        detections = []
        
        for rule_name, rule in self.rules.items():
            pattern = rule['pattern']
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                # Trouver le numéro de ligne
                line_number = content[:match.start()].count('\n') + 1
                line_content = lines[line_number - 1] if line_number <= len(lines) else ""
                
                detection = PatternDetection(
                    pattern_type=rule['type'],
                    severity=rule['severity'],
                    rule_name=rule_name,
                    message=rule['message'],
                    location=f"{file_path}:{line_number}",
                    line_number=line_number,
                    confidence=0.8,
                    fix_suggestion=rule.get('fix'),
                    code_snippet=line_content.strip()
                )
                detections.append(detection)
        
        return detections
    
    def _detect_complex_patterns(self, content: str, lines: List[str], file_path: str) -> List[PatternDetection]:
        """Détecter les patterns complexes"""
        detections = []
        
        for pattern_name, detector_func in self.complex_patterns.items():
            try:
                pattern_detections = detector_func(content, lines, file_path)
                detections.extend(pattern_detections)
            except Exception as e:
                logger.debug(f"Error in complex pattern detection {pattern_name}: {e}")
        
        return detections
    
    def _detect_this_in_functional_component(self, content: str, lines: List[str], file_path: str) -> List[PatternDetection]:
        """Détecter l'usage de 'this' dans les composants fonctionnels"""
        detections = []
        
        # Détecter les composants fonctionnels
        func_components = re.finditer(r'(const|function)\s+([A-Z]\w*)\s*[=:].*?\([^)]*\)\s*=>', content)
        
        for comp_match in func_components:
            comp_start = comp_match.start()
            comp_name = comp_match.group(2)
            
            # Chercher l'usage de 'this' après le début du composant
            remaining_content = content[comp_start:]
            this_matches = re.finditer(r'\bthis\b', remaining_content)
            
            for this_match in this_matches:
                actual_pos = comp_start + this_match.start()
                line_number = content[:actual_pos].count('\n') + 1
                
                detections.append(PatternDetection(
                    pattern_type=PatternType.ANTI_PATTERN,
                    severity='HIGH',
                    rule_name='this_in_functional_component',
                    message=f"Usage of 'this' in functional component '{comp_name}'",
                    location=f"{file_path}:{line_number}",
                    line_number=line_number,
                    confidence=0.9,
                    fix_suggestion="Remove 'this' - not available in functional components",
                    code_snippet=lines[line_number - 1].strip() if line_number <= len(lines) else ""
                ))
        
        return detections
    
    def _detect_complex_state_mutation(self, content: str, lines: List[str], file_path: str) -> List[PatternDetection]:
        """Détecter les mutations d'état complexes"""
        detections = []
        
        # Détecter les patterns comme: state.something = value dans React
        state_mutations = re.finditer(r'(\w+)\.([\w\[\]\.]+)\s*=\s*[^=]', content)
        
        for mutation in state_mutations:
            variable_name = mutation.group(1)
            line_number = content[:mutation.start()].count('\n') + 1
            
            # Vérifier si c'est potentiellement un state React
            if self._looks_like_react_state(variable_name, content):
                detections.append(PatternDetection(
                    pattern_type=PatternType.ANTI_PATTERN,
                    severity='HIGH',
                    rule_name='complex_state_mutation',
                    message=f"Potential direct state mutation: {mutation.group(0)}",
                    location=f"{file_path}:{line_number}",
                    line_number=line_number,
                    confidence=0.7,
                    fix_suggestion="Use setState or state setter function for immutable updates",
                    code_snippet=lines[line_number - 1].strip() if line_number <= len(lines) else ""
                ))
        
        return detections
    
    def _detect_missing_effect_dependencies(self, content: str, lines: List[str], file_path: str) -> List[PatternDetection]:
        """Détecter les dépendances manquantes dans useEffect"""
        detections = []
        
        # Trouver tous les useEffect
        effect_pattern = r'useEffect\s*\(\s*\(\s*\)\s*=>\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}\s*,\s*\[([^\]]*)\]\s*\)'
        effects = re.finditer(effect_pattern, content, re.DOTALL)
        
        for effect in effects:
            effect_body = effect.group(1)
            deps_list = effect.group(2).strip()
            line_number = content[:effect.start()].count('\n') + 1
            
            # Extraire les variables utilisées dans l'effet
            used_vars = set(re.findall(r'\b(\w+)\b', effect_body))
            
            # Extraire les dépendances déclarées
            declared_deps = set()
            if deps_list:
                declared_deps = set(re.findall(r'\b(\w+)\b', deps_list))
            
            # Chercher les variables potentiellement manquantes
            potential_missing = used_vars - declared_deps - {'console', 'document', 'window'}
            
            if potential_missing:
                detections.append(PatternDetection(
                    pattern_type=PatternType.HOOK_VIOLATION,
                    severity='MEDIUM',
                    rule_name='missing_effect_dependencies',
                    message=f"Potentially missing dependencies in useEffect: {', '.join(potential_missing)}",
                    location=f"{file_path}:{line_number}",
                    line_number=line_number,
                    confidence=0.6,
                    fix_suggestion=f"Add missing dependencies: [{', '.join(sorted(potential_missing))}]",
                    code_snippet=lines[line_number - 1].strip() if line_number <= len(lines) else ""
                ))
        
        return detections
    
    def _detect_prop_drilling(self, content: str, lines: List[str], file_path: str) -> List[PatternDetection]:
        """Détecter le prop drilling excessif"""
        detections = []
        
        # Analyser les props passées à travers plusieurs niveaux
        # Simplifié pour l'exemple
        prop_passages = re.finditer(r'(\w+)=\{(\w+)\}', content)
        prop_usage = {}
        
        for passage in prop_passages:
            prop_name = passage.group(2)
            prop_usage[prop_name] = prop_usage.get(prop_name, 0) + 1
        
        # Détecter les props passées trop souvent (indicateur de prop drilling)
        for prop_name, count in prop_usage.items():
            if count > 3:  # Seuil arbitraire
                detections.append(PatternDetection(
                    pattern_type=PatternType.ANTI_PATTERN,
                    severity='LOW',
                    rule_name='prop_drilling',
                    message=f"Potential prop drilling detected for '{prop_name}' (passed {count} times)",
                    location=f"{file_path}",
                    line_number=1,
                    confidence=0.5,
                    fix_suggestion="Consider using Context API or state management library",
                    references=[f"Prop '{prop_name}' usage pattern analysis"]
                ))
        
        return detections
    
    def _detect_unused_variables(self, content: str, lines: List[str], file_path: str) -> List[PatternDetection]:
        """Détecter les variables inutilisées"""
        detections = []
        
        # Extraire les déclarations de variables
        var_declarations = re.finditer(r'(?:const|let|var)\s+(\w+)', content)
        declared_vars = set()
        var_lines = {}
        
        for decl in var_declarations:
            var_name = decl.group(1)
            declared_vars.add(var_name)
            var_lines[var_name] = content[:decl.start()].count('\n') + 1
        
        # Extraire les utilisations de variables
        var_usages = re.finditer(r'\b(\w+)\b', content)
        used_vars = set()
        
        for usage in var_usages:
            used_vars.add(usage.group(1))
        
        # Trouver les variables non utilisées
        unused_vars = declared_vars - used_vars
        
        for var_name in unused_vars:
            if not var_name.startswith('_'):  # Convention pour variables intentionnellement inutilisées
                line_number = var_lines.get(var_name, 1)
                detections.append(PatternDetection(
                    pattern_type=PatternType.IMPORT_INCONSISTENCY,
                    severity='LOW',
                    rule_name='unused_variable',
                    message=f"Variable '{var_name}' is declared but never used",
                    location=f"{file_path}:{line_number}",
                    line_number=line_number,
                    confidence=0.8,
                    fix_suggestion=f"Remove unused variable or prefix with underscore: _{var_name}",
                    code_snippet=lines[line_number - 1].strip() if line_number <= len(lines) else ""
                ))
        
        return detections
    
    def _detect_cyclic_dependencies(self, content: str, lines: List[str], file_path: str) -> List[PatternDetection]:
        """Détecter les dépendances cycliques potentielles"""
        # Analyse simplifiée des imports
        detections = []
        
        imports = re.finditer(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', content)
        relative_imports = []
        
        for imp in imports:
            module_path = imp.group(1)
            if module_path.startswith('.'):
                line_number = content[:imp.start()].count('\n') + 1
                relative_imports.append({
                    'path': module_path,
                    'line': line_number
                })
        
        # Détecter les imports relatifs qui pourraient créer des cycles
        # (analyse simplifiée)
        if len(relative_imports) > 5:
            detections.append(PatternDetection(
                pattern_type=PatternType.IMPORT_INCONSISTENCY,
                severity='MEDIUM',
                rule_name='potential_cyclic_dependency',
                message=f"High number of relative imports ({len(relative_imports)}) may indicate architectural issues",
                location=f"{file_path}",
                line_number=1,
                confidence=0.4,
                fix_suggestion="Consider restructuring modules to reduce coupling",
                references=[f"Found {len(relative_imports)} relative imports"]
            ))
        
        return detections
    
    def _analyze_context_patterns(self, content: str, file_path: str) -> List[PatternDetection]:
        """Analyser les patterns nécessitant une compréhension du contexte"""
        detections = []
        
        # Analyser les patterns React spécifiques
        detections.extend(self._analyze_react_patterns(content, file_path))
        
        # Analyser les patterns TypeScript spécifiques
        detections.extend(self._analyze_typescript_patterns(content, file_path))
        
        # Analyser les patterns de performance
        detections.extend(self._analyze_performance_patterns(content, file_path))
        
        return detections
    
    def _analyze_react_patterns(self, content: str, file_path: str) -> List[PatternDetection]:
        """Analyser les patterns React spécifiques"""
        detections = []
        
        # Détecter les composants sans memo pour les props complexes
        components = re.finditer(r'const\s+([A-Z]\w*)\s*=.*?\(([^)]*)\)', content)
        
        for comp in components:
            comp_name = comp.group(1)
            props_str = comp.group(2)
            
            # Si les props sont complexes et le composant n'est pas mémoïsé
            if len(props_str) > 50 and 'memo(' not in content:
                line_number = content[:comp.start()].count('\n') + 1
                detections.append(PatternDetection(
                    pattern_type=PatternType.PERFORMANCE_ISSUE,
                    severity='LOW',
                    rule_name='missing_memo',
                    message=f"Component '{comp_name}' with complex props should consider using React.memo",
                    location=f"{file_path}:{line_number}",
                    line_number=line_number,
                    confidence=0.5,
                    fix_suggestion="Wrap component with React.memo() if props don't change frequently"
                ))
        
        return detections
    
    def _analyze_typescript_patterns(self, content: str, file_path: str) -> List[PatternDetection]:
        """Analyser les patterns TypeScript spécifiques"""
        detections = []
        
        # Détecter les interfaces vides
        empty_interfaces = re.finditer(r'interface\s+(\w+)\s*\{\s*\}', content)
        
        for interface in empty_interfaces:
            interface_name = interface.group(1)
            line_number = content[:interface.start()].count('\n') + 1
            
            detections.append(PatternDetection(
                pattern_type=PatternType.TYPE_SAFETY,
                severity='LOW',
                rule_name='empty_interface',
                message=f"Empty interface '{interface_name}' provides no type safety",
                location=f"{file_path}:{line_number}",
                line_number=line_number,
                confidence=0.9,
                fix_suggestion="Add properties to interface or use type alias instead"
            ))
        
        return detections
    
    def _analyze_performance_patterns(self, content: str, file_path: str) -> List[PatternDetection]:
        """Analyser les patterns de performance"""
        detections = []
        
        # Détecter les re-renders inutiles
        inline_styles = re.finditer(r'style=\{\{[^}]+\}\}', content)
        
        for style in inline_styles:
            line_number = content[:style.start()].count('\n') + 1
            detections.append(PatternDetection(
                pattern_type=PatternType.PERFORMANCE_ISSUE,
                severity='LOW',
                rule_name='inline_styles',
                message="Inline styles cause component re-renders",
                location=f"{file_path}:{line_number}",
                line_number=line_number,
                confidence=0.7,
                fix_suggestion="Move styles to CSS classes or use styled-components"
            ))
        
        return detections
    
    def _looks_like_react_state(self, variable_name: str, content: str) -> bool:
        """Vérifier si une variable ressemble à du state React"""
        # Rechercher des patterns comme useState, this.state, etc.
        state_patterns = [
            rf'{variable_name}\s*=\s*useState\(',
            rf'const\s+\[{variable_name},',
            rf'this\.state\.{variable_name}',
            rf'{variable_name}\s*=\s*this\.state'
        ]
        
        for pattern in state_patterns:
            if re.search(pattern, content):
                return True
        
        return False


# Fonction utilitaire
def detect_advanced_patterns(file_path: str, content: str) -> List[PatternDetection]:
    """Détecter tous les patterns avancés dans un fichier"""
    detector = AdvancedPatternsDetector()
    return detector.detect_patterns(content, file_path)


if __name__ == "__main__":
    # Test
    test_content = """
    import React, { useState, useEffect } from 'react';
    
    const MyComponent = ({ data }) => {
        const [state, setState] = useState([]);
        
        if (data.length > 0) {
            const [count, setCount] = useState(0); // Erreur: hook conditionnel
        }
        
        useEffect(() => {
            const timer = setTimeout(() => {
                console.log('Timer executed');
            }, 1000);
            // Pas de nettoyage - memory leak
        }, []);
        
        const handleClick = () => {
            state.push(newItem); // Mutation directe
            setState(state);
        };
        
        return (
            <div>
                {data.map(item => (
                    <div onClick={() => handleClick(item)}> {/* Pas de key, fonction inline */}
                        {item.name}
                    </div>
                ))}
                <img src="test.jpg" /> {/* Pas d'alt */}
            </div>
        );
    };
    """
    
    detections = detect_advanced_patterns("test.tsx", test_content)
    
    for detection in detections:
        print(f"{detection.severity}: {detection.message}")
        print(f"  Location: {detection.location}")
        print(f"  Fix: {detection.fix_suggestion}")
        print()