# Guide de Déploiement Portainer - OpenProject MCP Server

## Vue d'ensemble

Ce guide explique comment déployer le serveur MCP OpenProject via Portainer, en construisant d'abord l'image Docker sur l'hôte.

## Prérequis

1. **Portainer** installé et accessible
2. **Docker** sur l'hôte Portainer
3. **OpenProject** déjà déployé et accessible
4. **API Key OpenProject** générée
5. **Accès SSH** à l'hôte Portainer (pour le build)

## Étapes de déploiement

### 1. Préparation des fichiers

Sur votre machine de développement, préparez les fichiers :

```bash
# Fichiers nécessaires pour Portainer
build-for-portainer.sh
docker-compose-portainer.yml
env.portainer
PORTAINER_DEPLOYMENT_GUIDE.md
```

### 2. Transfert vers l'hôte Portainer

```bash
# Copier les fichiers vers l'hôte Portainer
scp -r . user@portainer-host:/opt/openproject-mcp-server/

# Ou utiliser rsync
rsync -avz --exclude='.git' . user@portainer-host:/opt/openproject-mcp-server/
```

### 3. Build de l'image sur l'hôte

Connectez-vous à l'hôte Portainer :

```bash
ssh user@portainer-host
cd /opt/openproject-mcp-server

# Rendre le script exécutable
chmod +x build-for-portainer.sh

# Construire l'image
./build-for-portainer.sh latest

# Vérifier que l'image est créée
docker images | grep openproject-mcp-server
```

### 4. Configuration dans Portainer

#### 4.1 Accès à Portainer

1. Ouvrez votre interface Portainer
2. Connectez-vous avec vos identifiants

#### 4.2 Configuration des variables d'environnement

1. Allez dans **Stacks** > **Add stack**
2. Nommez votre stack : `openproject-mcp`
3. Dans la section **Environment variables**, ajoutez :

```yaml
OPENPROJECT_URL=http://openproject:8080
OPENPROJECT_API_KEY=your_actual_api_key_here
MCP_HOST=0.0.0.0
MCP_PORT=8080
MCP_LOG_LEVEL=INFO
MCP_EXTERNAL_PORT=39127
MCP_STATUS_PORT=39128
```

#### 4.3 Configuration du docker-compose

Copiez le contenu de `docker-compose-portainer.yml` dans l'éditeur Portainer :

```yaml
version: '3.8'

services:
  openproject-mcp:
    image: openproject-mcp-server:latest
    container_name: openproject-mcp-server
    restart: unless-stopped
    
    environment:
      - OPENPROJECT_URL=${OPENPROJECT_URL:-http://openproject:8080}
      - OPENPROJECT_API_KEY=${OPENPROJECT_API_KEY}
      - MCP_HOST=${MCP_HOST:-0.0.0.0}
      - MCP_PORT=${MCP_PORT:-8080}
      - MCP_LOG_LEVEL=${MCP_LOG_LEVEL:-INFO}
    
    ports:
      - "${MCP_EXTERNAL_PORT:-39127}:8080"
      - "${MCP_STATUS_PORT:-39128}:8081"
    
    volumes:
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
    
    healthcheck:
      test: ["CMD", "python3", "-c", "import asyncio; import sys; sys.path.insert(0, '/app/src'); from openproject_client import OpenProjectClient; async def check(): client = OpenProjectClient(); result = await client.test_connection(); await client.close(); exit(0 if result['success'] else 1); asyncio.run(check())"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
    networks:
      - openproject-network
    
    labels:
      - "traefik.enable=false"
      - "portainer.agent.role=application"

networks:
  openproject-network:
    driver: bridge

volumes:
  mcp_logs:
    driver: local
  mcp_data:
    driver: local
```

### 5. Déploiement

1. Cliquez sur **Deploy the stack**
2. Attendez que le déploiement se termine
3. Vérifiez le statut dans **Containers**

### 6. Vérification

#### 6.1 Vérification dans Portainer

1. Allez dans **Containers**
2. Vérifiez que `openproject-mcp-server` est en cours d'exécution
3. Cliquez sur le conteneur pour voir les logs

#### 6.2 Test de connectivité

```bash
# Test du port de statut
curl http://portainer-host:39128/health

# Test du port MCP
curl http://portainer-host:39127/
```

## Configuration réseau

### Option A : OpenProject dans la même stack

Si vous voulez inclure OpenProject dans la même stack, décommentez la section OpenProject dans le docker-compose.

### Option B : OpenProject dans une stack séparée

Si OpenProject est dans une autre stack, modifiez la section réseau :

```yaml
networks:
  openproject-network:
    external: true
    name: openproject_default  # Nom du réseau OpenProject
```

## Gestion via Portainer

### Mise à jour de l'image

1. **Sur l'hôte Portainer** :
   ```bash
   cd /opt/openproject-mcp-server
   git pull  # Si vous utilisez git
   ./build-for-portainer.sh v2.0.0
   ```

2. **Dans Portainer** :
   - Allez dans **Stacks** > votre stack
   - Cliquez sur **Editor**
   - Modifiez l'image : `openproject-mcp-server:v2.0.0`
   - Cliquez sur **Update the stack**

### Redémarrage des services

1. Allez dans **Containers**
2. Sélectionnez `openproject-mcp-server`
3. Cliquez sur **Restart**

### Consultation des logs

1. Allez dans **Containers**
2. Cliquez sur `openproject-mcp-server`
3. Onglet **Logs**

### Sauvegarde des volumes

1. Allez dans **Volumes**
2. Sélectionnez `mcp_logs` ou `mcp_data`
3. Cliquez sur **Backup**

## Dépannage

### Problèmes courants

#### 1. Image non trouvée

```bash
# Vérifier que l'image existe
docker images | grep openproject-mcp-server

# Si elle n'existe pas, rebuilder
./build-for-portainer.sh latest
```

#### 2. Erreur de réseau

- Vérifiez que le réseau `openproject-network` existe
- Vérifiez que OpenProject est accessible depuis le conteneur

#### 3. Ports déjà utilisés

- Changez les ports dans les variables d'environnement
- Redéployez la stack

### Logs détaillés

```bash
# Logs du conteneur
docker logs openproject-mcp-server

# Logs avec timestamps
docker logs -t openproject-mcp-server

# Logs en temps réel
docker logs -f openproject-mcp-server
```

## Scripts utiles

### Script de maintenance

```bash
#!/bin/bash
# maintenance.sh

echo "🔧 Maintenance OpenProject MCP Server"

# Vérifier le statut
echo "📊 Statut des conteneurs:"
docker ps | grep openproject-mcp

# Vérifier les logs récents
echo "📋 Logs récents:"
docker logs --tail 20 openproject-mcp-server

# Vérifier l'espace disque
echo "💾 Espace disque:"
df -h

# Nettoyer les images non utilisées
echo "🧹 Nettoyage des images:"
docker image prune -f
```

### Script de backup

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/backups/openproject-mcp"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup des volumes
docker run --rm -v mcp_logs:/data -v "$BACKUP_DIR":/backup alpine tar czf "/backup/mcp_logs_$DATE.tar.gz" /data
docker run --rm -v mcp_data:/data -v "$BACKUP_DIR":/backup alpine tar czf "/backup/mcp_data_$DATE.tar.gz" /data

echo "✅ Backup créé dans $BACKUP_DIR"
```

## Sécurité

### Recommandations

1. **Firewall** : Limitez l'accès aux ports 39127 et 39128
2. **Monitoring** : Surveillez les logs via Portainer
3. **Rotation des clés** : Changez régulièrement l'API Key
4. **Backup** : Automatisez les sauvegardes des volumes
5. **Mises à jour** : Maintenez l'image à jour

### Variables sensibles

- `OPENPROJECT_API_KEY` : Gardez cette clé secrète
- Utilisez les variables d'environnement Portainer pour les secrets
- Ne commitez jamais les clés dans le code

## Support

Pour toute question :

1. Consultez les logs dans Portainer
2. Vérifiez la configuration réseau
3. Testez la connectivité OpenProject
4. Consultez la documentation OpenProject API
