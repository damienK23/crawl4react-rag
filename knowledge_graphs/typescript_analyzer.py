"""
TypeScript/React Analyzer

Parses TypeScript/JavaScript files to extract:
- Import/export statements
- React component definitions
- Function declarations
- Hook usage patterns
- TypeScript type annotations
- Variable declarations and usage
"""

import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ImportInfo:
    """Information about an import statement"""
    module: str
    name: str
    alias: Optional[str] = None
    is_default_import: bool = False
    is_namespace_import: bool = False
    line_number: int = 0


@dataclass
class ComponentInfo:
    """Information about a React component"""
    name: str
    type: str  # "function" or "class" or "arrow"
    props: List[str]
    hooks: List[str]
    line_number: int
    is_exported: bool = False


@dataclass
class HookCall:
    """Information about a React hook call"""
    hook_name: str
    args: List[str]
    line_number: int
    variable_name: Optional[str] = None


@dataclass
class FunctionCall:
    """Information about a function call"""
    function_name: str
    args: List[str]
    line_number: int
    object_name: Optional[str] = None  # For method calls like obj.method()


@dataclass
class TypeAnnotation:
    """Information about TypeScript type annotations"""
    variable_name: str
    type_name: str
    line_number: int
    is_interface: bool = False


@dataclass
class AnalysisResult:
    """Complete analysis results for a TypeScript/JavaScript file"""
    file_path: str
    imports: List[ImportInfo] = field(default_factory=list)
    components: List[ComponentInfo] = field(default_factory=list)
    hook_calls: List[HookCall] = field(default_factory=list)
    function_calls: List[FunctionCall] = field(default_factory=list)
    type_annotations: List[TypeAnnotation] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class TypeScriptAnalyzer:
    """Analyzes TypeScript/JavaScript files for React patterns and TypeScript features"""
    
    def __init__(self):
        self.react_hooks = {
            'useState', 'useEffect', 'useContext', 'useReducer', 'useCallback',
            'useMemo', 'useRef', 'useImperativeHandle', 'useLayoutEffect',
            'useDebugValue', 'useDeferredValue', 'useTransition', 'useId',
            'useSyncExternalStore', 'useInsertionEffect', 'useOptimistic'
        }
        
        # Framework patterns to detect
        self.framework_patterns = {
            'react': {'React', 'Component', 'PureComponent', 'Fragment', 'createElement'},
            'next': {'NextPage', 'GetServerSideProps', 'GetStaticProps', 'getServerSideProps', 'getStaticProps'},
            'vue': {'Vue', 'createApp', 'defineComponent', 'ref', 'reactive'},
            'angular': {'Component', 'Injectable', 'NgModule', 'OnInit', 'OnDestroy'},
            'svelte': {'onMount', 'beforeUpdate', 'afterUpdate', 'onDestroy'},
            'solid': {'createSignal', 'createEffect', 'createMemo', 'Show', 'For'}
        }
        
        # Common libraries and their signatures
        self.library_signatures = {
            'lodash': ['_', 'debounce', 'throttle', 'map', 'filter', 'reduce', 'find', 'forEach'],
            'axios': ['axios', 'get', 'post', 'put', 'delete', 'patch'],
            'moment': ['moment', 'format', 'add', 'subtract', 'diff'],
            'date-fns': ['format', 'addDays', 'subDays', 'parseISO'],
            'ramda': ['R', 'map', 'filter', 'compose', 'pipe', 'curry'],
            'rxjs': ['Observable', 'Subject', 'BehaviorSubject', 'map', 'filter', 'mergeMap']
        }
        
    def analyze_typescript_file(self, file_path: Path, repo_path: Path, project_modules: Set[str]) -> Optional[AnalysisResult]:
        """Analyze a TypeScript/JavaScript file using esprima for AST parsing"""
        try:
            result = AnalysisResult(file_path=str(file_path))
            
            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try with different encoding if UTF-8 fails
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            
            # Skip empty files
            if not content.strip():
                return result
            
            # Use esprima to parse the file
            ast_json = self._parse_with_esprima(content)
            if not ast_json:
                return None
                
            # Extract information from AST
            try:
                self._extract_imports(ast_json, result)
            except Exception as e:
                logger.debug(f"Error extracting imports from {file_path}: {e}")
                
            try:
                self._extract_components(ast_json, result)
            except Exception as e:
                logger.debug(f"Error extracting components from {file_path}: {e}")
                
            try:
                self._extract_hooks(ast_json, result)
            except Exception as e:
                logger.debug(f"Error extracting hooks from {file_path}: {e}")
                
            try:
                self._extract_function_calls(ast_json, result)
            except Exception as e:
                logger.debug(f"Error extracting function calls from {file_path}: {e}")
                
            try:
                self._extract_type_annotations(ast_json, result)
            except Exception as e:
                logger.debug(f"Error extracting type annotations from {file_path}: {e}")
                
            try:
                self._extract_exports(ast_json, result)
            except Exception as e:
                logger.debug(f"Error extracting exports from {file_path}: {e}")
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to analyze TypeScript file {file_path}: {str(e)}"
            logger.error(error_msg)
            result = AnalysisResult(file_path=str(file_path))
            result.errors.append(error_msg)
            return result
    
    def _parse_with_esprima(self, content: str) -> Optional[Dict]:
        """Parse JavaScript/TypeScript content using esprima with better error handling"""
        try:
            # Create a temporary file for parsing
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                # For Babel parser, we can use the original content
                # Only do minimal stripping if needed
                stripped_content = content
                
                # Write content to temp file
                with open(tmp_path, 'w') as f:
                    f.write(stripped_content)
                
                # Use node with babel parser for better TypeScript/JSX support
                cmd = [
                    'node', '-e', f'''
                    const {{ parse }} = require('@babel/parser');
                    const fs = require('fs');
                    const content = fs.readFileSync('{tmp_path}', 'utf8');
                    try {{
                        const ast = parse(content, {{
                            sourceType: 'module',
                            allowImportExportEverywhere: true,
                            allowReturnOutsideFunction: true,
                            plugins: [
                                'jsx',
                                'typescript',
                                'decorators-legacy',
                                'functionBind',
                                'exportDefaultFrom',
                                'exportNamespaceFrom',
                                'dynamicImport',
                                'nullishCoalescingOperator',
                                'optionalChaining',
                                'objectRestSpread',
                                'functionBind',
                                'decorators-legacy'
                            ]
                        }});
                        console.log(JSON.stringify(ast, null, 2));
                    }} catch (e) {{
                        // Fallback to esprima for simple JS
                        try {{
                            const esprima = require('esprima');
                            const ast = esprima.parseModule(content, {{
                                loc: true,
                                range: true,
                                tolerant: true,
                                ecmaVersion: 2022,
                                sourceType: 'module'
                            }});
                            console.log(JSON.stringify(ast, null, 2));
                        }} catch (e2) {{
                            console.error("Parse error:", e.message);
                            process.exit(1);
                        }}
                    }}
                    '''
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    return json.loads(result.stdout)
                else:
                    logger.warning(f"Esprima parsing failed: {result.stderr}")
                    return None
                    
            finally:
                os.unlink(tmp_path)
                
        except Exception as e:
            logger.error(f"Error parsing with esprima: {e}")
            return None
    
    def _strip_typescript_syntax(self, content: str) -> str:
        """Strip TypeScript-specific syntax to make it parseable by esprima"""
        import re
        
        # Step 1: Remove TypeScript declarations and interfaces
        content = re.sub(r'interface\s+\w+[^{]*\{[^}]*\}', '', content, flags=re.DOTALL)
        content = re.sub(r'type\s+\w+[^=]*=\s*[^;]+;', '', content)
        content = re.sub(r'enum\s+\w+\s*\{[^}]*\}', '', content, flags=re.DOTALL)
        content = re.sub(r'namespace\s+\w+\s*\{[^}]*\}', '', content, flags=re.DOTALL)
        content = re.sub(r'declare\s+[^;]*;', '', content)
        content = re.sub(r'export\s+type\s+[^=]*=\s*[^;]+;', '', content)
        content = re.sub(r'import\s+type\s+\{[^}]*\}\s+from\s+[\'"][^\'"]*[\'"];?', '', content)
        
        # Step 2: Remove TypeScript type annotations
        # Remove type annotations after colons
        content = re.sub(r':\s*[A-Za-z_$][A-Za-z0-9_$.<>[\]|&\s?]*(?=\s*[,=)\]};])', '', content)
        content = re.sub(r':\s*React\.FC[^=,;)]*', '', content)
        content = re.sub(r':\s*FC[^=,;)]*', '', content)
        content = re.sub(r':\s*JSX\.Element[^=,;)]*', '', content)
        
        # Step 3: Remove generic type parameters
        for _ in range(3):  # Multiple passes for nested generics
            content = re.sub(r'<[^<>]*>', '', content)
        
        # Step 4: Remove TypeScript-specific keywords
        content = re.sub(r'\b(public|private|protected|readonly|abstract)\s+', '', content)
        content = re.sub(r'\s+as\s+[A-Za-z_$][A-Za-z0-9_$.<>[\]|&\s]*', '', content)
        
        # Step 5: Handle modern JavaScript syntax
        content = re.sub(r'\?\.\s*', '.', content)  # Optional chaining
        content = re.sub(r'\?\?', '||', content)    # Nullish coalescing
        
        # Step 6: Simplified JSX handling - remove JSX completely for basic parsing
        # Replace JSX elements with null to avoid syntax errors
        content = re.sub(r'return\s*\([^)]*<[^>]*>[^<]*</[^>]*>[^)]*\);', 'return null;', content, flags=re.DOTALL)
        content = re.sub(r'return\s*<[^>]*>[^<]*</[^>]*>;', 'return null;', content, flags=re.DOTALL)
        content = re.sub(r'<[^>]*/?>', 'null', content)
        
        # Step 7: Clean up
        content = re.sub(r'\n\s*\n', '\n', content)  # Remove empty lines
        content = re.sub(r'  +', ' ', content)        # Remove extra spaces
        
        return content
    
    def _extract_basic_info_with_regex(self, content: str, result: AnalysisResult):
        """Extract basic information using regex when AST parsing fails"""
        import re
        
        lines = content.split('\n')
        
        # Extract imports
        for i, line in enumerate(lines, 1):
            # Basic import patterns
            import_match = re.match(r'^\s*import\s+(.+?)\s+from\s+[\'"]([^\'"]+)[\'"]', line)
            if import_match:
                imports_str, module = import_match.groups()
                # Handle different import styles
                if imports_str.startswith('{') and imports_str.endswith('}'):
                    # Named imports
                    names = [name.strip() for name in imports_str[1:-1].split(',')]
                    for name in names:
                        result.imports.append(ImportInfo(
                            module=module,
                            name=name,
                            line_number=i
                        ))
                else:
                    # Default import
                    result.imports.append(ImportInfo(
                        module=module,
                        name=imports_str.strip(),
                        is_default_import=True,
                        line_number=i
                    ))
        
        # Extract React components (basic patterns)
        for i, line in enumerate(lines, 1):
            # Function components
            func_match = re.match(r'^\s*(?:export\s+)?(?:const|function)\s+([A-Z][A-Za-z0-9]*)', line)
            if func_match:
                name = func_match.group(1)
                result.components.append(ComponentInfo(
                    name=name,
                    type='function',
                    props=[],
                    hooks=[],
                    line_number=i,
                    is_exported='export' in line
                ))
        
        # Extract hook calls
        for i, line in enumerate(lines, 1):
            hook_matches = re.findall(r'\b(use[A-Z][A-Za-z0-9]*)\s*\(', line)
            for hook_name in hook_matches:
                result.hook_calls.append(HookCall(
                    hook_name=hook_name,
                    args=[],
                    line_number=i
                ))
        
        # Extract exports
        for i, line in enumerate(lines, 1):
            export_match = re.match(r'^\s*export\s+(?:default\s+)?(?:const|function|class)\s+([A-Za-z_][A-Za-z0-9_]*)', line)
            if export_match:
                result.exports.append(export_match.group(1))
    
    def _extract_imports(self, ast: Dict, result: AnalysisResult):
        """Extract import statements from AST"""
        def walk_ast(node):
            if isinstance(node, dict):
                if node.get('type') == 'ImportDeclaration':
                    source_node = node.get('source')
                    if not source_node:
                        return
                    source = source_node.get('value', '') if isinstance(source_node, dict) else ''
                    
                    loc_node = node.get('loc', {})
                    start_node = loc_node.get('start', {}) if isinstance(loc_node, dict) else {}
                    line_num = start_node.get('line', 0) if isinstance(start_node, dict) else 0
                    
                    for spec in node.get('specifiers', []):
                        if not isinstance(spec, dict):
                            continue
                        spec_type = spec.get('type')
                        if spec_type == 'ImportDefaultSpecifier':
                            local_node = spec.get('local', {})
                            name = local_node.get('name', '') if isinstance(local_node, dict) else ''
                            result.imports.append(ImportInfo(
                                module=source,
                                name=name,
                                is_default_import=True,
                                line_number=line_num
                            ))
                        elif spec_type == 'ImportSpecifier':
                            imported_node = spec.get('imported', {})
                            local_node = spec.get('local', {})
                            imported_name = imported_node.get('name', '') if isinstance(imported_node, dict) else ''
                            local_name = local_node.get('name', '') if isinstance(local_node, dict) else ''
                            result.imports.append(ImportInfo(
                                module=source,
                                name=imported_name,
                                alias=local_name if local_name != imported_name else None,
                                line_number=line_num
                            ))
                        elif spec_type == 'ImportNamespaceSpecifier':
                            local_node = spec.get('local', {})
                            name = local_node.get('name', '') if isinstance(local_node, dict) else ''
                            result.imports.append(ImportInfo(
                                module=source,
                                name=name,
                                is_namespace_import=True,
                                line_number=line_num
                            ))
                
                # Recursively walk children
                for key, value in node.items():
                    if isinstance(value, (list, dict)):
                        walk_ast(value)
            elif isinstance(node, list):
                for item in node:
                    walk_ast(item)
        
        try:
            walk_ast(ast)
        except Exception as e:
            logger.debug(f"Error in _extract_imports: {e}")
    
    def _extract_components(self, ast: Dict, result: AnalysisResult):
        """Extract React component definitions from AST"""
        def walk_ast(node):
            if isinstance(node, dict):
                node_type = node.get('type')
                
                # Function declarations
                if node_type == 'FunctionDeclaration':
                    id_node = node.get('id', {})
                    name = id_node.get('name', '') if isinstance(id_node, dict) else ''
                    if self._is_component_name(name):
                        loc_node = node.get('loc', {})
                        start_node = loc_node.get('start', {}) if isinstance(loc_node, dict) else {}
                        line_num = start_node.get('line', 0) if isinstance(start_node, dict) else 0
                        props = self._extract_props_from_params(node.get('params', []))
                        result.components.append(ComponentInfo(
                            name=name,
                            type='function',
                            props=props,
                            hooks=[],
                            line_number=line_num,
                            is_exported=False
                        ))
                
                # Arrow functions assigned to variables
                elif node_type == 'VariableDeclaration':
                    for declarator in node.get('declarations', []):
                        if not isinstance(declarator, dict):
                            continue
                        init_node = declarator.get('init', {})
                        if isinstance(init_node, dict) and init_node.get('type') == 'ArrowFunctionExpression':
                            id_node = declarator.get('id', {})
                            name = id_node.get('name', '') if isinstance(id_node, dict) else ''
                            if self._is_component_name(name):
                                loc_node = node.get('loc', {})
                                start_node = loc_node.get('start', {}) if isinstance(loc_node, dict) else {}
                                line_num = start_node.get('line', 0) if isinstance(start_node, dict) else 0
                                props = self._extract_props_from_params(init_node.get('params', []))
                                result.components.append(ComponentInfo(
                                    name=name,
                                    type='arrow',
                                    props=props,
                                    hooks=[],
                                    line_number=line_num,
                                    is_exported=False
                                ))
                
                # Class components
                elif node_type == 'ClassDeclaration':
                    id_node = node.get('id', {})
                    name = id_node.get('name', '') if isinstance(id_node, dict) else ''
                    if self._is_component_name(name):
                        loc_node = node.get('loc', {})
                        start_node = loc_node.get('start', {}) if isinstance(loc_node, dict) else {}
                        line_num = start_node.get('line', 0) if isinstance(start_node, dict) else 0
                        result.components.append(ComponentInfo(
                            name=name,
                            type='class',
                            props=[],
                            hooks=[],
                            line_number=line_num,
                            is_exported=False
                        ))
                
                # Recursively walk children
                for key, value in node.items():
                    if isinstance(value, (list, dict)):
                        walk_ast(value)
            elif isinstance(node, list):
                for item in node:
                    walk_ast(item)
        
        try:
            walk_ast(ast)
        except Exception as e:
            logger.debug(f"Error in _extract_components: {e}")
    
    def _extract_hooks(self, ast: Dict, result: AnalysisResult):
        """Extract React hook calls from AST"""
        def walk_ast(node):
            if isinstance(node, dict):
                if node.get('type') == 'CallExpression':
                    callee = node.get('callee', {})
                    if callee.get('type') == 'Identifier':
                        name = callee.get('name', '')
                        if name in self.react_hooks or name.startswith('use'):
                            line_num = node.get('loc', {}).get('start', {}).get('line', 0)
                            args = [self._extract_arg_value(arg) for arg in node.get('arguments', [])]
                            result.hook_calls.append(HookCall(
                                hook_name=name,
                                args=args,
                                line_number=line_num
                            ))
                
                # Recursively walk children
                for key, value in node.items():
                    if isinstance(value, (list, dict)):
                        walk_ast(value)
            elif isinstance(node, list):
                for item in node:
                    walk_ast(item)
        
        walk_ast(ast)
    
    def _extract_function_calls(self, ast: Dict, result: AnalysisResult):
        """Extract function calls from AST"""
        def walk_ast(node):
            if isinstance(node, dict):
                if node.get('type') == 'CallExpression':
                    callee = node.get('callee', {})
                    line_num = node.get('loc', {}).get('start', {}).get('line', 0)
                    args = [self._extract_arg_value(arg) for arg in node.get('arguments', [])]
                    
                    if callee.get('type') == 'Identifier':
                        # Simple function call
                        name = callee.get('name', '')
                        if not (name in self.react_hooks or name.startswith('use')):
                            result.function_calls.append(FunctionCall(
                                function_name=name,
                                args=args,
                                line_number=line_num
                            ))
                    elif callee.get('type') == 'MemberExpression':
                        # Method call
                        obj_name = callee.get('object', {}).get('name', '')
                        method_name = callee.get('property', {}).get('name', '')
                        result.function_calls.append(FunctionCall(
                            function_name=method_name,
                            args=args,
                            line_number=line_num,
                            object_name=obj_name
                        ))
                
                # Recursively walk children
                for key, value in node.items():
                    if isinstance(value, (list, dict)):
                        walk_ast(value)
            elif isinstance(node, list):
                for item in node:
                    walk_ast(item)
        
        walk_ast(ast)
    
    def _extract_type_annotations(self, ast: Dict, result: AnalysisResult):
        """Extract TypeScript type annotations from AST"""
        # This would need more sophisticated TypeScript AST parsing
        # For now, we'll implement basic type extraction
        pass
    
    def _extract_exports(self, ast: Dict, result: AnalysisResult):
        """Extract export statements from AST"""
        def walk_ast(node):
            if isinstance(node, dict):
                node_type = node.get('type')
                
                if node_type == 'ExportDefaultDeclaration':
                    declaration = node.get('declaration', {})
                    if declaration.get('type') == 'Identifier':
                        result.exports.append(declaration.get('name', ''))
                elif node_type == 'ExportNamedDeclaration':
                    if node.get('declaration'):
                        # Export with declaration
                        decl = node.get('declaration', {})
                        if decl.get('type') == 'FunctionDeclaration':
                            result.exports.append(decl.get('id', {}).get('name', ''))
                        elif decl.get('type') == 'VariableDeclaration':
                            for declarator in decl.get('declarations', []):
                                result.exports.append(declarator.get('id', {}).get('name', ''))
                
                # Recursively walk children
                for key, value in node.items():
                    if isinstance(value, (list, dict)):
                        walk_ast(value)
            elif isinstance(node, list):
                for item in node:
                    walk_ast(item)
        
        walk_ast(ast)
    
    def _is_component_name(self, name: str) -> bool:
        """Check if a name follows React component naming conventions"""
        return name and name[0].isupper() and name.isidentifier()
    
    def _extract_props_from_params(self, params: List[Dict]) -> List[str]:
        """Extract prop names from function parameters"""
        props = []
        for param in params:
            if param.get('type') == 'Identifier':
                props.append(param.get('name', ''))
            elif param.get('type') == 'ObjectPattern':
                for prop in param.get('properties', []):
                    if prop.get('type') == 'Property':
                        props.append(prop.get('key', {}).get('name', ''))
        return props
    
    def _extract_arg_value(self, arg: Dict) -> str:
        """Extract argument value as string representation"""
        if not arg:
            return ''
        
        arg_type = arg.get('type')
        if arg_type == 'Literal':
            return str(arg.get('value', ''))
        elif arg_type == 'Identifier':
            return arg.get('name', '')
        elif arg_type == 'MemberExpression':
            obj = arg.get('object', {}).get('name', '')
            prop = arg.get('property', {}).get('name', '')
            return f"{obj}.{prop}"
        else:
            return f"<{arg_type}>"