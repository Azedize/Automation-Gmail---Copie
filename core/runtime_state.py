from collections import deque


class SharedRuntimeState:
    # Cette classe centralise les données d'état utilisées pendant
    # l'exécution de l'application.
    #
    # "Runtime" signifie que ces données représentent l'état actuel
    # de l'application pendant qu'elle fonctionne.
    #
    # "Shared" signifie que plusieurs parties de l'application
    # peuvent accéder au même objet runtime_state.

    def __init__(self):
        # Le constructeur est exécuté automatiquement lors de la création
        # d'une instance de SharedRuntimeState.
        #
        # Exemple :
        # runtime_state = SharedRuntimeState()
        #
        # À ce moment, toutes les variables ci-dessous sont initialisées.

        # Dictionnaire contenant les sessions Firefox actives.
        # Le dictionnaire est adapté lorsqu'on veut associer une clé
        # à une valeur, par exemple :
        # session_id -> objet/session Firefox.
        #
        # Exemple :
        # self.firefox_sessions["session_123"] = firefox_session
        self.firefox_sessions = {}

        # deque (Double-Ended Queue) utilisée pour stocker les logs
        # actuellement conservés en mémoire.
        #
        # Une deque permet d'ajouter et de supprimer rapidement
        # des éléments aux deux extrémités.
        #
        # Elle est particulièrement pratique si l'application veut
        # conserver seulement les derniers logs :
        # append()  -> ajouter un nouveau log
        # popleft() -> supprimer le plus ancien log
        self.logs = deque()

        # Liste contenant les PID (Process ID) des processus lancés
        # ou suivis par l'application.
        #
        # Une liste est utilisée ici car on a simplement besoin
        # de conserver plusieurs PID dans un ordre donné.
        self.process_pids = []

        # Dictionnaire utilisé pour gérer les badges de notification.
        #
        # Exemple :
        # "messages" -> 3
        # "errors"   -> 1
        #
        # Le dictionnaire permet donc d'associer un type de notification
        # à son nombre actuel.
        self.notification_badges = {}

        # Set contenant les emails actuellement actifs.
        #
        # Un set garantit qu'une même valeur ne sera présente
        # qu'une seule fois.
        #
        # Il est également très efficace pour vérifier rapidement
        # si un email existe déjà :
        # if email in self.active_emails:
        #
        # Cela peut notamment éviter de traiter deux fois
        # le même compte simultanément.
        self.active_emails = set()

        # Indique si le système de traitement/surveillance des logs
        # est actuellement actif.
        #
        # True  -> le traitement peut continuer.
        # False -> le traitement doit s'arrêter.
        self.logs_running = True

        # Nombre d'emails ou de tâches qui restent à traiter.
        #
        # Cette variable est un compteur numérique.
        # Elle commence à 0 car aucune tâche restante n'est connue
        # au moment de la création de l'objet.
        self.remaining_emails = 0

        # Contient le navigateur actuellement sélectionné.
        #
        # None signifie qu'aucun navigateur n'est sélectionné
        # au démarrage de l'application.
        #
        # Plus tard, cette variable peut contenir par exemple :
        # "firefox"
        # ou un objet représentant le navigateur.
        self.selected_browser = None


# Création de l'instance globale partagée.
#
# Cette ligne appelle automatiquement __init__().
# L'objet créé contient donc toutes les variables définies
# dans SharedRuntimeState.
#
# Les différentes parties de l'application peuvent ensuite
# accéder au même état via :
# runtime_state.firefox_sessions
# runtime_state.logs
# runtime_state.active_emails
# etc.
runtime_state = SharedRuntimeState()