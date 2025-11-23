# Intuis Connect with Netatmo - Custom Component for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/oThams/ha.svg)](https://github.com/oThams/ha/releases)
[![License](https://img.shields.io/github/license/oThams/ha.svg)](LICENSE)

Intégration personnalisée pour Home Assistant permettant de contrôler les radiateurs électriques équipés du module **Intuis Connect with Netatmo**.

## 📋 Description

Cette intégration permet de contrôler vos radiateurs électriques équipés du module Intuis Connect (anciennement Muller Intuitiv with Netatmo) directement depuis Home Assistant. Elle utilise l'API Netatmo Energy pour communiquer avec vos radiateurs.

### Marques compatibles

- **Intuis** (anciennement Muller Intuitiv)
- **Airelec**
- **Applimo**
- **Chaufelec**
- **Noirot**

## ✨ Fonctionnalités

- ✅ **Contrôle de température** : Définir la température cible de chaque radiateur/pièce
- ✅ **Modes HVAC** : Auto, Chauffage, Arrêt
- ✅ **Modes prédéfinis** :
  - 📅 Schedule (Programmation)
  - 🏠 Absent (Away)
  - ❄️ Hors-gel (Frost Guard)
  - 🔥 Boost (Chauffage maximum)
- ✅ **Lecture en temps réel** :
  - Température actuelle
  - Température cible
  - Puissance de chauffe demandée
  - État de connexion
- ✅ **Gestion des programmations** : Changer de planning horaire
- ✅ **Webhooks** : Mises à jour en temps réel via webhooks Netatmo
- ✅ **Services personnalisés** :
  - `intuis.set_schedule` - Changer la programmation
  - `intuis.set_preset_mode_with_end_datetime` - Définir un mode avec heure de fin

## 📦 Installation

### Installation via HACS (Recommandé)

1. Ouvrir HACS dans Home Assistant
2. Aller dans "Integrations"
3. Cliquer sur les 3 points en haut à droite et choisir "Custom repositories"
4. Ajouter l'URL du dépôt : `https://github.com/oThams/ha`
5. Catégorie : "Integration"
6. Rechercher "Intuis Connect with Netatmo"
7. Cliquer sur "Download"
8. Redémarrer Home Assistant

### Installation manuelle

1. Télécharger le dossier `custom_components/intuis` depuis ce dépôt
2. Copier le dossier dans `<config_dir>/custom_components/intuis`
3. Redémarrer Home Assistant

## 🔧 Configuration

### Prérequis : Créer une application Netatmo

Avant de configurer l'intégration, vous devez créer une application sur le portail développeur Netatmo :

1. Se connecter sur [https://dev.netatmo.com](https://dev.netatmo.com)
2. Aller dans "My Apps" puis "Create"
3. Remplir les informations :
   - **App Name** : Home Assistant Intuis
   - **Description** : Integration for Intuis radiators
   - **Webhook URL** : (laisser vide pour l'instant)
   - **Data Protection Officer** : (vos informations)
4. Cocher "I accept the terms and conditions"
5. Cliquer sur "Save"
6. Copier le **Client ID** et le **Client Secret**

### Configuration dans Home Assistant

#### 1. Ajouter les identifiants OAuth

1. Aller dans **Configuration** → **Intégrations**
2. Cliquer sur le bouton **+** en bas à droite
3. Rechercher "Application Credentials"
4. Sélectionner "Intuis Connect with Netatmo"
5. Entrer vos identifiants :
   - **Client ID** : Copié depuis dev.netatmo.com
   - **Client Secret** : Copié depuis dev.netatmo.com

#### 2. Ajouter l'intégration Intuis

1. Aller dans **Configuration** → **Intégrations**
2. Cliquer sur le bouton **+** en bas à droite
3. Rechercher "Intuis Connect with Netatmo"
4. Suivre les étapes de connexion OAuth
5. Autoriser l'accès à votre compte Netatmo

L'intégration va automatiquement découvrir tous vos radiateurs Intuis et créer une entité climate pour chaque pièce.

## 🎮 Utilisation

### Contrôle de base

Une fois configurée, chaque pièce avec un radiateur Intuis apparaîtra comme une entité `climate.xxx` dans Home Assistant.

#### Exemple d'automatisation

```yaml
automation:
  - alias: "Chauffage - Mode Absent le soir"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: climate.set_preset_mode
        target:
          entity_id: climate.salon
        data:
          preset_mode: "Away"

  - alias: "Chauffage - Retour à la programmation le matin"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: climate.set_preset_mode
        target:
          entity_id: climate.salon
        data:
          preset_mode: "Schedule"
```

### Services personnalisés

#### `intuis.set_schedule`

Change la programmation horaire active.

```yaml
service: intuis.set_schedule
target:
  entity_id: climate.salon
data:
  schedule_name: "Programmation Hiver"
```

#### `intuis.set_preset_mode_with_end_datetime`

Définit un mode prédéfini avec une heure de fin.

```yaml
service: intuis.set_preset_mode_with_end_datetime
target:
  entity_id: climate.salon
data:
  preset_mode: "Away"
  end_datetime: "2025-01-15 18:00:00"
```

### Carte Lovelace

Exemple de carte pour contrôler un radiateur :

```yaml
type: thermostat
entity: climate.salon
name: Salon
```

Ou pour une carte plus détaillée :

```yaml
type: entities
title: Chauffage Salon
entities:
  - entity: climate.salon
    type: custom:simple-thermostat
    control:
      - preset
      - hvac
    sensors:
      - entity: climate.salon
        attribute: heating_power_request
        name: Puissance
      - entity: climate.salon
        attribute: selected_schedule
        name: Programmation
```

## 🐛 Dépannage

### L'intégration ne trouve pas mes radiateurs

1. Vérifier que vos radiateurs sont bien visibles dans l'application Intuis/Netatmo
2. Vérifier que vous avez accordé les permissions `read_thermostat` et `write_thermostat`
3. Redémarrer Home Assistant
4. Vérifier les logs : **Configuration** → **Logs**

### Erreur d'authentification OAuth

1. Vérifier que le Client ID et Client Secret sont corrects
2. Supprimer l'intégration et la reconfigurer
3. Vérifier que votre application Netatmo est active sur dev.netatmo.com

### Les températures ne se mettent pas à jour

1. Vérifier que les webhooks sont enregistrés (voir les logs)
2. L'intégration poll l'API toutes les 5 minutes en plus des webhooks
3. Vérifier que vos radiateurs sont bien connectés au réseau

## 📊 Attributs disponibles

Chaque entité climate expose les attributs suivants :

| Attribut | Description |
|----------|-------------|
| `current_temperature` | Température actuelle de la pièce |
| `temperature` | Température cible |
| `hvac_mode` | Mode actuel (auto, heat, off) |
| `hvac_action` | Action en cours (heating, idle) |
| `preset_mode` | Mode prédéfini actif |
| `heating_power_request` | Puissance de chauffe demandée (0-100%) |
| `selected_schedule` | Nom de la programmation active |

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

- Signaler des bugs via les [Issues](https://github.com/oThams/ha/issues)
- Proposer des améliorations
- Soumettre des Pull Requests

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- [Netatmo](https://www.netatmo.com/) pour leur API
- [pyatmo](https://github.com/jabesq/netatmo-api-python) pour la bibliothèque Python
- La communauté Home Assistant

## 📧 Support

Pour toute question ou problème :
- Créer une [Issue](https://github.com/oThams/ha/issues)
- Consulter la [documentation Netatmo](https://dev.netatmo.com/apidocumentation/energy)

---

**Note** : Ce custom component n'est pas affilié à Netatmo ou Intuis. Il s'agit d'un projet communautaire indépendant.
