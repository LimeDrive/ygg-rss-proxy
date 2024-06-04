# ygg-rss-proxy

# 🚨 Important Notice 🚨

**Currently, the site is under heavy cloudflare protection. It is recommended to use flaresolver in parallel to ensure smooth operation.**

Please be aware of this and make sure to use flaresolver accordingly to avoid any issues.

Big thanks to [@FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) for their amazing work!


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

- `YGG_USER` : Votre nom d'utilisateur pour l'authentification sur le site YGG. Par défaut. (OBLIGATOIRE)
- `YGG_PASS` : Votre mot de passe pour l'authentification sur le site YGG. Par défaut. (OBLIGATOIRE)
- `RSS_HOST`: L'hôte sur lequel le serveur RSS est en cours d'exécution. Par défaut, il est défini sur 'localhost'. C'est ici que l'on peut mettre le noms de container si l'on utilise docker compose.
- `RSS_PORT`: Le port sur lequel le serveur RSS est en cours d'exécution. Par défaut, il est défini sur '5000'.
- `RSS_SHEMA`: Le schéma (http ou https) utilisé pour accéder au serveur RSS. Par défaut, il est défini sur 'http'.
- `FLARESOLVERR_SHEMA`: Le schéma (http ou https) utilisé pour accéder à l'instance de Flaresolverr. Par défaut, il est défini sur 'http'.
- `FLARESOLVERR_HOST`: L'hôte sur lequel l'instance de Flaresolverr est en cours d'exécution. Par défaut, il est défini sur 'localhost'.
- `FLARESOLVERR_PORT`: Le port sur lequel l'instance de Flaresolverr est en cours d'exécution. Par défaut, il est défini sur '8191'.
- `YGG_URL`: L'URL du site YGG. définie par default.
- `INTERNAL_PORT`: Le port sur lequel le serveur proxy interne est en cours d'exécution. Par défaut, il est défini sur '5000'.
- `LOG_LEVEL`: Le niveau de journalisation pour le serveur proxy. Par défaut, il est défini sur 'INFO'.

## Comment Utiliser

## 🚨 Important Notice 🚨

**Attention, l'installation nécessite FlareSolverr quand le site et sous protocole cloudflare. C'est a dire à peu près tout le temps.**

Please be aware of this and make sure to use FlareSolverr accordingly to avoid any issues.

For optimal performance and to bypass Cloudflare's protection, it is essential to run FlareSolverr alongside this application. This is because the site is frequently protected by Cloudflare, which can cause difficulties in accessing the content.

### Exécution avec Docker

1. **Exécuter le Conteneur Docker**

   ```bash
   docker run -d -p 5000:5000 \
       -e YGG_USER=your_username \
       -e YGG_PASS=your_password \
       -e FLARESOLVERR_HOST=flaresolverr_host \
       -e FLARESOLVERR_PORT=flaresolverr_port \
       ghcr.io/limedrive/ygg-rss-proxy:latest
   ```

### Exemple avec Docker Compose + 🚨 FlareSolverr 🚨 + Qbittorrent

Cet exemple utilise Docker Compose pour lancer l'application `ygg-rss-proxy`, FlareSolverr, et Qbittorrent en même temps.

1. **Créer un fichier `docker-compose.yml`**

   ```yaml
   version: "3.8"

   services:

      qbittorrent:
         image: lscr.io/linuxserver/qbittorrent:latest
         container_name: qbittorrent
         environment:
            PUID: 1000
            PGID: 1000
            TZ: Europe/Paris
            WEBUI_PORT: 8080
         volumes:
            - ./config:/config
            - ./downloads:/downloads
         ports:
            - 6881:6881
            - 6881:6881/udp
            - 8080:8080
         restart: unless-stopped

      ygg-rss-proxy:
         image: ghcr.io/limedrive/ygg-rss-proxy:latest
         container_name: ygg-rss-proxy
         expose:
            - 5000
         environment:
            YGG_USER: <Username>
            YGG_PASS: <Redacted>
            RSS_HOST: ygg-rss-proxy
            FLARESOLVERR_HOST: flaresolverr
            FLARESOLVERR_PORT: 8191
            LOG_LEVEL: INFO
         restart: unless-stopped
         depends_on:
            - flaresolverr

      flaresolverr:
         image: ghcr.io/flaresolverr/flaresolverr:latest
         container_name: flaresolverr
         environment:
            LOG_LEVEL: info
            CAPTCHA_SOLVER: none
         expose:
            - 8191
         restart: unless-stopped
   ```

2. **Exécuter Docker Compose**

   ```bash
   docker-compose up -d
   ```

## Comment Utiliser le Proxy

L'URL RSS à utiliser est la même que sur le site concerné, mais vous devez changer le nom de domaine de `www.ygg.re` à `localhost:5000` ou tout autre HOST que vous avez définie dans les variable `RSS_HOST` `RSS_PORT`. Assurez-vous de bien conserver tous les paramètres car notre script les réutilise.

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