# Guide de Test - Intuis Connect with Netatmo

Ce guide explique comment tester le custom component Intuis dans un environnement Docker isolé.

## 📋 Prérequis

- Docker installé et en cours d'exécution
- Docker Compose installé
- Compte développeur Netatmo avec Client ID et Client Secret ([dev.netatmo.com](https://dev.netatmo.com))

## 🚀 Démarrage Rapide

### Méthode 1 : Makefile (recommandé)

```bash
# Afficher l'aide
make help

# Démarrer l'environnement de test
make test

# Voir les logs en temps réel
make logs

# Redémarrer
make restart

# Arrêter
make down

# Nettoyer les données (⚠️ supprime la config)
make clean
```

### Méthode 2 : Script automatique

```bash
./start-test.sh
```

Ce script va :
1. Vérifier que Docker est en cours d'exécution
2. Créer les dossiers nécessaires
3. Construire l'image Docker
4. Démarrer Home Assistant
5. Afficher les logs en temps réel

### Méthode 3 : Commandes Docker Compose

```bash
# Construire l'image
docker-compose build

# Démarrer le conteneur
docker-compose up -d

# Voir les logs
docker-compose logs -f
```

## 🌐 Accès à Home Assistant

Une fois démarré, Home Assistant sera accessible à :
- **URL** : http://localhost:8123
- **Délai de démarrage** : 30-60 secondes

## 🔧 Configuration de l'intégration

### 1. Premier démarrage

Lors du premier accès à Home Assistant :
1. Créez un compte administrateur
2. Configurez votre localisation
3. Terminez l'onboarding

### 2. Ajouter les identifiants OAuth Netatmo

1. Allez dans **Configuration** → **Intégrations**
2. Cliquez sur **+ AJOUTER UNE INTÉGRATION**
3. Recherchez **"Application Credentials"**
4. Sélectionnez **"Intuis Connect with Netatmo"**
5. Entrez vos identifiants :
   - **Client ID** : Votre Client ID depuis dev.netatmo.com
   - **Client Secret** : Votre Client Secret depuis dev.netatmo.com
6. Cliquez sur **Soumettre**

### 3. Ajouter l'intégration Intuis

1. Dans **Configuration** → **Intégrations**
2. Cliquez sur **+ AJOUTER UNE INTÉGRATION**
3. Recherchez **"Intuis Connect with Netatmo"**
4. Cliquez sur **Configurer**
5. Suivez le flux OAuth pour vous connecter à votre compte Netatmo
6. Autorisez l'accès à vos radiateurs

L'intégration va automatiquement découvrir tous vos radiateurs Intuis.

## 🔍 Vérification

### Vérifier que l'intégration est chargée

Dans les logs, vous devriez voir :
```
INFO (MainThread) [homeassistant.setup] Setting up intuis
INFO (MainThread) [homeassistant.setup] Setup of domain intuis took X seconds
```

### Vérifier les entités

1. Allez dans **Outils de développement** → **États**
2. Recherchez les entités `climate.` avec vos pièces
3. Vérifiez que les attributs sont présents :
   - `current_temperature`
   - `temperature`
   - `hvac_mode`
   - `preset_mode`
   - `heating_power_request`

## 📊 Tests à effectuer

### Test 1 : Changement de température
```yaml
service: climate.set_temperature
target:
  entity_id: climate.salon
data:
  temperature: 21
```

### Test 2 : Changement de mode HVAC
```yaml
service: climate.set_hvac_mode
target:
  entity_id: climate.salon
data:
  hvac_mode: heat
```

### Test 3 : Changement de mode prédéfini
```yaml
service: climate.set_preset_mode
target:
  entity_id: climate.salon
data:
  preset_mode: "Away"
```

### Test 4 : Service personnalisé - Changement de programmation
```yaml
service: intuis.set_schedule
target:
  entity_id: climate.salon
data:
  schedule_name: "Programmation Hiver"
```

### Test 5 : Service personnalisé - Mode avec heure de fin
```yaml
service: intuis.set_preset_mode_with_end_datetime
target:
  entity_id: climate.salon
data:
  preset_mode: "Away"
  end_datetime: "2025-01-15 18:00:00"
```

## 🐛 Débogage

### Activer les logs détaillés

Modifiez `config/configuration.yaml` et ajoutez :

```yaml
logger:
  default: info
  logs:
    custom_components.intuis: debug
    pyatmo: debug
```

Puis redémarrez le conteneur :
```bash
docker-compose restart
```

### Voir les logs en temps réel

```bash
docker-compose logs -f
```

### Filtrer les logs de l'intégration

```bash
docker-compose logs -f | grep intuis
```

### Accéder au conteneur

```bash
docker-compose exec homeassistant bash
```

### Inspecter les fichiers du custom component

```bash
docker-compose exec homeassistant ls -la /config/custom_components/intuis/
```

## 🔄 Modifications du code

Le custom component est monté en tant que volume, donc :

1. **Modifications détectées automatiquement** : Non, il faut redémarrer
2. **Pour appliquer les changements** :
   ```bash
   docker-compose restart
   ```
3. **Pour un rechargement complet** :
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## 📁 Structure des fichiers de test

```
.
├── Dockerfile                    # Image Docker Home Assistant
├── docker-compose.yml            # Configuration Docker Compose
├── start-test.sh                 # Script de démarrage rapide
├── config/                       # Configuration Home Assistant
│   ├── configuration.yaml        # Config principale
│   ├── automations.yaml          # Automatisations
│   ├── scripts.yaml              # Scripts
│   ├── scenes.yaml               # Scènes
│   └── secrets.yaml              # Secrets (non versionné)
└── custom_components/
    └── intuis/                   # Custom component à tester
```

## 🛑 Arrêt et nettoyage

### Arrêter le conteneur
```bash
docker-compose down
```

### Arrêter et supprimer les données
```bash
docker-compose down -v
rm -rf config/.storage config/home-assistant*
```

### Supprimer l'image Docker
```bash
docker-compose down
docker rmi ha-homeassistant
```

## 💡 Astuces

### Redémarrage rapide après modification
```bash
docker-compose restart && docker-compose logs -f
```

### Sauvegarder la configuration
```bash
cp -r config config.backup
```

### Restaurer une configuration
```bash
rm -rf config
cp -r config.backup config
docker-compose restart
```

### Tester sur un réseau spécifique
Modifiez `docker-compose.yml` et remplacez `network_mode: host` par :
```yaml
ports:
  - "8123:8123"
networks:
  - ha-test-network

networks:
  ha-test-network:
    driver: bridge
```

## 🔗 Ressources

- [Documentation Home Assistant](https://www.home-assistant.io/docs/)
- [Documentation Docker](https://docs.docker.com/)
- [API Netatmo Energy](https://dev.netatmo.com/apidocumentation/energy)
- [Guide développeur Custom Components](https://developers.home-assistant.io/docs/creating_component_index)

## 📝 Notes importantes

1. **Données persistantes** : Le dossier `config/` est monté en volume. Les données sont conservées entre les redémarrages.
2. **Mode privilégié** : Le conteneur fonctionne en mode privilégié pour accéder à certaines fonctionnalités système.
3. **Network host** : Utilise le réseau de l'hôte pour faciliter la découverte de périphériques.
4. **Webhooks** : Les webhooks Netatmo nécessitent une URL publique. En local, seul le polling fonctionnera.

## ⚠️ Limitations en environnement Docker

- Les webhooks Netatmo ne fonctionneront pas avec `localhost`
- Pour tester les webhooks, utilisez un service comme [ngrok](https://ngrok.com/) ou déployez sur un serveur avec IP publique
- Certaines intégrations nécessitant l'accès au matériel local peuvent ne pas fonctionner
