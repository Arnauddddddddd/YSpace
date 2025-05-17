# YSpace - Simulateur Spatial Interactif

YSpace est un projet de simulateur spatial 3D construit avec le moteur Ursina, offrant plusieurs modules distincts pour explorer et interagir avec un système solaire simulé.

## Fonctionnalités

- Simulation réaliste du système solaire avec une mécanique orbitale précise
- Modes de visualisation multiples et contrôles interactifs
- Exportation des données de simulation vers des fichiers CSV
- Capacités multijoueur avec architecture client-serveur
- Mode de jeu thématique Star Wars avec sélection de faction

---

## Modules Principaux

## 🪐 SpaceSimulator (Solo)

Un simulateur de système solaire en mode solo avec orbites planétaires et physique réalistes.

- **Lancement :**
    ```bash
    cd YSpace/SpaceSimulator
    python spaceSimulator.py
    ```
- **Fonctionnalités :**
    - Simulation des orbites et de la gravité
    - Exportation des données planétaires (CSV)
    - Contrôles de vitesse et de caméra


#### Exportation de Données

Le SpaceSimulator peut exporter des données planétaires vers des fichiers CSV dans `SpaceSimulator/exports/`, incluant :
- Noms et masses des planètes
- Positions et vitesses
- Distance par rapport au soleil
- Périodes de rotation


#### Contrôles
    - `+` / `-` : Augmenter/diminuer la vitesse de simulation
    - `R` : Réinitialiser la simulation
    - `E` : Exporter les données


## 🌐 Serveur & Multijoueur

Implémentation multijoueur permettant à plusieurs utilisateurs d'explorer ensemble.

- **Serveur :**
    - `space_server.py` : Application serveur avec interface administrative
- **Client :**
    - `space_client.py` : Application client pour rejoindre une partie

- **Lancement :**
    1. Démarrer le serveur :
         ```bash
         cd YSpace/Server
         python space_server.py
         ```
    2. Démarrer un ou plusieurs clients :
         ```bash
         cd YSpace/Server
         python space_client.py
         ```

- **Fonctionnalités :**
    - Synchronisation des positions et actions des joueurs
    - Contrôles adaptés au multijoueur
    - Mode vue à la première personne

#### Contrôles

    - `F` : Vue à la première personne
    - `Espace` / `C` : Monter/descendre
    - `Clic gauche` ou `E` : Tirer des lasers (multijoueur)
    - `Maj` : Accélérer
    - `Échap` : Verrouiller/déverrouiller la souris


## Configuration Réseau

Pour le mode multijoueur, ajustez l'adresse IP du serveur dans `space_server.py` et `space_client.py` selon votre réseau.  
Par défaut, le serveur fonctionne sur le port 25565.

---

## ✨ StarWars (Mode Thématique)

Un mode spécial permettant de piloter des vaisseaux emblématiques (TIE Fighter ou X-Wing) selon la faction choisie.

- **Lancement :**
    ```bash
    cd YSpace/StarWars
    python starwars.py
    ```
- **Fonctionnalités :**
    - Sélection de faction et de vaisseau
    - Contrôles de vol et de tir
    - Vue immersive


## Installation

1. Assurez-vous d'avoir Python 3.7+ installé
2. Installez les dépendances requises
3. Clonez ou téléchargez le dépôt YSpace





## Prérequis

- Python 3.7+
- Moteur Ursina
- NumPy
- UrsinaNetworking (pour le multijoueur)

---



*Ce projet est à des fins éducatives et n'est pas affilié à Disney ou à la franchise Star Wars.*