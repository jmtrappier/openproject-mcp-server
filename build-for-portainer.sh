#!/bin/bash

# Script de build d'image Docker pour déploiement Portainer
# OpenProject MCP Server

set -e

# Configuration
IMAGE_NAME="openproject-mcp-server"
IMAGE_TAG="${1:-latest}"
REGISTRY="${2:-}"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Vérification des prérequis
check_prerequisites() {
    log_info "Vérification des prérequis..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé"
        exit 1
    fi
    
    if [ ! -f "Dockerfile" ]; then
        log_error "Dockerfile non trouvé dans le répertoire courant"
        exit 1
    fi
    
    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt non trouvé"
        exit 1
    fi
    
    log_info "Prérequis vérifiés ✓"
}

# Construction de l'image
build_image() {
    log_step "Construction de l'image Docker..."
    
    # Nom complet de l'image
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    else
        FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
    fi
    
    log_info "Construction de l'image: $FULL_IMAGE_NAME"
    
    # Build avec cache et optimisations
    docker build \
        --tag "$FULL_IMAGE_NAME" \
        --tag "${IMAGE_NAME}:latest" \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --progress=plain \
        .
    
    if [ $? -eq 0 ]; then
        log_info "Image construite avec succès ✓"
    else
        log_error "Erreur lors de la construction de l'image"
        exit 1
    fi
}

# Vérification de l'image
verify_image() {
    log_step "Vérification de l'image..."
    
    # Vérifier que l'image existe
    if docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" > /dev/null 2>&1; then
        log_info "Image vérifiée ✓"
        
        # Afficher les informations de l'image
        log_info "Informations de l'image:"
        docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" --format='
        Image ID: {{.Id}}
        Created: {{.Created}}
        Size: {{.Size}} bytes
        Architecture: {{.Architecture}}
        OS: {{.Os}}
        '
    else
        log_error "Image non trouvée après construction"
        exit 1
    fi
}

# Test de l'image
test_image() {
    log_step "Test de l'image..."
    
    # Test rapide de démarrage du conteneur
    log_info "Test de démarrage du conteneur..."
    
    CONTAINER_ID=$(docker run -d \
        --name "test-${IMAGE_NAME}" \
        --env OPENPROJECT_URL=http://test:8080 \
        --env OPENPROJECT_API_KEY=test_key_123456789012345678901234567890 \
        --env MCP_HOST=0.0.0.0 \
        --env MCP_PORT=8080 \
        --env MCP_LOG_LEVEL=INFO \
        "${IMAGE_NAME}:${IMAGE_TAG}")
    
    if [ $? -eq 0 ]; then
        log_info "Conteneur de test démarré ✓"
        
        # Attendre un peu puis vérifier qu'il tourne
        sleep 5
        
        if docker ps | grep -q "test-${IMAGE_NAME}"; then
            log_info "Conteneur de test fonctionne ✓"
        else
            log_warn "Conteneur de test ne semble pas fonctionner"
        fi
        
        # Nettoyer le conteneur de test
        docker stop "test-${IMAGE_NAME}" > /dev/null 2>&1
        docker rm "test-${IMAGE_NAME}" > /dev/null 2>&1
        log_info "Conteneur de test nettoyé ✓"
    else
        log_error "Erreur lors du test de l'image"
        exit 1
    fi
}

# Sauvegarde de l'image (optionnel)
save_image() {
    if [ "$3" = "--save" ]; then
        log_step "Sauvegarde de l'image..."
        
        SAVE_FILE="${IMAGE_NAME}-${IMAGE_TAG}.tar"
        log_info "Sauvegarde vers: $SAVE_FILE"
        
        docker save "${IMAGE_NAME}:${IMAGE_TAG}" -o "$SAVE_FILE"
        
        if [ $? -eq 0 ]; then
            log_info "Image sauvegardée ✓"
            log_info "Taille du fichier: $(du -h "$SAVE_FILE" | cut -f1)"
        else
            log_error "Erreur lors de la sauvegarde"
            exit 1
        fi
    fi
}

# Affichage des informations finales
show_final_info() {
    log_info "Build terminé avec succès !"
    echo ""
    echo "📦 Image Docker créée:"
    echo "   - Nom: ${IMAGE_NAME}:${IMAGE_TAG}"
    echo "   - Tag latest: ${IMAGE_NAME}:latest"
    echo ""
    echo "🚀 Pour déployer avec Portainer:"
    echo "   1. Allez dans Portainer > Images"
    echo "   2. Vérifiez que l'image '${IMAGE_NAME}' est présente"
    echo "   3. Créez un nouveau stack avec le docker-compose"
    echo ""
    echo "📋 Commandes utiles:"
    echo "   - Lister les images: docker images | grep ${IMAGE_NAME}"
    echo "   - Supprimer l'image: docker rmi ${IMAGE_NAME}:${IMAGE_TAG}"
    echo "   - Charger l'image: docker load -i ${IMAGE_NAME}-${IMAGE_TAG}.tar"
    echo ""
}

# Fonction principale
main() {
    echo "🏗️  Build d'image Docker pour Portainer"
    echo "========================================"
    echo ""
    
    check_prerequisites
    build_image
    verify_image
    test_image
    save_image "$@"
    show_final_info
}

# Gestion des arguments
case "${1:-help}" in
    "help"|"-h"|"--help")
        echo "Usage: $0 [TAG] [REGISTRY] [--save]"
        echo ""
        echo "Arguments:"
        echo "  TAG       - Tag de l'image (défaut: latest)"
        echo "  REGISTRY  - Registry Docker (optionnel)"
        echo "  --save    - Sauvegarder l'image en fichier .tar"
        echo ""
        echo "Exemples:"
        echo "  $0                    # Build avec tag 'latest'"
        echo "  $0 v1.0.0            # Build avec tag 'v1.0.0'"
        echo "  $0 latest myregistry # Build et push vers registry"
        echo "  $0 v1.0.0 '' --save  # Build et sauvegarde en fichier"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
