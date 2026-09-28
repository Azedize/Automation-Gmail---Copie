import time
from PyQt6.QtCore import QThread, pyqtSignal


class ApplicationLogDisplayThread(QThread):
    # Signal Qt utilisé pour transmettre un message de log sous forme de texte
    # depuis ce Thread vers la partie de l'application qui affiche les logs.
    #
    # Le type "str" indique que le signal transportera une chaîne de caractères.
    #
    # Exemple :
    # self.log_signal.emit("Application started")
    #
    # La GUI peut ensuite connecter ce signal à une méthode qui affiche
    # le message dans un widget.
    log_signal = pyqtSignal(str)

    def __init__(self, logs, is_running, parent=None):
        # Initialise la partie QThread héritée de la classe parente.
        #
        # parent permet à Qt de connaître le widget ou l'objet parent
        # responsable de ce Thread lorsqu'un parent est fourni.
        super().__init__(parent)

        # Conserve une référence vers la collection contenant les logs.
        #
        # Cette collection est généralement une deque partagée avec
        # les autres parties de l'application.
        #
        # Le Thread ne crée pas une nouvelle collection :
        # il travaille sur la même collection reçue en paramètre.
        self.LOGS = logs

        # Conserve la fonction utilisée pour déterminer si l'application
        # doit continuer à fonctionner.
        #
        # Cette valeur est généralement une fonction/callback appelée
        # avec self.is_running().
        #
        # Exemple :
        # def is_running():
        #     return application_is_running
        self.is_running = is_running

        # Flag local permettant de demander l'arrêt de ce Thread.
        #
        # False = le Thread peut continuer à fonctionner.
        # True  = un arrêt a été demandé.
        #
        # Le Thread n'est pas arrêté brutalement : run() vérifie cette valeur
        # et termine proprement sa boucle.
        self.stop_flag = False

    def run(self):
        # Méthode principale exécutée lorsque le Thread est démarré
        # avec thread.start().
        #
        # Son rôle est de surveiller la collection LOGS et de transmettre
        # progressivement les logs disponibles via log_signal.

        # Le Thread continue tant que :
        #
        # 1. l'application indique qu'elle est toujours en fonctionnement ;
        # 2. aucun arrêt local n'a été demandé pour ce Thread.
        #
        # Dès qu'une des deux conditions devient False,
        # la boucle se termine et le Thread peut être arrêté.
        while self.is_running() and not self.stop_flag:

            # Vérifie si la collection LOGS contient au moins un élément.
            #
            # Si LOGS contient des messages, on récupère le prochain log
            # et on l'envoie vers la GUI.
            if self.LOGS:

                # popleft() récupère et supprime le premier élément de la deque.
                #
                # Cela permet de traiter les logs dans leur ordre d'arrivée :
                #
                # LOGS = [log1, log2, log3]
                #
                # popleft() -> log1
                # LOGS devient [log2, log3]
                #
                # Le log récupéré est ensuite envoyé via le signal Qt.
                self.log_signal.emit(self.LOGS.popleft())

            else:
                # Aucun log n'est actuellement disponible.
                #
                # Le Thread attend une seconde avant de vérifier à nouveau.
                # Cela évite une boucle continue qui vérifierait LOGS
                # des milliers de fois par seconde et consommerait inutilement
                # des ressources CPU.
                time.sleep(1)

    def stopThread(self):
        # Demande l'arrêt propre du Thread.
        #
        # Cette méthode ne tue pas le Thread brutalement.
        # Elle modifie simplement le flag contrôlé par la boucle run().

        # Indique à run() qu'un arrêt a été demandé.
        #
        # La condition :
        #
        #     not self.stop_flag
        #
        # deviendra False au prochain contrôle de la boucle.
        self.stop_flag = True

        # Attend que le Thread ait réellement terminé son exécution.
        #
        # Cela permet de s'assurer que le Thread est complètement arrêté
        # avant que le programme continue ou détruise l'objet.
        self.wait()
