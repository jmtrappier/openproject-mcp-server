#!/bin/bash

# Script de test pour vérifier le déploiement Portainer
# OpenProject MCP Server

set -e

# Configuration
CONTAINER_NAME="openproject-mcp-server"
MCP_PORT=39127
STATUS_PORT=39128

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Test 1: Vérifier que le conteneur existe
test_container_exists() {
    log_step "Test 1: Vérification du conteneur"
    
    if docker ps | grep -q "$CONTAINER_NAME"; then
        log_info "✅ Conteneur $CONTAINER_NAME en cours d'exécution"
        return 0
    else
        log_error "❌ Conteneur $CONTAINER_NAME non trouvé ou arrêté"
        return 1
    fi
}

# Test 2: Vérifier les ports
test_ports() {
    log_step "Test 2: Vérification des ports"
    
    # Test port MCP
    if netstat -tlnp 2>/dev/null | grep -q ":$MCP_PORT "; then
        log_info "✅ Port MCP $MCP_PORT ouvert"
    else
        log_warn "⚠️  Port MCP $MCP_PORT non accessible"
    fi
    
    # Test port status
    if netstat -tlnp 2>/dev/null | grep -q ":$STATUS_PORT "; then
        log_info "✅ Port Status $STATUS_PORT ouvert"
    else
        log_warn "⚠️  Port Status $STATUS_PORT non accessible"
    fi
}

# Test 3: Test de connectivité HTTP
test_http_connectivity() {
    log_step "Test 3: Test de connectivité HTTP"
    
    # Test endpoint de statut
    if curl -s "http://localhost:$STATUS_PORT/health" > /dev/null; then
        log_info "✅ Endpoint /health accessible"
        
        # Afficher la réponse
        echo "📊 Réponse du health check:"
        curl -s "http://localhost:$STATUS_PORT/health" | python3 -m json.tool 2>/dev/null || curl -s "http://localhost:$STATUS_PORT/health"
    else
        log_error "❌ Endpoint /health non accessible"
    fi
    
    # Test endpoint racine
    if curl -s "http://localhost:$STATUS_PORT/" > /dev/null; then
        log_info "✅ Endpoint racine accessible"
    else
        log_warn "⚠️  Endpoint racine non accessible"
    fi
}

# Test 4: Vérifier les logs
test_logs() {
    log_step "Test 4: Vérification des logs"
    
    if docker logs "$CONTAINER_NAME" 2>&1 | grep -q "Starting OpenProject MCP Server"; then
        log_info "✅ Serveur MCP démarré correctement"
    else
        log_warn "⚠️  Serveur MCP n'a pas démarré correctement"
    fi
    
    # Afficher les dernières lignes de logs
    echo "📋 Dernières lignes de logs:"
    docker logs --tail 10 "$CONTAINER_NAME"
}

# Test 5: Vérifier la santé du conteneur
test_container_health() {
    log_step "Test 5: Vérification de la santé du conteneur"
    
    HEALTH_STATUS=$(docker inspect "$CONTAINER_NAME" --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
    
    case "$HEALTH_STATUS" in
        "healthy")
            log_info "✅ Conteneur en bonne santé"
            ;;
        "unhealthy")
            log_error "❌ Conteneur en mauvaise santé"
            ;;
        "starting")
            log_warn "⚠️  Conteneur en cours de démarrage"
            ;;
        *)
            log_warn "⚠️  Statut de santé inconnu: $HEALTH_STATUS"
            ;;
    esac
}

# Test 6: Vérifier les volumes
test_volumes() {
    log_step "Test 6: Vérification des volumes"
    
    # Vérifier que les volumes sont montés
    if docker inspect "$CONTAINER_NAME" --format='{{range .Mounts}}{{.Destination}} {{end}}' | grep -q "/app/logs"; then
        log_info "✅ Volume logs monté"
    else
        log_warn "⚠️  Volume logs non monté"
    fi
    
    if docker inspect "$CONTAINER_NAME" --format='{{range .Mounts}}{{.Destination}} {{end}}' | grep -q "/app/data"; then
        log_info "✅ Volume data monté"
    else
        log_warn "⚠️  Volume data non monté"
    fi
}

# Fonction principale
main() {
    echo "🧪 Test de déploiement Portainer - OpenProject MCP Server"
    echo "========================================================"
    echo ""
    
    local tests_passed=0
    local total_tests=6
    
    test_container_exists && ((tests_passed++))
    test_ports && ((tests_passed++))
    test_http_connectivity && ((tests_passed++))
    test_logs && ((tests_passed++))
    test_container_health && ((tests_passed++))
    test_volumes && ((tests_passed++))
    
    echo ""
    echo "📊 Résumé des tests:"
    echo "   Tests réussis: $tests_passed/$total_tests"
    
    if [ $tests_passed -eq $total_tests ]; then
        log_info "🎉 Tous les tests sont passés ! Le déploiement est réussi."
        exit 0
    else
        log_warn "⚠️  Certains tests ont échoué. Vérifiez la configuration."
        exit 1
    fi
}

# Gestion des arguments
case "${1:-test}" in
    "test")
        main
        ;;
    "quick")
        test_container_exists
        test_http_connectivity
        ;;
    "logs")
        docker logs -f "$CONTAINER_NAME"
        ;;
    "status")
        docker ps | grep "$CONTAINER_NAME"
        docker inspect "$CONTAINER_NAME" --format='{{.State.Health.Status}}'
        ;;
    *)
        echo "Usage: $0 {test|quick|logs|status}"
        echo "  test   - Exécuter tous les tests (défaut)"
        echo "  quick  - Tests rapides seulement"
        echo "  logs   - Afficher les logs en temps réel"
        echo "  status - Afficher le statut du conteneur"
        exit 1
        ;;
esac
