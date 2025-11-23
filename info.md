# Intuis Connect with Netatmo

Intégration personnalisée pour Home Assistant permettant de contrôler les radiateurs électriques équipés du module **Intuis Connect with Netatmo**.

## Fonctionnalités principales

- ✅ Contrôle de température pour chaque radiateur/pièce
- ✅ Modes HVAC : Auto, Chauffage, Arrêt
- ✅ Modes prédéfinis : Programmation, Absent, Hors-gel, Boost
- ✅ Lecture en temps réel de la température et de la puissance de chauffe
- ✅ Gestion des programmations horaires
- ✅ Webhooks pour mises à jour instantanées

## Radiateurs compatibles

Compatible avec les radiateurs électriques équipés du module Intuis Connect des marques :

- **Intuis** (anciennement Muller Intuitiv)
- **Airelec**
- **Applimo**
- **Chaufelec**
- **Noirot**

## Configuration

### Prérequis

Avant d'installer cette intégration, vous devez créer une application Netatmo :

1. Créer un compte sur [dev.netatmo.com](https://dev.netatmo.com)
2. Créer une nouvelle application
3. Récupérer le Client ID et Client Secret

### Installation

1. Installer via HACS
2. Redémarrer Home Assistant
3. Aller dans Configuration → Intégrations
4. Ajouter "Application Credentials" avec vos identifiants Netatmo
5. Ajouter l'intégration "Intuis Connect with Netatmo"
6. Suivre le processus d'authentification OAuth

## Utilisation

Une fois configurée, chaque pièce équipée d'un radiateur Intuis apparaîtra comme une entité `climate` dans Home Assistant.

### Exemple d'automatisation

```yaml
automation:
  - alias: "Mode Absent le soir"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: climate.set_preset_mode
        target:
          entity_id: climate.salon
        data:
          preset_mode: "Away"
```

## Support

Pour toute question ou problème :
- [Documentation complète](https://github.com/oThams/ha/blob/main/README.md)
- [Signaler un bug](https://github.com/oThams/ha/issues)

---

**Note** : Cette intégration n'est pas affiliée à Netatmo ou Intuis.
