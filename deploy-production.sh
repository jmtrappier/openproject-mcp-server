#!/bin/bash

# Script de déploiement OpenProject MCP Server pour Production
# Environnement sécurisé sans certificat SSL

set -e

# Configuration
COMPOSE_FILE="docker-compose-production.yml"
ENV_FILE="env.production"
PROJECT_NAME="openproject-mcp"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérification des prérequis
check_prerequisites() {
    log_info "Vérification des prérequis..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose n'est pas installé"
        exit 1
    fi
    
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Fichier d'environnement $ENV_FILE non trouvé"
        exit 1
    fi
    
    log_info "Prérequis vérifiés ✓"
}

# Vérification de la configuration
check_configuration() {
    log_info "Vérification de la configuration..."
    
    # Vérifier que l'API key est configurée
    if grep -q "your_40_character_api_key_here" "$ENV_FILE"; then
        log_error "Veuillez configurer votre API key OpenProject dans $ENV_FILE"
        exit 1
    fi
    
    # Vérifier que l'URL OpenProject est configurée
    if ! grep -q "OPENPROJECT_URL=http://" "$ENV_FILE"; then
        log_error "Veuillez configurer l'URL OpenProject dans $ENV_FILE"
        exit 1
    fi
    
    log_info "Configuration vérifiée ✓"
}

# Construction et déploiement
deploy() {
    log_info "Démarrage du déploiement..."
    
    # Arrêter les conteneurs existants
    log_info "Arrêt des conteneurs existants..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down || true
    
    # Nettoyer les images obsolètes
    log_info "Nettoyage des images obsolètes..."
    docker image prune -f
    
    # Construire et démarrer
    log_info "Construction et démarrage des services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
    
    log_info "Déploiement terminé ✓"
}

# Vérification du statut
check_status() {
    log_info "Vérification du statut des services..."
    
    # Attendre que les services démarrent
    sleep 10
    
    # Vérifier le statut des conteneurs
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps | grep -q "Up"; then
        log_info "Services démarrés avec succès ✓"
    else
        log_error "Erreur lors du démarrage des services"
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs
        exit 1
    fi
    
    # Vérifier la santé du service
    log_info "Vérification de la santé du service..."
    sleep 5
    
    # Récupérer le port de statut
    STATUS_PORT=$(grep "MCP_STATUS_PORT" "$ENV_FILE" | cut -d'=' -f2)
    STATUS_PORT=${STATUS_PORT:-39128}
    
    if curl -s "http://localhost:$STATUS_PORT/health" > /dev/null; then
        log_info "Service MCP en bonne santé ✓"
    else
        log_warn "Service MCP non accessible sur le port de statut"
    fi
}

# Affichage des informations de connexion
show_connection_info() {
    log_info "Informations de connexion:"
    
    # Récupérer les ports depuis le fichier d'environnement
    MCP_PORT=$(grep "MCP_EXTERNAL_PORT" "$ENV_FILE" | cut -d'=' -f2)
    MCP_PORT=${MCP_PORT:-39127}
    STATUS_PORT=$(grep "MCP_STATUS_PORT" "$ENV_FILE" | cut -d'=' -f2)
    STATUS_PORT=${STATUS_PORT:-39128}
    
    echo ""
    echo "🌐 Serveur MCP accessible sur:"
    echo "   - Port principal: $MCP_PORT"
    echo "   - Port de statut: $STATUS_PORT"
    echo ""
    echo "📊 Endpoints disponibles:"
    echo "   - Statut: http://localhost:$STATUS_PORT/health"
    echo "   - Info: http://localhost:$STATUS_PORT/"
    echo ""
    echo "🔧 Commandes utiles:"
    echo "   - Logs: docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE logs -f"
    echo "   - Arrêt: docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE down"
    echo "   - Redémarrage: docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE restart"
    echo ""
}

# Fonction principale
main() {
    echo "🚀 Déploiement OpenProject MCP Server pour Production"
    echo "=================================================="
    echo ""
    
    check_prerequisites
    check_configuration
    deploy
    check_status
    show_connection_info
    
    log_info "Déploiement terminé avec succès !"
}

# Gestion des arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "status")
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
        ;;
    "logs")
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs -f
        ;;
    "stop")
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
        ;;
    "restart")
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" restart
        ;;
    *)
        echo "Usage: $0 {deploy|status|logs|stop|restart}"
        echo "  deploy   - Déployer le service (défaut)"
        echo "  status   - Afficher le statut des services"
        echo "  logs     - Afficher les logs en temps réel"
        echo "  stop     - Arrêter les services"
        echo "  restart  - Redémarrer les services"
        exit 1
        ;;
esac
