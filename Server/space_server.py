from ursinanetworking import *
import numpy as np
import time
import random
import signal
import sys
from ursina import *  # Ajout d'Ursina pour l'interface graphique du serveur

# Fonction pour gérer l'arrêt du serveur proprement
# Fonction pour gérer l'arrêt du serveur proprement
def signal_handler(sig, frame):
    # sig et frame sont nécessaires pour la signature de fonction du gestionnaire de signal
    print("\nFermeture du serveur en cours...")
    # Force l'arrêt du processus avec code 0 (succès)
    import os
    os._exit(0)
# Capturer CTRL+C pour arrêter proprement le serveur
signal.signal(signal.SIGINT, signal_handler)

# Configuration serveur
print("Démarrage du serveur...")
print("Pour arrêter le serveur, appuyez sur CTRL+C")
try:
    server = UrsinaNetworkingServer("192.168.163.41", 25565)
    print("✓ Serveur démarré avec succès sur localhost:25565")
except Exception as e:
    print(f"❌ Erreur lors du démarrage du serveur: {e}")
    sys.exit(1)

# Initialisation d'Ursina pour la vue du serveur
app = Ursina()
window.title = 'Vue Serveur - Système Solaire'
window.color = color.black
scene.background = color.black

# Création d'un conteneur pour le système solaire (pour le zoom)
systeme_solaire_parent = Entity(position=(0,0,0))

# Configuration de la caméra - utilisation d'une caméra standard avec vue de dessus
camera.position = (0, 1000000, 0)   # Position très haute au-dessus du système
camera.rotation_x = 90              # Regarder directement vers le bas
camera.fov = 60                     # Champ de vision
camera.clip_plane_far = 10000000000 # Distance de rendu maximale

# Niveau de zoom initial et facteur de zoom
niveau_zoom = 1.0
facteur_zoom = 0.9  # <1 pour zoom in, >1 pour zoom out

# Interface utilisateur pour le serveur
serveur_info_text = Text(text="Serveur actif - 0 joueurs connectés", position=(-0.65, 0.45), scale=1.5, color=color.lime)
temps_ecoule_text = Text(text="Jours écoulés: 0", position=(-0.65, 0.40), scale=1.2, color=color.white)
serveur_zoom_text = Text(text=f"Zoom: x{niveau_zoom:.1f}", position=(-0.65, 0.35), scale=1.0, color=color.white)
serveur_controls_text = Text(text="Contrôles: Z/S = Zoom, 1/2/3 = Vues prédéfinies", position=(0.3, 0.45), scale=0.8, color=color.yellow)

# Classe personnalisée pour créer des lignes
def create_line(start_point, end_point, color=color.white):
    line_entity = Entity(parent=systeme_solaire_parent)  # Attach to the parent entity
    line_entity.model = Mesh(vertices=[start_point, end_point], mode='line')
    line_entity.color = color
    return line_entity

# Fonction pour créer une grille de fond
def creer_grille(taille=10000, pas=1000):
    for i in range(-taille, taille+1, pas):
        # Ligne horizontale (axe X)
        create_line(Vec3(i, 0, -taille), Vec3(i, 0, taille), color=color.dark_gray)
        # Ligne verticale (axe Z)
        create_line(Vec3(-taille, 0, i), Vec3(taille, 0, i), color=color.dark_gray)
    
    # Axes principaux en couleurs
    create_line(Vec3(-taille, 0, 0), Vec3(taille, 0, 0), color=color.red)    # Axe X
    create_line(Vec3(0, 0, -taille), Vec3(0, 0, taille), color=color.green)  # Axe Z

# Création de la grille
creer_grille()

# Variables pour la visualisation
visualisations_joueurs = {}
visualisations_planetes = {}
SCALE = 2e-10  # Même échelle que celle utilisée par les clients
TAILLE_PLANETES = {
    'Soleil': 100,      # Taille plus petite que sur le client pour une meilleure vue d'ensemble
    'Mercure': 10,
    'Vénus': 10,
    'Terre': 10,
    'Mars': 10,
    'Jupiter': 40,
    'Saturne': 35,
    'Uranus': 20,
    'Neptune': 20,
    'Pluton': 5
}

# Couleurs des planètes pour la visualisation serveur
COULEURS_PLANETES = {
    'Soleil': color.yellow,
    'Mercure': color.gray,
    'Vénus': color.orange,
    'Terre': color.azure,
    'Mars': color.red,
    'Jupiter': color.brown,
    'Saturne': color.yellow,
    'Uranus': color.cyan,
    'Neptune': color.blue,
    'Pluton': color.white
}

# Configuration du système solaire
G = 6.67430e-11  # constante gravitationnelle
TIME_STEP = 60 * 24 * 60  # 1 jour en secondes

# Liste des joueurs connectés avec leurs informations
joueurs = {}

# Données des planètes
class CorpsCeleste:
    def __init__(self, nom, masse, position, vitesse, periode_rotation=24):
        self.nom = nom
        self.masse = masse
        self.position_reelle = np.array(position, dtype='float64')
        self.vitesse = np.array(vitesse, dtype='float64')
        self.periode_rotation = periode_rotation * 3600  # conversion en secondes
        
        # Créer la représentation visuelle pour la vue serveur
        taille = TAILLE_PLANETES.get(nom, 10)
        couleur = COULEURS_PLANETES.get(nom, color.white)
        self.visualisation = Entity(
            model='sphere',
            color=couleur,
            scale=taille,
            position=Vec3(*(self.position_reelle * SCALE)),
            parent=systeme_solaire_parent  # Attacher au conteneur parent
        )
        
        # Ajouter un texte avec le nom de la planète qui reste face à la caméra
        self.nom_texte = Text(
            text=nom,
            parent=self.visualisation,
            billboard=True,  # Toujours face à la caméra
            position=(0, 2, 0),  # Position au-dessus de la planète
            scale=20,  # Taille plus grande pour être visible
            color=couleur,
            origin=(0, 0),
            background=True,  # Ajouter un fond pour meilleure lisibilité 
            background_color=color.clear,  # Fond transparent
            background_scale=(1.2, 1.2)  # Léger padding autour du texte
        )

    def mise_a_jour(self, corps_exterieurs):
        # Mise à jour orbitale
        force_totale = np.array([0.0, 0.0, 0.0])
        for autre in corps_exterieurs:
            if autre is self:
                continue
            direction = autre.position_reelle - self.position_reelle
            distance = np.linalg.norm(direction)
            if distance < 1e3:  # éviter division par zéro ou forces extrêmes
                continue
            force = G * self.masse * autre.masse / distance**2
            force_totale += force * direction / distance
        acceleration = force_totale / self.masse
        self.vitesse += acceleration * TIME_STEP
        self.position_reelle += self.vitesse * TIME_STEP
        
        # Mettre à jour la position visuelle
        self.visualisation.position = Vec3(*(self.position_reelle * SCALE))
        
        return np.array(self.position_reelle * SCALE).tolist()  # Convertir en liste pour JSON

planetes = []

# Soleil (station centrale)
soleil = CorpsCeleste(
    nom='Soleil',
    masse=1.989e30,
    position=[0, 0, 0],
    vitesse=[0, 0, 0],
    periode_rotation=25 * 24  # 25 jours pour le Soleil
)

planetes.append(soleil)

# Facteur d'échelle supplémentaire pour les distances des planètes
facteur_distance = 10

# Données des planètes avec distances réalistes et périodes de rotation
donnees_planetes = [
    {
        'nom': 'Mercure',
        'masse': 3.285e23,
        'distance': 5.791e10 * facteur_distance,
        'periode_rotation': 58.6 * 24  # 58.6 jours
    },
    {
        'nom': 'Vénus',
        'masse': 4.867e24,
        'distance': 1.082e11 * facteur_distance,
        'periode_rotation': -243 * 24  # 243 jours (rotation rétrograde)
    },
    {
        'nom': 'Terre',
        'masse': 5.972e24,
        'distance': 1.496e11 * facteur_distance,
        'periode_rotation': 24  # 24 heures
    },
    {
        'nom': 'Mars',
        'masse': 6.39e23,
        'distance': 2.279e11 * facteur_distance,
        'periode_rotation': 24.6  # 24.6 heures
    },
    {
        'nom': 'Jupiter',
        'masse': 1.898e27,
        'distance': 7.785e11 * facteur_distance,
        'periode_rotation': 9.9  # 9.9 heures
    },
    {
        'nom': 'Saturne',
        'masse': 5.683e26,
        'distance': 1.433e12 * facteur_distance,
        'periode_rotation': 10.7  # 10.7 heures
    },
    {
        'nom': 'Uranus',
        'masse': 8.681e25,
        'distance': 2.877e12 * facteur_distance,
        'periode_rotation': 17.2  # 17.2 heures
    },
    {
        'nom': 'Neptune',
        'masse': 1.024e26,
        'distance': 4.503e12 * facteur_distance,
        'periode_rotation': 16.1  # 16.1 heures
    },
    {
        'nom': 'Pluton',
        'masse': 1.309e22,
        'distance': 5.906e12 * facteur_distance,
        'periode_rotation': 153 * 24  # 153 jours
    }
]

# Ajout des planètes avec vitesse orbitale circulaire correcte
for p in donnees_planetes:
    r = p['distance']
    # Vitesse orbitale circulaire: v = sqrt(G*M/r)
    v = np.sqrt(G * soleil.masse / r)
    # Orientation correcte de la vitesse pour une orbite circulaire
    position = np.array([r, 0, 0])
    vitesse = np.array([0, v, 0])  # Vitesse perpendiculaire au rayon dans le bon plan
    
    planete = CorpsCeleste(
        nom=p['nom'],
        masse=p['masse'],
        position=position,
        vitesse=vitesse,
        periode_rotation=p['periode_rotation']
    )
    planetes.append(planete)

# Variables de simulation
temps_ecoule = 0
simulation_speed = 1

# Initialisation des variables de timing pour la simulation et la synchronisation
derniere_mise_a_jour = time.time()
derniere_synchro = time.time()

# Fonction pour obtenir les données des planètes
def get_planets_data():
    planets_data = []
    for i, planete in enumerate(planetes):
        pos = np.array(planete.position_reelle * SCALE).tolist()
        planets_data.append({
            "id": i,
            "nom": planete.nom,
            "position": pos
        })
    return planets_data

# Gestion des événements réseau
@server.event
def onClientConnected(client):
    print(f"Nouveau joueur connecté: {client.id}")
    # Assigner un ID unique et une couleur aléatoire au joueur
    r = random.random()
    g = random.random()
    b = random.random()
    
    # Envoi des données initiales au client
    client.send_message("init_player", {
        "id": client.id,
        "color": [r, g, b],
        "planets_data": get_planets_data(),
        "temps_ecoule": temps_ecoule
    })
    
    # Informer les autres joueurs de la nouvelle connexion
    joueurs[client.id] = {
        "id": client.id,
        "position": [0, 0, 0],
        "rotation": [0, 0, 0],
        "color": [r, g, b]
    }
    
    server.broadcast("new_player", {
        "id": client.id,
        "color": [r, g, b]
    }, [client.id])
    
    # Envoyer les données des joueurs existants au nouveau joueur
    for joueur_id, joueur in joueurs.items():
        if joueur_id != client.id:
            client.send_message("new_player", {
                "id": joueur_id,
                "color": joueur["color"]
            })

@server.event
def onClientDisconnected(client):
    print(f"Joueur déconnecté: {client.id}")
    if client.id in joueurs:
        del joueurs[client.id]
        server.broadcast("player_disconnect", {
            "id": client.id
        })

@server.event
def player_position(client, data):
    """Reçoit la position d'un joueur et la transmet aux autres"""
    if client.id in joueurs:
        position = data["position"]
        rotation = data["rotation"]
        joueurs[client.id]["position"] = position
        joueurs[client.id]["rotation"] = rotation
        
        # Mettre à jour ou créer la représentation visuelle du joueur sur la vue serveur
        if client.id not in visualisations_joueurs:
            color_value = joueurs[client.id]["color"]
            # Créer une représentation visuelle du joueur (petit cube)
            visualisations_joueurs[client.id] = Entity(
                model='cube',
                color=color.rgba(*color_value, 1),
                scale=(500, 500, 500),  # Taille suffisante pour être visible
                position=Vec3(*position),
                parent=systeme_solaire_parent  # Attacher au conteneur parent
            )
            
            # Ajouter un texte avec l'ID du joueur
            Text(
                text=f"Joueur {client.id}",
                parent=visualisations_joueurs[client.id],
                position=(0, 2, 0),  # Position au-dessus du vaisseau
                billboard=True,  # Toujours face à la caméra
                scale=300,  # Taille plus grande pour être visible
                color=color.rgba(*color_value, 1),
                origin=(0, 0),
                background=True,  # Ajouter un fond pour meilleure lisibilité
                background_color=color.black50,  # Fond semi-transparent noir
                background_scale=(1.2, 1.2)  # Léger padding autour du texte
            )
        else:
            # Mettre à jour la position de la représentation visuelle
            visualisations_joueurs[client.id].position = Vec3(*position)
        
        # Envoyer la position à tous les autres joueurs
        server.broadcast("player_move", {
            "id": client.id,
            "position": position,
            "rotation": rotation
        }, [client.id])

def reset_simulation_request(client, data):
    """Réinitialise la simulation pour tous les clients"""
    # client et data sont nécessaires pour la signature de la fonction d'événement
    global temps_ecoule
    temps_ecoule = 0
    
    # Réinitialisation des positions des planètes
    for i, p in enumerate(donnees_planetes):
        r = p['distance']
        planetes[i+1].position_reelle = np.array([r, 0, 0])
        planetes[i+1].vitesse = np.array([0, np.sqrt(G * soleil.masse / r), 0])
    
    server.broadcast("reset_simulation", {})
@server.event
def set_simulation_speed(client, data):
    """Change la vitesse de simulation pour tous les clients"""
    # client est nécessaire pour la signature de la fonction d'événement
    global simulation_speed
    simulation_speed = max(1, min(10, data["speed"]))
    server.broadcast("simulation_speed_changed", {
        "speed": simulation_speed
    })
@server.event
def disconnect_request(client, data):
    """Gestion explicite de la déconnexion d'un client"""
    # data est nécessaire pour la signature de la fonction d'événement
    print(f"Demande de déconnexion du client {client.id}")
    
    # Les actions nécessaires sont déjà gérées par onClientDisconnected
    # Cette fonction permet simplement de tracer la déconnexion explicite
    

@server.event
def disconnect_request(client, data):
    """Gestion explicite de la déconnexion d'un client"""
    print(f"Demande de déconnexion du client {client.id}")
    
    # Les actions nécessaires sont déjà gérées par onClientDisconnected
    # Cette fonction permet simplement de tracer la déconnexion explicite

@server.event
def player_shoot(client, data):
    """Reçoit les données d'un tir de laser et les transmet aux autres clients"""
    if client.id in joueurs:
        # Ajouter l'ID du tireur aux données pour que les clients sachent qui a tiré
        data["id"] = client.id
        
        # Transmettre le tir à tous les autres joueurs
        server.broadcast("player_shoot", data, [client.id])
        

# Simplification et unification des contrôles de caméra
# Remplacer la fonction update et update_server par une seule fonction complète
def update():
    global niveau_zoom, derniere_mise_a_jour, derniere_synchro, temps_ecoule
    
    # Traiter les événements réseau
    server.process_net_events()
    
    maintenant = time.time()
    dt = maintenant - derniere_mise_a_jour
    
    # Mettre à jour les planètes toutes les 50ms
    if dt >= 0.05:
        derniere_mise_a_jour = maintenant
        
        # Appliquer la vitesse de simulation - AUGMENTATION pour mieux voir le mouvement
        for _ in range(simulation_speed * 5):  # Multiplié par 5 pour rendre le mouvement plus visible
            for corps in planetes:
                corps.mise_a_jour(planetes)
            temps_ecoule += TIME_STEP
    
    # Synchroniser les données des planètes avec les clients toutes les 0.5 secondes
    if maintenant - derniere_synchro >= 0.5:
        derniere_synchro = maintenant
        
        planets_data = get_planets_data()
        server.broadcast("update_planets", {
            "planets": planets_data,
            "temps_ecoule": temps_ecoule
        })
    
    # Mettre à jour l'interface utilisateur
    serveur_info_text.text = f"Serveur actif - {len(joueurs)} joueurs connectés"
    temps_ecoule_text.text = f"Jours écoulés: {int(temps_ecoule / (60*60*24))}"
    
    # Contrôles de zoom
    if held_keys['w']:
        niveau_zoom *= facteur_zoom  # Zoom in progressif
        systeme_solaire_parent.scale = Vec3(niveau_zoom, niveau_zoom, niveau_zoom)
        serveur_zoom_text.text = f"Zoom: x{niveau_zoom:.1f}"
    
    if held_keys['s']:
        niveau_zoom /= facteur_zoom  # Zoom out progressif
        systeme_solaire_parent.scale = Vec3(niveau_zoom, niveau_zoom, niveau_zoom)
        serveur_zoom_text.text = f"Zoom: x{niveau_zoom:.1f}"
    
    # Préréglages de zoom
    if held_keys['1']:
        niveau_zoom = 1.0  # Vue globale
        systeme_solaire_parent.scale = Vec3(niveau_zoom, niveau_zoom, niveau_zoom)
        serveur_zoom_text.text = f"Zoom: x{niveau_zoom:.1f}"
    
    if held_keys['2']:
        niveau_zoom = 10.0   # Vue intermédiaire
        systeme_solaire_parent.scale = Vec3(niveau_zoom, niveau_zoom, niveau_zoom)
        serveur_zoom_text.text = f"Zoom: x{niveau_zoom:.1f}"
    
    if held_keys['3']:
        niveau_zoom = 100.0    # Vue rapprochée
        systeme_solaire_parent.scale = Vec3(niveau_zoom, niveau_zoom, niveau_zoom)
        serveur_zoom_text.text = f"Zoom: x{niveau_zoom:.1f}"

# Remplacer la fonction update par notre fonction
app.update = update

# Lancer l'application Ursina (ceci remplace la boucle while True)
print("Démarrage de l'interface serveur...")
app.run()
