# Guide de Déploiement OpenProject MCP Server

## Vue d'ensemble

Ce guide explique comment déployer le serveur MCP OpenProject dans un environnement Docker sécurisé, sans certificat SSL, en utilisant le réseau interne Docker pour communiquer avec OpenProject.

## Architecture recommandée

```
┌─────────────────────────────────────────────────────────────┐
│                    Hôte Distant                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   OpenProject   │    │   MCP Server    │                │
│  │   (Port 8080)   │◄──►│  (Port 8080)    │                │
│  │                 │    │                 │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                       │                        │
│           └───────────────────────┼────────────────────────┘
│                                   │
│  ┌─────────────────────────────────┼─────────────────────┐  │
│  │        Réseau Docker            │                     │  │
│  │      (openproject-network)      │                     │  │
│  └─────────────────────────────────┴─────────────────────┘  │
│                                   │                        │
│  ┌─────────────────────────────────┼─────────────────────┐  │
│  │        Accès Externe            │                     │  │
│  │  • MCP: Port 39127              │                     │  │
│  │  • Status: Port 39128           │                     │  │
│  └─────────────────────────────────┴─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Prérequis

1. **Docker et Docker Compose** installés sur l'hôte distant
2. **OpenProject** déjà déployé et accessible
3. **API Key OpenProject** générée depuis votre profil utilisateur
4. **Accès réseau** entre les conteneurs

## Configuration

### 1. Préparation des fichiers

Copiez les fichiers de configuration dans votre répertoire de déploiement :

```bash
# Fichiers nécessaires
docker-compose-production.yml
env.production
deploy-production.sh
```

### 2. Configuration de l'environnement

Éditez le fichier `env.production` :

```bash
# URL OpenProject (nom du service dans le réseau Docker)
OPENPROJECT_URL=http://openproject:8080

# Votre API Key OpenProject (40 caractères)
OPENPROJECT_API_KEY=your_actual_api_key_here

# Configuration MCP Server
MCP_HOST=0.0.0.0
MCP_PORT=8080
MCP_LOG_LEVEL=INFO

# Ports externes pour accès depuis l'extérieur
MCP_EXTERNAL_PORT=39127
MCP_STATUS_PORT=39128
```

### 3. Configuration du réseau Docker

#### Option A : OpenProject dans la même stack

Si OpenProject est dans le même `docker-compose.yml`, décommentez la section OpenProject dans `docker-compose-production.yml`.

#### Option B : OpenProject dans une stack séparée

Si OpenProject est dans une autre stack, configurez le réseau externe :

```yaml
networks:
  openproject-network:
    external: true
    name: openproject_default  # Nom du réseau OpenProject
```

## Déploiement

### Déploiement automatique

```bash
# Rendre le script exécutable
chmod +x deploy-production.sh

# Déployer
./deploy-production.sh
```

### Déploiement manuel

```bash
# Construire et démarrer
docker-compose -f docker-compose-production.yml --env-file env.production up -d --build

# Vérifier le statut
docker-compose -f docker-compose-production.yml --env-file env.production ps

# Voir les logs
docker-compose -f docker-compose-production.yml --env-file env.production logs -f
```

## Vérification

### 1. Statut des services

```bash
./deploy-production.sh status
```

### 2. Test de connectivité

```bash
# Test du port de statut
curl http://localhost:39128/health

# Test du port MCP
curl http://localhost:39127/
```

### 3. Logs en temps réel

```bash
./deploy-production.sh logs
```

## Intégration avec les clients MCP

### Configuration client

Les clients MCP peuvent se connecter via :

- **URL** : `http://your-server-ip:39127`
- **Transport** : HTTP/SSE
- **Pas de certificat SSL requis**

### Exemple de configuration Claude

```json
{
  "mcpServers": {
    "openproject": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-cli", "http://your-server-ip:39127"],
      "env": {}
    }
  }
}
```

## Sécurité

### Avantages de cette configuration

1. **Communication interne sécurisée** : OpenProject et MCP communiquent via le réseau Docker interne
2. **Pas d'exposition directe** : OpenProject n'est pas exposé directement à l'extérieur
3. **Contrôle d'accès** : Seul le serveur MCP est accessible depuis l'extérieur
4. **Authentification** : Utilisation de l'API Key OpenProject pour l'authentification

### Recommandations

1. **Firewall** : Limitez l'accès aux ports 39127 et 39128
2. **Monitoring** : Surveillez les logs pour détecter les accès non autorisés
3. **Rotation des clés** : Changez régulièrement l'API Key OpenProject
4. **Backup** : Sauvegardez les volumes de données

## Dépannage

### Problèmes courants

#### 1. Erreur de connexion à OpenProject

```bash
# Vérifier que OpenProject est accessible depuis le conteneur MCP
docker exec openproject-mcp-server curl -s http://openproject:8080/api/v3/status
```

#### 2. Ports déjà utilisés

```bash
# Vérifier les ports utilisés
netstat -tlnp | grep :39127
netstat -tlnp | grep :39128

# Changer les ports dans env.production si nécessaire
```

#### 3. Problèmes de réseau Docker

```bash
# Lister les réseaux Docker
docker network ls

# Inspecter le réseau
docker network inspect openproject-network
```

### Logs détaillés

```bash
# Logs du conteneur MCP
docker logs openproject-mcp-server

# Logs avec timestamps
docker logs -t openproject-mcp-server
```

## Maintenance

### Mise à jour

```bash
# Arrêter les services
./deploy-production.sh stop

# Mettre à jour le code
git pull

# Redéployer
./deploy-production.sh deploy
```

### Sauvegarde

```bash
# Sauvegarder les données
docker run --rm -v openproject-mcp-server_data:/data -v $(pwd):/backup alpine tar czf /backup/mcp-backup-$(date +%Y%m%d).tar.gz /data
```

### Nettoyage

```bash
# Nettoyer les images non utilisées
docker image prune -f

# Nettoyer les volumes non utilisés
docker volume prune -f
```

## Support

Pour toute question ou problème :

1. Consultez les logs : `./deploy-production.sh logs`
2. Vérifiez la configuration : `cat env.production`
3. Testez la connectivité : `curl http://localhost:39128/health`
4. Consultez la documentation OpenProject pour l'API
