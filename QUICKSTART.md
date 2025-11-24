# 🚀 Quick Start - Test Intuis avec Docker

## En 3 étapes

### 1️⃣ Prérequis
- Docker installé et en cours d'exécution
- Compte développeur Netatmo ([dev.netatmo.com](https://dev.netatmo.com))

### 2️⃣ Démarrer Home Assistant
```bash
make test
# ou
./start-test.sh
```

### 3️⃣ Configurer
1. Ouvrir http://localhost:8123
2. Terminer l'onboarding (créer compte admin)
3. Ajouter l'intégration "Intuis Connect with Netatmo"
4. Suivre le flux OAuth

## Commandes utiles

```bash
make logs       # Voir les logs
make restart    # Redémarrer
make down       # Arrêter
make clean      # Nettoyer les données
```

## 📖 Documentation complète
- [README.md](README.md) - Documentation de l'intégration
- [TESTING.md](TESTING.md) - Guide de test détaillé

## 🐛 Problème ?
Vérifier les logs :
```bash
make logs | grep intuis
```
