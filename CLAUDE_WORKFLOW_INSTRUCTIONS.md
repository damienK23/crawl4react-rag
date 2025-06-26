# 🎯 Instructions Systématiques pour Claude

## 📋 WORKFLOW OBLIGATOIRE À CHAQUE REQUÊTE

### **🔒 RÈGLE D'OR : JAMAIS de code sans validation MCP**

```
⚠️  INTERDICTION ABSOLUE :
❌ Écrire du code sans vérifier le schéma DB
❌ Utiliser des APIs/composants sans validation MCP
❌ Supposer l'existence de tables/fonctions
❌ Inventer des paramètres de fonctions

✅ OBLIGATION SYSTÉMATIQUE :
✅ TOUJOURS commencer par analyze_supabase_schema()
✅ TOUJOURS valider avec comprehensive_validation()
✅ TOUJOURS vérifier avant de créer
✅ TOUJOURS itérer jusqu'à 0 erreur
```

---

## 📝 TEMPLATE DE CONVERSATION OBLIGATOIRE

### **Étape 1 : DÉCLARATION D'INTENTION**
```
🤔 ANALYSE DE LA DEMANDE :
[Claude explique sa compréhension]

🎯 PLAN PRÉLIMINAIRE :
[Ce que Claude pense faire]

⚠️  AVANT TOUT CODE : Je vais d'abord analyser l'existant avec MCP
```

### **Étape 2 : EXPLORATION SYSTÉMATIQUE**
```
🔍 EXPLORATION MCP EN COURS...

1. Analyse du schéma Supabase
2. Exploration de la structure projet  
3. Validation de l'état actuel

[Claude exécute les outils MCP]
```

### **Étape 3 : RAPPORT D'EXPLORATION**
```
📊 DÉCOUVERTES MCP :

✅ CE QUI EXISTE :
- Tables : [liste réelle]
- Fonctions RPC : [liste réelle]
- Composants : [liste réelle]

❌ CE QUI N'EXISTE PAS :
- [éléments manquants]

🔄 PLAN RÉVISÉ (basé sur la réalité) :
[plan corrigé selon les découvertes MCP]
```

### **Étape 4 : DÉVELOPPEMENT VALIDÉ**
```
✏️  DÉVELOPPEMENT EN COURS...

[Pour chaque fichier créé/modifié :]
1. ✅ Création du code
2. 🔍 Validation MCP immédiate
3. 🔄 Correction si erreurs
4. ✅ Confirmation de validation

[Claude valide CHAQUE fichier individuellement]
```

### **Étape 5 : VALIDATION FINALE**
```
🎯 VALIDATION FINALE COMPLÈTE :

✅ Tous les fichiers validés individuellement
✅ Validation globale du projet
✅ 0 hallucination détectée
✅ Confidence : XX%

📋 RÉSUMÉ DES MODIFICATIONS :
[liste des changements avec validation]
```

---

## 🛠️ OUTILS MCP - USAGE SYSTÉMATIQUE

### **🔍 Phase Exploration (OBLIGATOIRE au début)**

```bash
# 1. TOUJOURS commencer par le schéma DB
analyze_supabase_schema()

# 2. Explorer la structure projet si modif de code
parse_github_repository(".")

# 3. Valider l'état actuel d'un fichier existant
comprehensive_validation("chemin/vers/fichier.tsx")
```

### **✅ Phase Validation (OBLIGATOIRE après chaque modification)**

```bash
# Après CHAQUE création/modification de fichier
comprehensive_validation("nouveau-fichier.tsx")

# Validation globale finale
comprehensive_validation("src/")
```

### **🔧 Commandes de Vérification Rapide**

```bash
# Tester une API Supabase avant utilisation
comprehensive_validation(`
const { data } = await supabase.rpc('nom_fonction', { param: 'value' });
`)

# Tester l'existence d'un composant
comprehensive_validation(`
import { MonComposant } from './MonComposant';
`)

# Vérifier une table/colonne
comprehensive_validation(`
const { data } = await supabase.from('ma_table').select('ma_colonne');
`)
```

---

## 📋 CHECKLIST OBLIGATOIRE

### **✅ Avant TOUTE modification de code :**

```
□ analyze_supabase_schema() exécuté
□ Schéma DB compris et documenté
□ Tables/colonnes existantes identifiées
□ Fonctions RPC disponibles listées
□ Structure projet explorée si nécessaire
□ Plan basé sur la RÉALITÉ (pas sur des suppositions)
```

### **✅ Pendant le développement :**

```
□ CHAQUE nouveau fichier validé avec comprehensive_validation()
□ CHAQUE modification validée immédiatement
□ Aucune API utilisée sans vérification préalable
□ Aucun composant référencé sans validation d'existence
□ Correction immédiate de toute erreur détectée
```

### **✅ Validation finale :**

```
□ comprehensive_validation() sur tous les fichiers modifiés
□ 0 erreur de hallucination
□ Confidence > 95%
□ Tests fonctionnels si possible
□ Documentation des changements
```

---

## 🚨 SYSTÈME D'ALERTE AUTO-CONTRÔLE

### **Claude doit se poser ces questions :**

```
🤔 AVANT D'ÉCRIRE DU CODE :
❓ Ai-je analysé le schéma Supabase ?
❓ Cette table/fonction existe-t-elle vraiment ?
❓ Ces colonnes sont-elles confirmées ?
❓ Ce composant existe-t-il déjà ?

⚠️  SI UNE RÉPONSE EST "NON" → STOP et utiliser MCP d'abord

🔍 PENDANT LE CODE :
❓ Cette API a-t-elle été validée ?
❓ Ces paramètres sont-ils corrects ?
❓ Cette interface correspond-elle au schéma réel ?

⚠️  SI DOUTE → Validation MCP immédiate

✅ APRÈS LE CODE :
❓ comprehensive_validation() exécuté ?
❓ 0 erreur détectée ?
❓ Tous les fichiers validés ?

⚠️  SI NON → Iteration jusqu'à succès complet
```

---

## 📜 PHRASES INTERDITES pour Claude

### **🚫 Phrases qui indiquent des hallucinations :**

❌ "Cette table devrait exister"  
❌ "Normalement il y a une fonction pour..."  
❌ "Je suppose que..."  
❌ "Il est probable que..."  
❌ "Cette API existe généralement"  
❌ "Dans la plupart des cas..."  

### **✅ Phrases correctes (basées sur MCP) :**

✅ "D'après analyze_supabase_schema(), la table X existe avec les colonnes Y"  
✅ "comprehensive_validation() confirme que la fonction Z est disponible"  
✅ "Le schéma MCP montre que..."  
✅ "Validation MCP réussie, le code est correct"  
✅ "Après vérification MCP, je peux utiliser..."  

---

## 🔄 EXEMPLE DE CONVERSATION TYPE

### **❌ MAUVAISE Approche (sans MCP) :**
```
User: "Ajoute une fonction pour récupérer les notifications"

Claude: "Voici le code pour récupérer les notifications :
```typescript
const { data } = await supabase
  .from('notifications')  // ❌ Table non vérifiée
  .select('id, message, read_status'); // ❌ Colonnes non vérifiées
```

❌ PROBLÈME : Aucune validation, code potentiellement cassé
```

### **✅ BONNE Approche (avec MCP obligatoire) :**

```
User: "Ajoute une fonction pour récupérer les notifications"

Claude: 
🤔 ANALYSE : Besoin d'une fonction pour récupérer les notifications

⚠️  AVANT TOUT CODE : Je vais analyser le schéma Supabase existant

[Exécute: analyze_supabase_schema()]

📊 DÉCOUVERTES MCP :
❌ Table 'notifications' : N'EXISTE PAS
✅ Tables disponibles : users, profiles, documents

🔄 PLAN RÉVISÉ : 
Option 1: Créer une table notifications d'abord (côté DB)
Option 2: Utiliser une table existante comme placeholder
Option 3: Simuler avec des données mock

Quelle approche préférez-vous ?

[Attend la décision utilisateur avant de coder]
```

---

## 🎯 AUTOMATISATION DU WORKFLOW

### **Script de Validation Continue**

```python
# auto_validate.py - À exécuter pendant le développement
import subprocess
import time

def validate_continuously():
    while True:
        print("🔍 Validation automatique en cours...")
        
        # Valider tous les fichiers modifiés
        result = subprocess.run([
            "python", "src/crawl4ai_mcp.py",
            "--tool", "comprehensive_validation",
            "--file", "src/"
        ], capture_output=True, text=True)
        
        if "0 issues" in result.stdout:
            print("✅ Aucune hallucination détectée")
            break
        else:
            print("❌ Erreurs détectées :")
            print(result.stdout)
            input("Appuyez sur Entrée après correction...")
        
        time.sleep(2)

if __name__ == "__main__":
    validate_continuously()
```

### **Template de Commit avec Validation**

```bash
#!/bin/bash
# pre-commit-validation.sh

echo "🔍 Validation MCP avant commit..."

# Valider avec MCP
python src/crawl4ai_mcp.py --tool comprehensive_validation --file src/

if [ $? -eq 0 ]; then
    echo "✅ Validation MCP réussie - Commit autorisé"
    exit 0
else
    echo "❌ Validation MCP échouée - Commit refusé"
    echo "Corrigez les hallucinations avant de commiter"
    exit 1
fi
```

---

## 💡 MÉMO POUR CLAUDE

### **🎯 À retenir absolument :**

1. **JAMAIS de code sans MCP** - C'est la règle #1
2. **analyze_supabase_schema() en premier** - Toujours
3. **comprehensive_validation() après chaque fichier** - Obligatoire
4. **0 erreur acceptée** - Itérer jusqu'au succès
5. **Documenter les découvertes MCP** - Pour transparence

### **🔧 Raccourcis mentaux :**

```
Code à écrire → STOP → MCP d'abord → Code validé ✅
API à utiliser → STOP → Vérification MCP → Utilisation ✅  
Table à interroger → STOP → Schéma MCP → Requête ✅
Composant à importer → STOP → Validation existence → Import ✅
```

### **📱 Aide-mémoire des commandes :**

```bash
# Démarrage obligatoire
analyze_supabase_schema()

# Validation continue  
comprehensive_validation("fichier.tsx")

# Test rapide API
comprehensive_validation(`code_snippet`)

# Validation finale
comprehensive_validation("src/")
```

**🎯 OBJECTIF : 0% d'hallucination, 100% de code fonctionnel basé sur la réalité !**