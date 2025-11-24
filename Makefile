.PHONY: help build up down restart logs shell clean test

help: ## Affiche cette aide
	@echo "Commandes disponibles pour tester Intuis Custom Component:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

build: ## Construit l'image Docker
	@echo "🔨 Construction de l'image Docker..."
	docker-compose build

up: ## Démarre Home Assistant
	@echo "🚀 Démarrage de Home Assistant..."
	docker-compose up -d
	@echo "✅ Home Assistant est démarré!"
	@echo "📍 Accès: http://localhost:8123"

down: ## Arrête Home Assistant
	@echo "🛑 Arrêt de Home Assistant..."
	docker-compose down

restart: ## Redémarre Home Assistant
	@echo "🔄 Redémarrage de Home Assistant..."
	docker-compose restart
	@echo "✅ Home Assistant a été redémarré!"

logs: ## Affiche les logs en temps réel
	docker-compose logs -f

shell: ## Ouvre un shell dans le conteneur
	docker-compose exec homeassistant bash

clean: ## Nettoie les données de test (⚠️ supprime la config)
	@echo "⚠️  ATTENTION: Cette commande va supprimer toutes les données de test!"
	@read -p "Êtes-vous sûr? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		rm -rf config/.storage config/home-assistant* config/.HA_VERSION; \
		echo "✅ Nettoyage terminé!"; \
	else \
		echo "❌ Annulé."; \
	fi

test: build up ## Build et démarre pour tester
	@echo ""
	@echo "✅ Environnement de test prêt!"
	@echo "📍 Accès: http://localhost:8123"
	@echo ""
	@echo "📋 Pour voir les logs:"
	@echo "   make logs"
	@echo ""
