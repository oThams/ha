# 🔧 Guide de Dépannage

## Problème : "Cannot connect" à http://localhost:8123

### Solution 1 : Vérifier que le conteneur est démarré
```bash
docker ps | grep intuis
```

Si le conteneur n'est pas listé, démarrez-le :
```bash
docker-compose up -d
```

### Solution 2 : Attendre le démarrage complet
Home Assistant prend 30-60 secondes pour démarrer. Vérifiez les logs :
```bash
docker-compose logs -f
```

Attendez de voir : `Starting Home Assistant`

### Solution 3 : Vérifier le mapping de port (macOS)
Sur macOS, `network_mode: host` ne fonctionne pas. Vérifiez que [docker-compose.yml](docker-compose.yml) utilise :
```yaml
ports:
  - "8123:8123"
```

Et NON :
```yaml
network_mode: host
```

### Solution 4 : Vérifier que le port n'est pas déjà utilisé
```bash
lsof -i :8123
```

Si un autre processus utilise le port 8123, arrêtez-le ou changez le port dans docker-compose.yml :
```yaml
ports:
  - "8124:8123"  # Utilise le port 8124 à la place
```

### Solution 5 : Rebuild complet
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Problème : Le custom component n'apparaît pas

### Solution 1 : Vérifier que le composant est monté
```bash
docker-compose exec homeassistant ls -la /config/custom_components/intuis/
```

Vous devriez voir tous les fichiers Python du composant.

### Solution 2 : Vérifier les logs
```bash
docker-compose logs | grep intuis
```

Vous devriez voir : `We found a custom integration intuis`

### Solution 3 : Redémarrer le conteneur
```bash
docker-compose restart
```

## Problème : Erreur d'authentification OAuth

### Solution : Vérifier les identifiants Netatmo
1. Vérifiez vos identifiants sur [dev.netatmo.com](https://dev.netatmo.com)
2. Assurez-vous que l'application Netatmo est active
3. Supprimez l'intégration dans HA et recréez-la
4. Vérifiez que vous avez bien ajouté les "Application Credentials" d'abord

## Problème : Les températures ne se mettent pas à jour

### Solution 1 : Vérifier les webhooks (limités en local)
Les webhooks Netatmo ne fonctionnent pas avec localhost. L'intégration utilisera le polling (toutes les 5 minutes).

Pour tester les webhooks, vous devez :
- Utiliser ngrok ou un service similaire
- Ou déployer sur un serveur avec IP publique

### Solution 2 : Forcer une mise à jour
```bash
# Redémarrer l'intégration via l'interface HA
# Ou redémarrer le conteneur
docker-compose restart
```

## Problème : Erreurs dans les logs

### Voir les logs détaillés
```bash
# Tous les logs
docker-compose logs -f

# Filtrer sur intuis uniquement
docker-compose logs -f | grep intuis

# Dernières 50 lignes
docker-compose logs --tail=50
```

### Activer les logs debug
Modifiez [config/configuration.yaml](config/configuration.yaml) :
```yaml
logger:
  default: info
  logs:
    custom_components.intuis: debug
    pyatmo: debug
```

Puis redémarrez :
```bash
docker-compose restart
```

## Problème : Le conteneur s'arrête tout seul

### Vérifier les logs d'erreur
```bash
docker-compose logs | tail -100
```

### Vérifier les ressources
```bash
docker stats homeassistant-intuis-test
```

### Augmenter la mémoire Docker
Dans Docker Desktop (macOS) :
1. Paramètres → Resources
2. Augmenter Memory à au moins 4 GB
3. Apply & Restart

## Problème : Modifications du code non prises en compte

### Solution : Le custom component est monté en read-only
Pour appliquer les modifications :
```bash
docker-compose restart
```

Le volume est monté en `:ro` (read-only) pour la sécurité. Les modifications du code local sont immédiatement visibles après redémarrage.

## Problème : Permission denied sur les fichiers

### Solution macOS
```bash
# Donner les permissions
chmod -R 755 custom_components/
chmod -R 644 config/*.yaml
```

## Commandes utiles pour le debug

### Entrer dans le conteneur
```bash
docker-compose exec homeassistant bash
```

### Vérifier la version de Home Assistant
```bash
docker-compose exec homeassistant cat /config/.HA_VERSION
```

### Lister les intégrations chargées
```bash
docker-compose logs | grep "Setting up"
```

### Vérifier l'état du healthcheck
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## Besoin d'aide supplémentaire ?

1. Consultez les logs complets :
   ```bash
   docker-compose logs > logs.txt
   ```

2. Créez une [Issue](https://github.com/oThams/ha/issues) avec :
   - Description du problème
   - Les logs pertinents
   - Votre système d'exploitation
   - Version de Docker

## Ressources

- [Documentation Home Assistant](https://www.home-assistant.io/docs/)
- [Documentation Docker](https://docs.docker.com/)
- [API Netatmo](https://dev.netatmo.com/apidocumentation/energy)
