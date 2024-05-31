# ygg-rss-proxy

## Description

`ygg-rss-proxy` est une application Python qui sert de proxy pour récupérer des flux RSS et des fichiers torrent depuis un site protégé nécessitant une authentification. Cette application est conteneurisée à l'aide de Docker et utilise Poetry pour la gestion des dépendances.

## Fonctionnalités

- Authentifie sur le site et récupère les cookies de session.
- Récupère et modifie les flux RSS pour remplacer les URL de téléchargement par des URL de proxy.
- Récupère les fichiers torrent via le proxy avec authentification.

## Exigences

- Docker
- Docker Compose (pour la configuration Docker Compose)

## Variables d'Environnement

- `YGG_USER` : Votre nom d'utilisateur pour l'authentification.
- `YGG_PASS` : Votre mot de passe pour l'authentification.

## Comment Utiliser

### Exécution avec Docker

1. **Exécuter le Conteneur Docker**

   ```bash
   docker run -d -p 5000:5000 \
       -e YGG_USER=your_username \
       -e YGG_PASS=your_password \
       ghcr.io/LimeDrive/ygg-rss-proxy:latest
   ```

### Exécution avec Docker Compose

1. **Créer un fichier `docker-compose.yml`**

   ```yaml
   version: '3.8'

   services:
     ygg-rss-proxy:
       image: ghcr.io/LimeDrive/ygg-rss-proxy:latest
       ports:
         - "5000:5000"
       environment:
         YGG_USER: your_username
         YGG_PASS: your_password
   ```

2. **Exécuter Docker Compose**

   ```bash
   docker-compose up -d
   ```

## Comment Utiliser le Proxy

L'URL RSS à utiliser est la même que sur le site concerné, mais vous devez changer le nom de domaine de `www.ygg.re` à `localhost:5000`. Assurez-vous de bien conserver tous les paramètres car notre script les réutilise.

### Exemple

URL d'origine : `https://www.ygg.re/rss?action=generate&type=subcat&id=2183&passkey=xxxxxxxxxxxxxxxxxxxxxxxxxxx`

URL à utiliser dans le client torrent : `http://localhost:5000/rss?action=generate&type=subcat&id=2183&passkey=xxxxxxxxxxxxxxxxxxxxxxxxxxx`


## Structure du Projet

```
ygg-rss-proxy/
│
├── Dockerfile
├── pyproject.toml
├── poetry.lock
├── .github/
│   └── workflows/
│       └── release.yml
│
└── ygg_rss_proxy/
    ├── __init__.py
    └── proxy.py
```

## Contribuer

N'hésitez pas à ouvrir des issues ou à soumettre des pull requests si vous trouvez des bugs ou avez des suggestions de fonctionnalités.