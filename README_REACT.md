# Configuration pour React

## Variables d'environnement pour React

Pour utiliser ce serveur MCP avec une application React, vous devez configurer les variables d'environnement appropriées.

### Variables côté serveur (dans .env)
```bash
# Supabase Configuration
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_SERVICE_ROLE_KEY=votre-service-role-key

# OpenAI Configuration
OPENAI_API_KEY=votre-openai-api-key
MODEL_CHOICE=gpt-4o-mini

# Features
USE_CONTEXTUAL_EMBEDDINGS=true
USE_HYBRID_SEARCH=true
USE_AGENTIC_RAG=true
USE_RERANKING=false
USE_KNOWLEDGE_GRAPH=false
```

### Variables côté client React (dans .env.local)
```bash
# Variables publiques pour React (préfixées par REACT_APP_)
REACT_APP_SUPABASE_URL=https://votre-projet.supabase.co
REACT_APP_SUPABASE_ANON_KEY=votre-anon-key

# URL du serveur MCP
REACT_APP_MCP_SERVER_URL=http://localhost:8000
```

## Intégration avec React

### 1. Installation côté client

Dans votre projet React, installez les dépendances nécessaires :

```bash
npm install @supabase/supabase-js
npm install axios  # pour les appels API vers le serveur MCP
```

### 2. Configuration Supabase côté client

```javascript
// src/lib/supabase.js
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

### 3. Service pour les appels au serveur MCP

```javascript
// src/services/mcpService.js
import axios from 'axios'

const MCP_BASE_URL = process.env.REACT_APP_MCP_SERVER_URL

class MCPService {
  async crawlSite(url) {
    try {
      const response = await axios.post(`${MCP_BASE_URL}/crawl`, { url })
      return response.data
    } catch (error) {
      console.error('Error crawling site:', error)
      throw error
    }
  }

  async searchDocuments(query, options = {}) {
    try {
      const response = await axios.post(`${MCP_BASE_URL}/search`, {
        query,
        ...options
      })
      return response.data
    } catch (error) {
      console.error('Error searching documents:', error)
      throw error
    }
  }

  async searchCodeExamples(query, options = {}) {
    try {
      const response = await axios.post(`${MCP_BASE_URL}/search-code`, {
        query,
        ...options
      })
      return response.data
    } catch (error) {
      console.error('Error searching code examples:', error)
      throw error
    }
  }

  async listSources() {
    try {
      const response = await axios.get(`${MCP_BASE_URL}/sources`)
      return response.data
    } catch (error) {
      console.error('Error listing sources:', error)
      throw error
    }
  }
}

export default new MCPService()
```

### 4. Hook React pour la recherche

```javascript
// src/hooks/useSearch.js
import { useState, useCallback } from 'react'
import mcpService from '../services/mcpService'

export const useSearch = () => {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState([])
  const [error, setError] = useState(null)

  const searchDocuments = useCallback(async (query, options) => {
    setLoading(true)
    setError(null)
    try {
      const data = await mcpService.searchDocuments(query, options)
      setResults(data)
      return data
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const searchCodeExamples = useCallback(async (query, options) => {
    setLoading(true)
    setError(null)
    try {
      const data = await mcpService.searchCodeExamples(query, options)
      setResults(data)
      return data
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    loading,
    results,
    error,
    searchDocuments,
    searchCodeExamples
  }
}
```

### 5. Composant de recherche

```javascript
// src/components/SearchComponent.jsx
import React, { useState } from 'react'
import { useSearch } from '../hooks/useSearch'

const SearchComponent = () => {
  const [query, setQuery] = useState('')
  const [searchType, setSearchType] = useState('documents')
  const { loading, results, error, searchDocuments, searchCodeExamples } = useSearch()

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    try {
      if (searchType === 'documents') {
        await searchDocuments(query)
      } else {
        await searchCodeExamples(query)
      }
    } catch (err) {
      console.error('Search failed:', err)
    }
  }

  return (
    <div className="search-container">
      <form onSubmit={handleSearch}>
        <div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Rechercher..."
            disabled={loading}
          />
          <select
            value={searchType}
            onChange={(e) => setSearchType(e.target.value)}
          >
            <option value="documents">Documents</option>
            <option value="code">Exemples de code</option>
          </select>
          <button type="submit" disabled={loading}>
            {loading ? 'Recherche...' : 'Rechercher'}
          </button>
        </div>
      </form>

      {error && (
        <div className="error">
          Erreur: {error}
        </div>
      )}

      {results.length > 0 && (
        <div className="results">
          <h3>Résultats ({results.length})</h3>
          {results.map((result, index) => (
            <div key={index} className="result-item">
              <h4>{result.url}</h4>
              <p>{result.content}</p>
              {result.similarity && (
                <span>Pertinence: {(result.similarity * 100).toFixed(1)}%</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default SearchComponent
```

## Démarrage

1. **Démarrer le serveur MCP** :
   ```bash
   cd mcp-crawl4react-rag
   python -m src.crawl4react_mcp
   ```

2. **Démarrer votre application React** :
   ```bash
   cd votre-app-react
   npm start
   ```

3. **Crawl des sites** via l'interface React ou directement via l'API MCP

4. **Recherche** dans les documents crawlés via votre interface React