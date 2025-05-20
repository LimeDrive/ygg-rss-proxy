Fork du projet ygg-rss-proxy.

La branch main contient actuellement des modifications qui permettent d'utiliser la version [flaresolverr](https://github.com/21hsmw/FlareSolverr) de [@21hsmw](https://github.com/21hsmw). (Version qui n'est plus fonctionnelle).

Une version fonctionnelle est disponible sur la branche `byparr`. Le code n'est pas propre mais il est fonctionnel. Il utilise [byparr](https://github.com/ThePhaseless/Byparr) plutot que flaresolverr, qui resoud les capatchas cloudflare a l'heure ou j'ecris ces lignes.

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

## Configuration

Le scripte peut désormais être configuré en utilisant des variables d'environnement, un ficher `.env` ou les docker secrets. Pour les Docker secrets, il faut les nommer comme les variable d'environnement.

### Variables d'Environnement

- `YGG_USER` : Votre nom d'utilisateur pour l'authentification sur le site YGG. Par défaut. (OBLIGATOIRE)
- `YGG_PASS` : Votre mot de passe pour l'authentification sur le site YGG. Par défaut. (OBLIGATOIRE)
- `YGG_URL`: L'URL du site YGG. définie par default.
- `RSS_HOST`: L'hôte sur lequel le serveur RSS est en cours d'exécution. Par défaut, il est défini sur 'localhost'. **C'est ici que l'on peut mettre le noms de container si l'on utilise docker compose.**
- `RSS_PORT`: Le port sur lequel le serveur RSS est en cours d'exécution. Par défaut, il est défini sur '8080'.
- `RSS_SHEMA`: Le schéma (http ou https) utilisé pour accéder au serveur RSS. Par défaut, il est défini sur 'http'.
- `FLARESOLVERR_SHEMA`: Le schéma (http ou https) utilisé pour accéder à l'instance de Flaresolverr. Par défaut, il est défini sur 'http'.
- `FLARESOLVERR_HOST`: L'hôte sur lequel l'instance de Flaresolverr est en cours d'exécution. Par défaut, il est défini sur 'localhost'.
- `FLARESOLVERR_PORT`: Le port sur lequel l'instance de Flaresolverr est en cours d'exécution. Par défaut, il est défini sur '8191'.
- `GUNICORN_PORT`: Le port sur lequel le serveur proxy interne est en cours d'exécution. Par défaut, il est défini sur '8080'.
- `GUNICORN_WORKERS`: Le nombre de travailleurs Gunicorn à utiliser. Par défaut, il est défini sur '4'.
- `GUNICORN_BINDER`: L'adresse IP sur laquelle le serveur proxy interne est lié. Par défaut, il est défini sur '0.0.0.0'.
- `GUNICORN_TIMEOUT`: Le délai d'attente pour les requêtes Gunicorn. Par défaut, il est défini sur '120'.
- `LOG_PATH`: Le chemin du fichier journal pour le serveur proxy. Par défaut, il est défini sur '/app/config/logs/rss-proxy.log'. Il y a une rotaion de fichier journal déja configuré. Attention c'est le chemin dans le container.
- `LOG_LEVEL`: Le niveau de journalisation pour le serveur proxy. Par défaut, il est défini sur 'INFO'.
- `LOG_REDACTED`: Si les journaux doivent être anonymisés. Par défaut, il est défini sur 'True'.
- `DB_PATH`: Le chemin de la base de données SQLite pour le serveur proxy. Par défaut, il est défini sur '/app/config/rss-proxy.db'. Attention c'est le chemin dans le container.
- `SECRET_KEY`: La clé secrète utilisée pour la signature des cookies de session. Par défaut, il est défini sur 'superkey_that_can_be_changed'. Sécurité suplémentaire pour chiffré la base de donnée.



## Comment Utiliser

## 🚨 Important Notice 🚨

**Attention, l'installation nécessite FlareSolverr quand le site et sous protocole cloudflare. C'est a dire à peu près tout le temps.**

Please be aware of this and make sure to use FlareSolverr accordingly to avoid any issues.

For optimal performance and to bypass Cloudflare's protection, it is essential to run FlareSolverr alongside this application. This is because the site is frequently protected by Cloudflare, which can cause difficulties in accessing the content.

### Exemple avec Docker Compose + 🚨 FlareSolverr 🚨 + Qbittorrent

Cet exemple utilise Docker Compose pour lancer l'application `ygg-rss-proxy`, FlareSolverr, et Qbittorrent en même temps.
C'est pour illustré l'utilisation de l'application avec d'autres services.

**Attention, Flaresolverr est un super projet 🤩 mais il peut être très gourmand en ressources si des petits malins trouve votre instance et ne doit pas être exoposé en dehors de votre réseau local. Il est donc recommandé de ne pas binder le port 8191 sur l'hôte. On utilisera donc le nom du container pour communiquer entre les deux pour rester dans le réseau docker.**

1. **Créer un fichier `docker-compose.yml`**

   ```yaml
   services:
      ygg-rss-proxy:
         container_name: ygg-rss-proxy
         ports:
            - 8080:8080
         environment:
            TZ: Europe/Paris
            YGG_USER: 'User'
            YGG_PASS: 'passw0rd'
            FLARESOLVERR_HOST: flaresolverr
            RSS_HOST: ygg-rss-proxy
            RSS_PORT: 8080
            LOG_LEVEL: INFO
         volumes:
            - ./config:/app/config
         restart: unless-stopped
         depends_on:
            - flaresolverr

      flaresolverr:
         image: ghcr.io/flaresolverr/flaresolverr:latest
         container_name: flaresolverr
         environment:
            TZ: Europe/Paris
            LOG_LEVEL: info
            CAPTCHA_SOLVER: none
         expose:
            - 8191
         restart: unless-stopped
   ```

2. **Exécuter Docker Compose**

   ```bash
   docker-compose up -d --build
   ```

## Comment Utiliser le Proxy

L'URL RSS à utiliser est la même que sur le site concerné, mais vous devez changer le nom de domaine de `www.ygg.re` à `localhost:8080` ou tout autre HOST que vous avez définie dans les variable `RSS_HOST` `RSS_PORT`. Assurez-vous de bien conserver tous les paramètres car notre script les réutilise.

### Exemple

URL d'origine : `https://www.ygg.re/rss?action=generate&type=subcat&id=2183&passkey=xxxxxxxxxxxxxxxxxxxxxxxxxxx`

URL à utiliser dans le client torrent : `http://localhost:8080/rss?action=generate&type=subcat&id=2183&passkey=xxxxxxxxxxxxxxxxxxxxxxxxxxx`


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
    ├── app.py
    ├── auth.py
    ├── logging_config.py
    ├── rss.py
    ├── run_gunicorn.py
    ├── session_manager.py.py
    └── settings.py
```

## Contribuer

N'hésitez pas à ouvrir des issues ou à soumettre des pull requests si vous trouvez des bugs ou avez des suggestions de fonctionnalités.
