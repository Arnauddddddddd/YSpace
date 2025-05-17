from ursina import *
import numpy as np
import math
import random
import time

app = Ursina()
window.color = color.black
scene.background = color.black

# Variables globales pour la sélection
selection_faite = False
vaisseau = None
modele_vaisseau = None
team = None

class EcranSelection(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui)
        # Désactiver tous les autres éléments UI au début
        self.disable_other_ui()
        
        self.background = Entity(
            parent=self,
            model='quad',
            scale=(2, 1),
            color=color.black,
            z=1
        )
        
        # Titre
        self.title = Text("Choisissez votre camp", y=0.3, scale=3, origin=(0,0))
        
        # Bouton Empire
        self.btn_empire = Button(
            text="Empire Galactique",
            color=color.dark_gray,
            scale=(0.3, 0.1),
            position=(-0.2, 0),
            on_click=self.choisir_empire
        )
        
        # Bouton Rebelles
        self.btn_rebelles = Button(
            text="Alliance Rebelle",
            color=color.red,
            scale=(0.3, 0.1),
            position=(0.2, 0),
            on_click=self.choisir_rebelles
        )

    def disable_other_ui(self):
        # Cacher tous les autres éléments UI
        if 'jours_ecoule_text' in globals():
            jours_ecoule_text.enabled = False
        if 'vitesse_text' in globals():
            vitesse_text.enabled = False
        if 'coordinates_text' in globals():
            coordinates_text.enabled = False
        if 'instructions' in globals():
            instructions.enabled = False
        if 'info_text' in globals():
            info_text.enabled = False

    def enable_other_ui(self):
        # Réactiver tous les éléments UI
        if 'jours_ecoule_text' in globals():
            jours_ecoule_text.enabled = True
        if 'vitesse_text' in globals():
            vitesse_text.enabled = True
        if 'coordinates_text' in globals():
            coordinates_text.enabled = True
        if 'instructions' in globals():
            instructions.enabled = True
        if 'info_text' in globals():
            info_text.enabled = True
    
    def nettoyer_selection(self):
        destroy(self.background)
        destroy(self.title)
        destroy(self.btn_empire)
        destroy(self.btn_rebelles)
        self.enable_other_ui()
        mouse.locked = True
    
    def choisir_empire(self):
        global vaisseau, selection_faite, modele_vaisseau, team
        try:
            modele_vaisseau = load_model('assets/TIEFighter2.fbx')
        except:
            modele_vaisseau = 'cube'
        team = 'Empire'
        self.creer_vaisseau()
        self.nettoyer_selection()
        destroy(self)
        
    def choisir_rebelles(self):
        global vaisseau, selection_faite, modele_vaisseau, team
        try:
            modele_vaisseau = load_model('assets/xwing.fbx')  # Assurez-vous d'avoir ce modèle
        except:
            modele_vaisseau = 'cube'
        team = 'Rebelles'
        self.creer_vaisseau()
        self.nettoyer_selection()
        destroy(self)
    
    def creer_vaisseau(self):
        global vaisseau, selection_faite, team
        if isinstance(modele_vaisseau, str):
            vaisseau = Entity(
                model='cube',
                color=color.light_gray,
                scale=(2, 1, 3),
                position=(0, 0, 0)
            )
        else:
            if team == 'Empire':
                print("empire")
                vaisseau = Entity(
                    model=modele_vaisseau,
                    scale=0.001,
                    position=(0, 0, 0),
                    collider=None,
                    texture="white",
                    double_sided=True,
                    rotation=(0, 180, 0),
                    transparent=True
                )
            else:
                vaisseau = Entity(
                    model=modele_vaisseau,
                    scale=0.005,
                    position=(0, 0, 0),
                    collider=None,
                    texture="white",
                    double_sided=True,
                    rotation=(0, 180, 0),
                    transparent=True
                )
        selection_faite = True

# Créer l'écran de sélection au démarrage
ecran_selection = EcranSelection()

# Configuration de la caméra
camera.clip_plane_far = 1_000_000_000
camera.fov = 90

mouse.locked = False

sky = Entity(
    model='sphere',
    texture='assets/space_skybox.png',
    texture_scale=(20, 20),
    scale=5000000,
    double_sided=True,
    position=(0,0,0),
    parent=scene,
    shader=None
)


G = 6.67430e-11
SCALE = 2e-10
TIME_STEP = 60 * 24 * 60
planetes = []

G = 6.67430e-11
SCALE = 2e-10
TIME_STEP = 60 * 24 * 60
planetes = []

class CorpsCeleste(Entity):
    def __init__(self, nom, masse, position, vitesse, couleur, taille_affichee, periode_rotation=24):
        super().__init__(model='sphere', color=couleur, scale=taille_affichee, position=Vec3(*(np.array(position)*SCALE)))
        self.nom = nom
        self.masse = masse
        self.position_reelle = np.array(position, dtype='float64')
        self.vitesse = np.array(vitesse, dtype='float64')
        self.trajectoire = []
        self.lignes_trajectoire = None
        self.points_trajectoire = []
        self.periode_rotation = periode_rotation * 3600  # conversion en secondes
        self.angle_rotation = 0  # angle initial de rotation
        self.light = PointLight(parent=self, position=(0,0,0), color=self.color, shadows=False)
        self.light.scale = 0.5

    def mise_a_jour(self, corps_exterieurs):
        force_totale = np.array([0.0, 0.0, 0.0])
        for autre in corps_exterieurs:
            if autre is self:
                continue
            direction = autre.position_reelle - self.position_reelle
            distance = np.linalg.norm(direction)
            if distance < 1e3:
                continue
            force = G * self.masse * autre.masse / distance**2
            force_totale += force * direction / distance
        acceleration = force_totale / self.masse
        self.vitesse += acceleration * TIME_STEP
        self.position_reelle += self.vitesse * TIME_STEP

        self.position = Vec3(*(self.position_reelle * SCALE))
        self.trajectoire.append(self.position)

    
        self.position = Vec3(*(self.position_reelle * SCALE))
    
        self.points_trajectoire.append(self.position)

        if len(self.points_trajectoire) > 100:
            self.points_trajectoire.pop(0)

        if self.lignes_trajectoire:
            destroy(self.lignes_trajectoire)
        if len(self.points_trajectoire) > 1:
            bright_color = color.rgb(
                min(self.color.r * 2, 1),
                min(self.color.g * 2, 1),
                min(self.color.b * 2, 1)
            )
            self.lignes_trajectoire = Entity(
                model=Mesh(vertices=self.points_trajectoire, mode='line', thickness=10),
                color=bright_color,
                alpha=0.8
            )

soleil = CorpsCeleste(
    nom='Soleil',
    masse=1.989e30,
    position=[0, 0, 0],
    vitesse=[0, 0, 0],
    couleur=color.yellow,
    taille_affichee=350,  # Taille 350
    periode_rotation=25 * 24  # 25 jours pour le Soleil
)

planetes.append(soleil)

facteur_distance = 10

donnees_planetes = [
    {
        'nom': 'Mercure',
        'masse': 3.285e23,
        'distance': 5.791e10 * facteur_distance,
        'couleur': color.gray,
        'taille': 12.8,
        'periode_rotation': 58.6 * 24  # 58.6 jours
    },
    {
        'nom': 'Vénus',
        'masse': 4.867e24,
        'distance': 1.082e11 * facteur_distance,
        'couleur': color.orange,
        'taille': 12.0,
        'periode_rotation': -243 * 24  # 243 jours (rotation rétrograde)
    },
    {
        'nom': 'Terre',
        'masse': 5.972e24,
        'distance': 1.496e11 * facteur_distance,
        'couleur': color.azure,
        'taille': 12.0,
        'periode_rotation': 24  # 24 heures
    },
    {
        'nom': 'Mars',
        'masse': 6.39e23,
        'distance': 2.279e11 * facteur_distance,
        'couleur': color.red,
        'taille': 6.0,
        'periode_rotation': 24.6  # 24.6 heures
    },
    {
        'nom': 'Jupiter',
        'masse': 1.898e27,
        'distance': 7.785e11 * facteur_distance,
        'couleur': color.brown,
        'taille': 153.0,
        'periode_rotation': 9.9  # 9.9 heures
    },
    {
        'nom': 'Saturne',
        'masse': 5.683e26,
        'distance': 1.433e12 * facteur_distance,
        'couleur': color.yellow,
        'taille': 129.0,
        'periode_rotation': 10.7  # 10.7 heures
    },
    {
        'nom': 'Uranus',
        'masse': 8.681e25,
        'distance': 2.877e12 * facteur_distance,
        'couleur': color.cyan,
        'taille': 60.0,
        'periode_rotation': 17.2  # 17.2 heures
    },
    {
        'nom': 'Neptune',
        'masse': 1.024e26,
        'distance': 4.503e12 * facteur_distance,
        'couleur': color.blue,
        'taille': 51.0,
        'periode_rotation': 16.1  # 16.1 heures
    },
    {
        'nom': 'Pluton',
        'masse': 1.309e22,
        'distance': 5.906e12 * facteur_distance,
        'couleur': color.white,
        'taille': 3.0,
        'periode_rotation': 153 * 24  # 153 jours
    }
]

# Ajout des planètes avec vitesse orbitale circulaire correcte
for p in donnees_planetes:
    r = p['distance']
    v = np.sqrt(G * soleil.masse / r)
    position = np.array([r, 0, 0])
    vitesse = np.array([0, v, 0])
    
    planete = CorpsCeleste(
        nom=p['nom'],
        masse=p['masse'],
        position=position,
        vitesse=vitesse,
        couleur=p['couleur'],
        taille_affichee=p['taille'],
        periode_rotation=p['periode_rotation']
    )
    planetes.append(planete)

# Configuration de l'éclairage pour le soleil
soleil.light = PointLight(parent=soleil, position=(0,0,0), color=color.yellow, shadows=False)
soleil.light.scale = 50
soleil.light.intensity = 50
soleil.emissive_color = color.yellow

# Ajout d'informations sur les planètes
info_text = Text(text="", position=(-0.85, 0.35), scale=1, color=color.white)
selected_planet = None

def on_planet_click(planet):
    global selected_planet
    selected_planet = planet
    info_text.text = f"{planet.nom}\nMasse: {planet.masse:.2e} kg\nPériode rotation: {planet.periode_rotation/3600:.1f} h"

# Ajouter des collisions pour le clic sur les planètes
for planet in planetes:
    planet.collider = SphereCollider(planet, center=Vec3(0,0,0), radius=0.5)
    planet.on_click = lambda p=planet: on_planet_click(p)

# Interface de contrôle
temps_ecoule = 0
jours_ecoule_text = Text(text=f"Jours écoulés: 0", position=(-0.85, 0.45), scale=1.5, color=color.white)
vitesse_text = Text(text=f"Vitesse: 1x", position=(-0.85, 0.40), scale=1, color=color.white)
simulation_speed = 1

# Texte pour les coordonnées du vaisseau
coordinates_text = Text(
    text='Coordinates: X: 0 Y: 0 Z: 0',
    position=(0.5, 0.45),
    scale=1,
    color=color.white
)

# Fonction de mise à jour pour chaque frame
def update():
    if not selection_faite:
        return
        
    global temps_ecoule, simulation_speed
    
    if mouse.locked:
    # Rotation du vaisseau avec la souris
        vaisseau.rotation_y += mouse.velocity[0] * 1000 * time.dt
        vaisseau.rotation_x = clamp(
            vaisseau.rotation_x - mouse.velocity[1] * 1000 * time.dt,
            -60,
            60
        )

    # Configuration de la caméra
    cam_distance = 2000
    cam_height = 0.5
    
    # Calcul de la position de la caméra relative au vaisseau
    ship_forward = vaisseau.forward
    ship_up = vaisseau.up
    
    # Position derrière le vaisseau
    target_pos = vaisseau.position - ship_forward * cam_distance + Vec3(0, cam_height, 0)
    
    # Lissage du mouvement
    camera.position = lerp(camera.position, target_pos, time.dt * 15)
    
    # Orientation de la caméra
    camera.look_at(vaisseau, axis='forward')
    
    # Ajustement de la rotation pour suivre l'inclinaison du vaisseau
    camera.rotation_x = vaisseau.rotation_x
    camera.rotation_z = 0

    # Mouvement vers l'avant
    if held_keys['w']:
        if held_keys['shift']:
            vaisseau.position += vaisseau.forward * 100000 * time.dt
        vaisseau.position += vaisseau.forward * 10000 * time.dt
    
    # Configuration de la caméra (3e personne)
    if not held_keys['f']:
        cam_distance = 3000
        
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

    # Appliquer la vitesse de simulation
    for _ in range(simulation_speed*10):
        for corps in planetes:
            corps.mise_a_jour(planetes)
        temps_ecoule += TIME_STEP
    
    jours = int(temps_ecoule / (60*60*24))
    jours_ecoule_text.text = f"Jours écoulés: {jours}"
    
    # Mise à jour des coordonnées du vaisseau
    coordinates_text.text = f'Position: X: {int(vaisseau.x)} Y: {int(vaisseau.y)} Z: {int(vaisseau.z)}'

# Gestion des entrées
def input(key):
    global simulation_speed
    
    if key == 'escape':
        mouse.locked = not mouse.locked
    
    if key == '+':
        simulation_speed = min(10, simulation_speed + 1)
        vitesse_text.text = f"Vitesse: {simulation_speed}x"
    if key == '-':
        simulation_speed = max(1, simulation_speed - 1)
        vitesse_text.text = f"Vitesse: {simulation_speed}x"
    if key == 'r':
        reset_simulation()

def reset_simulation():
    global temps_ecoule
    temps_ecoule = 0
    for i, p in enumerate(donnees_planetes):
        if i+1 < len(planetes):
            r = p['distance']
            planetes[i+1].position_reelle = np.array([r, 0, 0])
            planetes[i+1].vitesse = np.array([0, np.sqrt(G * soleil.masse / r), 0])
            planetes[i+1].position = Vec3(*(planetes[i+1].position_reelle * SCALE))
            
            for ligne in planetes[i+1].lignes_trajectoire:
                destroy(ligne)
            planetes[i+1].lignes_trajectoire = []
            planetes[i+1].trajectoire = [planetes[i+1].position]

# Instructions
instructions = Text(
    text="Contrôles:\n"
         "ZQSD/WASD : déplacer vaisseau\n"
         "Souris : orientation\n"
         "Shift : accélérer\n"
         "Espace/C : monter/descendre\n"
         "F : vue 1ère personne\n"
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