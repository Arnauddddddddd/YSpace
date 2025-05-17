from ursina import *
from ursinanetworking import *
import numpy as np
import math
import random
import time
import sys
import signal
import os

# Fonction pour gérer CTRL+C et fermer proprement l'application
def signal_handler(sig, frame):
    print("\nFermeture du client en cours...")
    force_quit_game()

# Force la fermeture du jeu de façon fiable
def force_quit_game():
    try:
        if client:
            # Informer le serveur que nous nous déconnectons
            client.send_message("disconnect_request", {})
    except:
        pass
    # Force l'arrêt du processus immédiatement
    print("Fermeture forcée de l'application...")
    os._exit(0)

# Enregistrer le gestionnaire de signal pour CTRL+C
signal.signal(signal.SIGINT, signal_handler)

# Configuration client
print("Tentative de connexion au serveur sur localhost:25565...")
try:
    client = UrsinaNetworkingClient("192.168.163.41", 25565)
    print("Connecté au serveur!")
except Exception as e:
    print(f"Erreur de connexion: {e}")
    # Continuer sans connexion réseau (mode hors ligne)
    print("Fonctionnement en mode hors ligne")
    client = None

# Configuration de l'application
app = Ursina()
window.color = color.black
scene.background = color.black

# Gestionnaire pour fermer l'application quand on utilise la croix de la fenêtre
def quit_game():
    print("\nFermeture du client via la fenêtre...")
    try:
        if client:
            # Informer le serveur que nous nous déconnectons
            client.send_message("disconnect_request", {})
    except:
        pass
    # Force l'arrêt du processus
    application.quit()
    os._exit(0)

# Associer la fonction à l'événement de fermeture de fenêtre
window.exit_button.on_click = quit_game

# Configuration de la caméra
camera.clip_plane_far = 1_000_000_000
camera.fov = 90

# Variables pour le contrôle
mouse.locked = True

# Variables globales pour le multijoueur
player_id = None
autres_joueurs = {}
planetes = []
SCALE = 2e-10  # Constante d'échelle (doit être la même que sur le serveur)
mode_hors_ligne = False  # Mode hors ligne par défaut désactivé
lasers = []  # Liste pour stocker les rayons laser tirés

# Textes d'information
info_connexion = Text(text="Connexion au serveur...", position=(0, 0), origin=(0, 0), color=color.yellow)
info_text = Text(text="", position=(-0.85, 0.35), scale=1, color=color.white)
jours_ecoule_text = Text(text=f"Jours écoulés: 0", position=(-0.85, 0.45), scale=1.5, color=color.white)
vitesse_text = Text(text=f"Vitesse: 1x", position=(-0.85, 0.40), scale=1, color=color.white)
player_count_text = Text(text="Joueurs: 1", position=(0.85, 0.45), scale=1, color=color.white)
coordinates_text = Text(
    text='Coordinates: X: 0 Y: 0 Z: 0',
    position=(0.5, 0.45),
    scale=1,
    color=color.white
)

# Couleurs des planètes pour les reconnaître
couleurs_planetes = {
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

# Tailles des planètes
tailles_planetes = {
    'Soleil': 350,
    'Mercure': 12.8,
    'Vénus': 12.0,
    'Terre': 12.0,
    'Mars': 6.0,
    'Jupiter': 153.0,
    'Saturne': 129.0,
    'Uranus': 60.0,
    'Neptune': 51.0,
    'Pluton': 3.0
}

# Chargement du vaisseau TIE Fighter
try:
    custom_model = load_model('assets/TIEFighter.fbx')
    vaisseau = Entity(
        model=custom_model,
        scale=0.01,
        position=(0, 0, 0),  # Position initiale au centre (soleil)
        collider=None,
        texture=None,  # Suppression de la texture "white" qui cause des erreurs
        double_sided=True,
        rotation=(0, 180, 0),
        transparent=True
    )
except Exception as e:
    print(f"Erreur lors du chargement du modèle: {e}")
    # Si le modèle n'est pas trouvé, utiliser un cube simple comme vaisseau
    vaisseau = Entity(
        model='cube',
        color=color.light_gray,
        scale=(2, 1, 3),
        position=(0, 0, 0)  # Position initiale au centre (soleil)
    )

# Classe pour gérer les planètes
class Planete(Entity):
    def __init__(self, id, nom, position, scale):
        super().__init__(
            model='sphere',
            color=couleurs_planetes.get(nom, color.white),
            position=Vec3(*position),
            scale=scale
        )
        self.nom = nom
        self.id = id
        
        # Ajouter une lumière si c'est le soleil
        if nom == 'Soleil':
            self.light = PointLight(parent=self, position=(0,0,0), color=color.yellow, shadows=False)
            self.light.scale = 50
            self.light.intensity = 50
            self.emissive_color = color.yellow
        else:
            self.light = PointLight(parent=self, position=(0,0,0), color=self.color, shadows=False)
            self.light.scale = 0.5

# Classe pour gérer les rayons laser
class Laser(Entity):
    def __init__(self, position, direction, color_value=color.red, owner_id=None):
        # Augmenter considérablement la longueur du laser pour qu'il soit plus visible
        self.laser_length = 5000
        
        # Utiliser un cylindre très fin au lieu d'un cube pour meilleure visibilité
        super().__init__(
            model='cube',
            color=color_value,
            position=position,
            scale=(10, self.laser_length, 10),  # Augmenter l'épaisseur (x, longueur, z)
            billboard=False,
        )
        
        # S'assurer que le laser est orienté dans la direction de tir
        self.look_at(position + direction)
        # Correction de la rotation pour aligner le cylindre avec la direction
        self.rotation_x += 90
        
        # Effet d'émission de lumière pour faire briller le laser (plus intense)
        self.emissive = True
        
        # Ajouter un effet lumineux encore plus visible
        self.light = PointLight(parent=self, position=(0, self.laser_length/2, 0), color=color_value, shadows=False)
        self.light.scale = 10
        self.light.intensity = 10
        
        # Durée de vie du laser
        self.lifetime = 2.0  # En secondes
        self.creation_time = time.time()
        
        # Direction et vitesse
        self.direction = direction
        self.speed = 80000  # Augmenter la vitesse pour plus de dynamisme
        
        # Pour identifier le propriétaire du laser (pour le multijoueur)
        self.owner_id = owner_id
        
        # État du laser
        self.is_active = True
        
        # Tracer l'événement pour le débogage
        print(f"Laser créé: pos={position}, dir={direction}, owner={owner_id}")
        
    def update(self):
        # Si le laser n'est plus actif, ne rien faire
        if not self.is_active:
            return False
            
        try:
            # Déplacement du laser
            self.position += self.direction * self.speed * time.dt
            
            # Vérifier si le laser doit être supprimé
            if time.time() - self.creation_time > self.lifetime:
                self.disable()
                return False
            return True
        except Exception as e:
            print(f"Erreur lors de la mise à jour du laser: {e}")
            self.disable()
            return False
        
    def disable(self):
        if self.is_active:
            self.is_active = False
            try:
                if hasattr(self, 'light') and self.light:
                    destroy(self.light)
                destroy(self)
            except Exception as e:
                print(f"Erreur lors de la désactivation du laser: {e}")

# Classe pour gérer les autres joueurs
class AutreJoueur(Entity):
    def __init__(self, id, position, color_value):
        try:
            model_vaisseau = load_model('assets/TIEFighter.fbx')
            super().__init__(
                model=model_vaisseau, 
                scale=0.01, 
                position=Vec3(*position),
                rotation=(0, 180, 0),
                texture=None,
                double_sided=True,
                transparent=True,
                color=color.rgba(*color_value, 1)
            )
            print(f"Vaisseau créé pour joueur {id} avec modèle TIEFighter")
        except Exception as e:
            print(f"Erreur lors du chargement du modèle pour joueur {id}: {e}")
            super().__init__(
                model='cube',
                color=color.rgba(*color_value, 1),
                scale=(2, 1, 3),
                position=Vec3(*position)
            )
            print(f"Vaisseau créé pour joueur {id} avec cube de remplacement")
        
        self.id = id
        
        # Création d'une entité séparée pour le nom du joueur qui suit le vaisseau
        self.nom_entity = Entity(
            parent=scene,
            position=self.position + Vec3(0, 10, 0),
            billboard=True
        )
        
        # Ajout du texte sur l'entité
        self.nom_text = Text(
            text=f"Joueur {id}",
            parent=self.nom_entity,
            scale=25,
            origin=(0, 0),
            color=color.rgba(*color_value, 1)
        )
        
    def update_position(self, position, rotation):
        """Mise à jour de la position et de la rotation du joueur et de son nom"""
        self.position = Vec3(*position)
        self.rotation = Vec3(*rotation)
        # Mise à jour de la position du nom pour qu'il reste au-dessus du vaisseau
        if hasattr(self, 'nom_entity'):
            self.nom_entity.position = self.position + Vec3(0, 10, 0)

simulation_speed = 1
temps_ecoule = 0
selected_planet = None

# Fonction pour initialiser les planètes reçues du serveur
def create_planets(planets_data):
    global planetes
    # Supprimer les planètes existantes
    for p in planetes:
        destroy(p)
    planetes = []
    
    # Créer les nouvelles planètes
    for planet_data in planets_data:
        id = planet_data["id"]
        nom = planet_data["nom"]
        position = planet_data["position"]
        scale = tailles_planetes.get(nom, 10)
        
        planete = Planete(id, nom, position, scale)
        planetes.append(planete)
        
        # Ajouter un collider pour le clic
        planete.collider = SphereCollider(planete, center=Vec3(0,0,0), radius=0.5)
        planete.on_click = lambda p=planete: on_planet_click(p)

# Fonctions pour les événements réseau
@client.event
def init_player(data):
    global player_id
    player_id = data["id"]
    info_connexion.text = f"Connecté au serveur avec l'ID: {player_id}"
    print(f"Connecté au serveur avec l'ID: {player_id}")
    
    # Changer la couleur du vaisseau
    color_value = data["color"]
    vaisseau.color = color.rgba(*color_value, 1)
    
    # Créer les planètes
    create_planets(data["planets_data"])
    
    # Mettre à jour le temps écoulé
    global temps_ecoule
    temps_ecoule = data["temps_ecoule"]
    jours = int(temps_ecoule / (60*60*24))
    jours_ecoule_text.text = f"Jours écoulés: {jours}"
    
    # Cacher le texte de connexion après quelques secondes
    invoke(setattr, info_connexion, 'enabled', False, delay=3)

@client.event
def new_player(data):
    new_id = data["id"]
    color_value = data["color"]
    
    print(f"Nouveau joueur connecté: {new_id}")
    
    # Créer un modèle pour ce joueur
    autres_joueurs[new_id] = AutreJoueur(new_id, [0, 0, 0], color_value)
    
    # Mettre à jour le nombre de joueurs
    player_count_text.text = f"Joueurs: {len(autres_joueurs) + 1}"

@client.event
def player_disconnect(data):
    disconnect_id = data["id"]
    if disconnect_id in autres_joueurs:
        print(f"Joueur déconnecté: {disconnect_id}")
        destroy(autres_joueurs[disconnect_id])
        del autres_joueurs[disconnect_id]
        
        # Mettre à jour le nombre de joueurs
        player_count_text.text = f"Joueurs: {len(autres_joueurs) + 1}"

@client.event
def player_move(data):
    move_id = data["id"]
    if move_id in autres_joueurs:
        # Mettre à jour la position et rotation du joueur
        position = data["position"]
        rotation = data["rotation"]
        # Utiliser la nouvelle méthode update_position pour mettre à jour la position du vaisseau et de son nom
        autres_joueurs[move_id].update_position(position, rotation)

@client.event
def update_planets(data):
    # Mise à jour des planètes
    planets_data = data["planets"]
    for planet_data in planets_data:
        id = planet_data["id"]
        position = planet_data["position"]
        if id < len(planetes):
            planetes[id].position = Vec3(*position)
    
    # Mise à jour du temps écoulé
    global temps_ecoule
    temps_ecoule = data["temps_ecoule"]
    jours = int(temps_ecoule / (60*60*24))
    jours_ecoule_text.text = f"Jours écoulés: {jours}"

@client.event
def reset_simulation(data):
    # Le serveur a réinitialisé la simulation
    print("La simulation a été réinitialisée")

@client.event
def simulation_speed_changed(data):
    global simulation_speed
    simulation_speed = data["speed"]
    vitesse_text.text = f"Vitesse: {simulation_speed}x"

@client.event
def player_shoot(data):
    """Réception d'un tir laser d'un autre joueur"""
    shooter_id = data["id"]
    position = data["position"]
    direction = data["direction"]
    color_value = data["color"]
    
    # Ne pas créer le laser si c'est notre propre tir (on l'a déjà créé localement)
    if shooter_id == player_id:
        return
        
    print(f"Tir laser reçu du joueur {shooter_id}: pos={position}, dir={direction}")
    
    try:
        # S'assurer que la direction est un vecteur valide
        dir_vector = Vec3(*direction)
        # Si la norme du vecteur est trop petite, utiliser une direction par défaut
        if dir_vector.length() < 0.1:
            # Direction par défaut vers l'avant (si on n'a pas d'information valide)
            if shooter_id in autres_joueurs:
                # Utiliser la direction du joueur si disponible
                forward_dir = autres_joueurs[shooter_id].forward
            else:
                # Sinon utiliser une direction arbitraire
                forward_dir = Vec3(0, 0, 1)
            dir_vector = forward_dir
        
        # Créer le laser à la position de l'autre joueur
        new_laser = Laser(
            position=Vec3(*position),
            direction=dir_vector.normalized(),
            color_value=color.rgba(*color_value),
            owner_id=shooter_id
        )
        
        # Ajouter le laser à la liste pour le suivi
        lasers.append(new_laser)
        
    except Exception as e:
        print(f"Erreur lors de la création du laser d'un autre joueur: {e}")

# Fonction de clic sur une planète
def on_planet_click(planet):
    global selected_planet
    selected_planet = planet
    info_text.text = f"{planet.nom}"

# Dernière position et rotation envoyées
last_sent_position = None
last_sent_rotation = None

# Fonction de mise à jour pour chaque frame
def update():
    global last_sent_position, last_sent_rotation, lasers
    
    # Traiter les événements réseau
    client.process_net_events()
    
    if mouse.locked:
        # Rotation du vaisseau avec la souris
        vaisseau.rotation_y += mouse.velocity[0] * 1000 * time.dt
        vaisseau.rotation_x = clamp(
            vaisseau.rotation_x - mouse.velocity[1] * 1000 * time.dt,
            -60,  # Limite haute
            60    # Limite basse
        )

    # Mouvement vers l'avant
    if held_keys['w']:
        if held_keys['shift']:
            vaisseau.position += vaisseau.forward * 100_000 * time.dt
        else:
            vaisseau.position += vaisseau.forward * 10_000 * time.dt
    
    # Mouvement vers l'arrière
    if held_keys['s']:
        vaisseau.position -= vaisseau.forward * 10_000 * time.dt
    
    # Mouvement latéral
    if held_keys['a']:
        vaisseau.position -= vaisseau.right * 10_000 * time.dt
    if held_keys['d']:
        vaisseau.position += vaisseau.right * 10_000 * time.dt
    
    # Mouvement vertical
    if held_keys['space']:
        vaisseau.position += vaisseau.up * 10_000 * time.dt
    if held_keys['c'] or held_keys['ctrl']:
        vaisseau.position -= vaisseau.up * 10_000 * time.dt
    
    # Configuration de la caméra (3e personne)
    if not held_keys['f']:  # Mode caméra 3e personne
        cam_distance = 3000
        cam_height = 2
        
        # Position derrière le vaisseau
        target_pos = vaisseau.position - vaisseau.forward * cam_distance + Vec3(0, cam_height, 0)
        
        # Lissage du mouvement
        camera.position = lerp(camera.position, target_pos, time.dt * 15)
        
        # Orientation de la caméra
        camera.look_at(vaisseau, axis='forward')
        
        # Ajustement de la rotation pour suivre l'inclinaison du vaisseau
        camera.rotation_x = vaisseau.rotation_x
        camera.rotation_z = 0
    else:  # Mode première personne
        camera.position = vaisseau.position
        camera.rotation_x = vaisseau.rotation_x
        camera.rotation_y = vaisseau.rotation_y
        camera.rotation_z = 0
    
    # Mise à jour des coordonnées du vaisseau
    coordinates_text.text = f'Position: X: {int(vaisseau.x)} Y: {int(vaisseau.y)} Z: {int(vaisseau.z)}'
    
    # Envoyer la position et rotation au serveur si elles ont changé
    position = [vaisseau.x, vaisseau.y, vaisseau.z]
    rotation = [vaisseau.rotation_x, vaisseau.rotation_y, vaisseau.rotation_z]
    
    # Vérifier si la position a changé significativement
    if (last_sent_position is None or 
        distance(Vec3(*last_sent_position), Vec3(*position)) > 1000 or
        last_sent_rotation is None or
        sum(abs(a - b) for a, b in zip(last_sent_rotation, rotation)) > 1):
        
        # Envoyer la position et rotation au serveur
        client.send_message("player_position", {
            "position": position,
            "rotation": rotation
        })
        
        last_sent_position = position
        last_sent_rotation = rotation
    
    # Mise à jour et nettoyage des lasers
    lasers_to_keep = []
    for laser in lasers:
        # Si update() renvoie True, le laser est toujours actif
        if laser.update():
            lasers_to_keep.append(laser)
    
    # Remplacer la liste des lasers par les lasers encore actifs
    lasers = lasers_to_keep

# Gestion des entrées
def input(key):
    global simulation_speed, lasers
    
    if key == 'escape':  # Permet de déverrouiller/verrouiller la souris avec Échap
        mouse.locked = not mouse.locked
    
    # Raccourci pour quitter l'application avec Q quand Échap est activé
    if key == 'q' and not mouse.locked:
        print("Fermeture de l'application avec la touche Q")
        force_quit_game()
    
    if key == '+':
        # Envoyer la demande de changement de vitesse au serveur
        new_speed = min(10, simulation_speed + 1)
        client.send_message("set_simulation_speed", {"speed": new_speed})
    
    if key == '-':
        # Envoyer la demande de changement de vitesse au serveur
        new_speed = max(1, simulation_speed - 1)
        client.send_message("set_simulation_speed", {"speed": new_speed})
    
    if key == 'r':
        # Envoyer la demande de réinitialisation au serveur
        client.send_message("reset_simulation_request", {})
    
    if key == 'e' or key == 'left mouse down':  # Tirer un rayon laser avec E ou clic gauche
        # Récupérer la couleur du vaisseau pour le laser
        laser_color = vaisseau.color
        if laser_color == color.white or laser_color == color.light_gray:  # Couleur par défaut si non définie
            laser_color = color.red
            
        # Créer un nouveau laser à la position du vaisseau avec son orientation
        new_laser = Laser(
            position=vaisseau.position,
            direction=vaisseau.forward,
            color_value=laser_color,
            owner_id=player_id
        )
        
        # Ajouter le laser à la liste pour le suivi
        lasers.append(new_laser)
        
        # Envoyer les informations du laser au serveur pour les autres joueurs
        if client:
            client.send_message("player_shoot", {
                "position": [vaisseau.x, vaisseau.y, vaisseau.z],
                "direction": [vaisseau.forward.x, vaisseau.forward.y, vaisseau.forward.z],
                "color": [laser_color.r, laser_color.g, laser_color.b, laser_color.a] if hasattr(laser_color, 'r') else [1, 0, 0, 1]
            })

# Instructions
instructions = Text(
    text="Contrôles:\n"
         "ZQSD/WASD : déplacer vaisseau\n"
         "Souris : orientation\n"
         "Shift : accélérer\n"
         "Espace/C : monter/descendre\n"
         "F : vue 1ère personne\n"
         "E ou Clic gauche : Tirer laser\n"
         "+/- : modifier vitesse simulation\n"
         "R : réinitialiser simulation\n"
         "Clic : info planète\n"
         "Échap : verrouiller/déverrouiller souris",
    position=(0.5, 0.0),
    scale=0.75,
    color=color.white
)

# Éclairage général
scene.ambient_color = color.rgba(30, 30, 30, 255)
DirectionalLight(direction=(0.5, -1, -0.5), color=color.white)
AmbientLight(color=color.rgba(0.2, 0.2, 0.2, 1))

# Lancer l'application
app.run()