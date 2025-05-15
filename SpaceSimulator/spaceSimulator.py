from ursina import *
import numpy as np
import csv

app = Ursina()
window.color = color.black
scene.background = color.black



def creer_skybox():    
    # Ajouter des étoiles aléatoires
    for _ in range(1000):
        # Position aléatoire sur la sphère
        angle1 = random.uniform(0, math.pi * 2)
        angle2 = random.uniform(0, math.pi)
        x = math.sin(angle2) * math.cos(angle1) * 1000  # Agrandir le skybox
        y = math.sin(angle2) * math.sin(angle1) * 1000
        z = math.cos(angle2) * 1000
        
        taille = random.uniform(0.1, 0.4)
        
        # Créer une étoile (petit point lumineux)
        Entity(
            model='sphere',
            color=color.white,
            position=(x, y, z),
            scale=taille,
            billboard=True
        )
    return

skybox = creer_skybox()

G = 6.67430e-11  # constante gravitationnelle
SCALE = 2e-10    # réduction des distances pour affichage (modifié pour éloigner les planètes)
TIME_STEP = 60 * 24 * 60  # 1 jour en secondes
planetes = []

class CorpsCeleste(Entity):
    def __init__(self, nom, masse, position, vitesse, couleur, taille_affichee, periode_rotation=24):
        super().__init__(model='sphere', color=couleur, scale=taille_affichee, position=Vec3(*(np.array(position)*SCALE)))
        self.nom = nom
        self.masse = masse
        self.position_reelle = np.array(position, dtype='float64')
        self.vitesse = np.array(vitesse, dtype='float64')
        self.trajectoire = []
        self.lignes_trajectoire = []
        self.periode_rotation = periode_rotation * 3600  # conversion en secondes
        self.angle_rotation = 0  # angle initial de rotation
        self.light = PointLight(parent=self, position=(0,0,0), color=self.color, shadows=False)
        self.light.scale = 0.5


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
        self.position = Vec3(*(self.position_reelle * SCALE))
        self.trajectoire.append(self.position)       

        # tracer la trajectoire (max 200 points pour éviter surcharge)
        if len(self.trajectoire) > 1:
            if len(self.lignes_trajectoire) > 200:
                destroy(self.lignes_trajectoire[0])
                self.lignes_trajectoire.pop(0)
                self.trajectoire.pop(0)
            
            # Ajouter une nouvelle ligne
            ligne = Entity(
                model=Mesh(vertices=[self.trajectoire[-2], self.trajectoire[-1]], mode='line', thickness=2),
                color=self.color
            )
            self.lignes_trajectoire.append(ligne)

# Soleil (station centrale)
soleil = CorpsCeleste(
    nom='Soleil',
    masse=1.989e30,
    position=[0, 0, 0],
    vitesse=[0, 0, 0],
    couleur=color.yellow,
    taille_affichee=200,  # Taille 500 comme demandé
    periode_rotation=25 * 24  # 25 jours pour le Soleil
)


planetes.append(soleil)

#Fonction pour rendre le soleil lumineux
def creer_soleil_stylise():
    # Augmenter l'intensité lumineuse du Soleil
    # planetes[0].light.intensity = 2000
    # planetes[0].light.scale = 500
    planetes[0].color = color.rgb(255, 150, 0)  # Orange vif

    planetes[0].emissive_color = color.rgb(255, 150, 0)
    

# Facteur d'échelle supplémentaire pour les distances des planètes
facteur_distance = 10

# Données des planètes avec distances réalistes et périodes de rotation
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
    # Vitesse orbitale circulaire: v = sqrt(G*M/r)
    v = np.sqrt(G * soleil.masse / r)
    # Orientation correcte de la vitesse pour une orbite circulaire
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

# Ajout d'informations sur les planètes
info_text = Text(text="", position=(-0.85, 0.35), scale=1, color=color.white)
selected_planet = None

def on_planet_click(planet):
    global selected_planet
    selected_planet = planet
    info_text.text = f"{planet.nom}\n" \
                    f"Masse: {planet.masse/10**24:.2f} × 10²⁴ kg\n" \
                    f"Période rotation: {planet.periode_rotation/3600:.1f} h\n" \
                    f"Position: ({planet.position_reelle[0]/10**9:.1f}, {planet.position_reelle[1]/10**9:.1f}, {planet.position_reelle[2]/10**9:.1f}) × 10⁹ m\n" \
                    f"Vitesse: ({planet.vitesse[0]/1000:.1f}, {planet.vitesse[1]/1000:.1f}, {planet.vitesse[2]/1000:.1f}) km/s\n" \
                    f"Distance au soleil: {np.linalg.norm(planet.position_reelle)/10**9:.1f} × 10⁹ m"
# Ajouter des collisions pour le clic sur les planètes
for planet in planetes:
    planet.collider = SphereCollider(planet, center=Vec3(0,0,0), radius=0.5)
    planet.on_click = lambda p=planet: on_planet_click(p)

# Interface de contrôle
temps_ecoule = 0
jours_ecoule_text = Text(text=f"Jours écoulés: 0", position=(-0.85, 0.45), scale=1.5, color=color.white)
vitesse_text = Text(text=f"Vitesse: 1x", position=(-0.85, 0.40), scale=1, color=color.white)
simulation_speed = 1

creer_soleil_stylise()

def update():
    global temps_ecoule, simulation_speed
    
    # Appliquer la vitesse de simulation
    for _ in range(simulation_speed*10):
        for corps in planetes:
            corps.mise_a_jour(planetes)
        temps_ecoule += TIME_STEP
    
    jours = int(temps_ecoule / (60*60*24))
    jours_ecoule_text.text = f"Jours écoulés: {int(jours/50)}"

def input(key):
    global simulation_speed
    if key == '+':
        simulation_speed = min(10, simulation_speed + 1)
        vitesse_text.text = f"Vitesse: {simulation_speed}x"
    if key == '-':
        simulation_speed = max(1, simulation_speed - 1)
        vitesse_text.text = f"Vitesse: {simulation_speed}x"
    if key == 'r':
        reset_simulation()
    if key == 'e':  
        exporter_csv()


def exporter_csv():
    try:
        # Création du dossier 'exports' si nécessaire
        if not os.path.exists('SpaceSimulator/exports'):
            os.makedirs('SpaceSimulator/exports')
            
        # Chemin du fichier CSV
        fichier_csv = os.path.join('SpaceSimulator/exports', f'planetes_jour_{int((temps_ecoule / (60*60*24))/50)}.csv')
        
        # Ouverture du fichier en mode écriture
        with open(fichier_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Nom', 'Masse (kg)', 'Position X (m)', 'Position Y (m)', 'Position Z (m)', 
                            'Vitesse X (m/s)', 'Vitesse Y (m/s)', 'Vitesse Z (m/s)', 
                            'Distance au soleil (m)', 'Période de rotation (h)'])
            
            # Données pour chaque planète
            for corps in planetes:
                distance_soleil = np.linalg.norm(corps.position_reelle - planetes[0].position_reelle)
                writer.writerow([
                    corps.nom,
                    corps.masse,
                    corps.position_reelle[0],
                    corps.position_reelle[1],
                    corps.position_reelle[2],
                    corps.vitesse[0],
                    corps.vitesse[1],
                    corps.vitesse[2],
                    distance_soleil,
                    corps.periode_rotation / 3600  # Conversion en heures
                ])
        
        # Notification de réussite
        notification = Text(text=f"Données exportées: {fichier_csv}", position=(0, 0), scale=1.5, color=color.green)
        destroy(notification, delay=3)  # La notification disparaît après 3 secondes
        
    except Exception as e:
        # Notification d'erreur
        notification = Text(text=f"Erreur d'exportation: {str(e)}", position=(0, 0), scale=1.5, color=color.red)
        destroy(notification, delay=3)

def reset_simulation():
    global temps_ecoule
    temps_ecoule = 0
    for i, p in enumerate(donnees_planetes):
        if i+1 < len(planetes):  # +1 pour le soleil qui est en position 0
            r = p['distance']
            planetes[i+1].position_reelle = np.array([r, 0, 0])
            planetes[i+1].vitesse = np.array([0, np.sqrt(G * soleil.masse / r), 0])
            planetes[i+1].position = Vec3(*(planetes[i+1].position_reelle * SCALE))
            # Nettoyer les trajectoires
            for ligne in planetes[i+1].lignes_trajectoire:
                destroy(ligne)
            planetes[i+1].lignes_trajectoire = []
            planetes[i+1].trajectoire = [planetes[i+1].position]

# Instructions mises à jour
instructions = Text(
    text="Contrôles:\nr : réinitialiser\ne : exporter CSV\nClic Gauche : info planète\nClic Droit : rotation\nMolette : zoom +/-",
    position=(0.5, 0.45),
    scale=1,
    color=color.white
)

# Caméra et contrôles - ajuster pour voir le système entier
camera.position = (0, 100, -200)
camera.clip_plane_far = 1_000_000_000
camera.look_at(soleil)
EditorCamera()  # Permet de contrôler la caméra avec la souris
scene.ambient_color = color.rgba(30, 30, 30, 255)

# Lumière
DirectionalLight(direction=(0.5, -1, -0.5), color=color.white)
AmbientLight(color=color.rgba(0.2, 0.2, 0.2, 1))

app.run()