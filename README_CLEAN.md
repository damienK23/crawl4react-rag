# MCP Crawl4AI RAG - Version Nettoyée

## 🎯 Projet Optimisé pour l'Analyse Directe de Base de Données

Ce projet a été nettoyé et optimisé pour se concentrer uniquement sur **l'analyse directe de bases de données existantes** plutôt que sur leur création ou migration.

## 📁 Structure Simplifiée

```
mcp-crawl4react-rag/
├── src/                                 # Code source principal
│   ├── crawl4react_mcp.py                 # ⭐ Serveur MCP principal
│   ├── HallucinationChecker.tsx        # Composant React de validation
│   ├── example-usage.tsx               # Exemples d'utilisation
│   └── utils.py                        # Utilitaires
├── knowledge_graphs/                    # Analyseurs et validateurs
│   ├── comprehensive_validator.py       # ⭐ Validateur complet IA
│   ├── rpc_parameter_validator.py      # ⭐ Validation RPC avancée
│   ├── typescript_analyzer.py          # Analyseur TypeScript/React
│   ├── supabase_analyzer.py            # Analyseur Supabase
│   ├── neo4j_clean_hierarchy.py        # Parser Neo4j propre
│   ├── signature_validator.py          # Validation des signatures
│   └── advanced_patterns_detector.py   # Détection de patterns
├── test_files/                         # Fichiers de test
│   ├── realistic_rpc_test.tsx          # Test RPC réaliste
│   ├── database_hallucination_test.tsx # Test d'hallucinations DB
│   └── test_component.tsx              # Test de composants React
├── test_advanced_rpc_validation.py     # ⭐ Test validation RPC
├── test_realistic_validation.py        # ⭐ Test réaliste
├── clear_neo4j_repository.py           # Outils de nettoyage Neo4j
└── show_neo4j_clear_commands.py        # Guide commandes Neo4j
```

## 🚀 Fonctionnalités Principales

### ✅ **Validation Complète d'Hallucinations IA**

**5 niveaux de validation RPC Supabase :**
1. **Types de paramètres** (UUID vs string vs int)
2. **Paramètres obligatoires** vs optionnels
3. **Valeurs enum** (validation stricte)
4. **Structures JSON** (validation de schéma)
5. **Nombre de paramètres** (min/max)

**Autres détections :**
- ❌ Composants React inexistants
- ❌ Hooks personnalisés introuvables
- ❌ Tables Supabase inexistantes
- ❌ Fonctions RPC inexistantes
- ❌ Signatures incorrectes
- ❌ Types TypeScript invalides
- ⚠️ Mauvaises pratiques de sécurité

### 🔧 **Analyseurs Spécialisés**

- **TypeScript/React** : Components, hooks, types, interfaces
- **Supabase** : Tables, colonnes, fonctions RPC, enums
- **Neo4j** : Hiérarchie propre et navigable
- **Patterns** : Sécurité, performance, anti-patterns

## 📋 Utilisation

### 1. **Serveur MCP Principal**
```bash
python src/crawl4react_mcp.py
```

### 2. **Test de Validation Complète**
```bash
python test_realistic_validation.py
```

### 3. **Validation RPC Avancée**
```bash
python test_advanced_rpc_validation.py
```

### 4. **Nettoyage Neo4j**
```bash
# Afficher la structure
python clear_neo4j_repository.py --show-structure

# Effacer un repository
python clear_neo4j_repository.py --repo-name "nom_repo"
```

## ⚙️ Configuration

### Variables d'environnement requises :
```bash
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Supabase (pour validation RPC)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
```

### Installation des dépendances :
```bash
pip install -r requirements.txt
# ou
uv sync
```

## 🎯 Cas d'Usage Principaux

### **1. Validation de Code TypeScript/React**
```typescript
// Le système détecte automatiquement :
const { data } = await supabase
    .rpc('invalid_function', {           // ❌ Fonction inexistante
        user_id: 'not-a-uuid',          // ❌ Format UUID invalide
        status: 'invalid_enum'           // ❌ Valeur enum incorrecte
    });
```

### **2. Analyse de Composants React**
```typescript
// Détection d'hallucinations :
import { NonExistentComponent } from './fake';  // ❌ Composant inexistant

const MyComponent = () => {
    const [data] = useFakeHook();                // ❌ Hook inexistant
    return <NonExistentComponent />;             // ❌ Utilisation invalide
};
```

### **3. Validation de Base de Données**
```typescript
// Validation automatique :
const { data } = await supabase
    .from('imaginary_table')                     // ❌ Table inexistante
    .select('fake_column, another_fake');        // ❌ Colonnes inexistantes
```

## 🗑️ Éléments Supprimés

Le nettoyage a retiré **tous les scripts de création/migration** :
- ❌ `supabase/migrations/` (complet)
- ❌ `supabase/config.toml`
- ❌ Scripts SQL de création
- ❌ Tests redondants (10+ fichiers)
- ❌ Documentation en double
- ❌ Node.js modules non utilisés

## 📊 Résultats Typiques

```bash
📊 VALIDATION RESULTS:
  Total issues detected: 21
  Overall confidence: 71.3%
  RPC parameter issues: 8
  
🚨 RPC PARAMETER VALIDATION ERRORS:
❌ TYPE_MISMATCH (3 issues):
   • Parameter 'user_id' must be a valid UUID
   • Parameter 'include_details' must be a boolean
   
❌ INVALID_ENUM_VALUE (2 issues):
   • Parameter 'date_range' has invalid enum value
   
❌ PARAMETER_COUNT_MISMATCH (1 issue):
   • Too many parameters. Expected at most 5, got 7
```

## 🎉 Avantages de la Version Nettoyée

✅ **Focus** : Analyse directe plutôt que création DB  
✅ **Performance** : Structure simplifiée et rapide  
✅ **Clarté** : Fichiers essentiels seulement  
✅ **Maintenance** : Moins de complexité  
✅ **Efficacité** : Validation précise et complète  

## 🔧 Développement

### Tests Conservés :
- `test_realistic_validation.py` - Test complet sur cas réels
- `test_advanced_rpc_validation.py` - Test validation RPC spécialisée  
- `test_clean_hierarchy.py` - Test hiérarchie Neo4j

### Outils Utiles :
- `show_neo4j_clear_commands.py` - Guide des commandes
- `clear_neo4j_repository.py` - Nettoyage Neo4j
- `auto_cleanup.py` - Script de nettoyage utilisé

---

**🎯 Cette version optimisée se concentre sur l'analyse et la validation de bases de données existantes, avec une validation d'hallucinations IA de niveau professionnel.**