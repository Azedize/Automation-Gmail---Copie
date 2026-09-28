from queue import Queue
from watchdog.events import FileSystemEventHandler


class DownloadFileEventHandler(FileSystemEventHandler):
    # Ce Handler reçoit les événements générés par Watchdog
    # lorsqu'un fichier ou un dossier est créé, déplacé ou renommé.
    # Il ne traite pas directement les fichiers : il transmet leur chemin
    # à une Queue afin qu'un Worker/Consumer puisse les traiter séparément.

    def __init__(self, file_queue: Queue):
        # Le constructeur est exécuté automatiquement lors de la création
        # d'une instance de DownloadFileEventHandler.
        # Il reçoit la Queue partagée entre le Producteur et le Consumer.
        super().__init__()

        # On conserve une référence vers la Queue dans l'objet.
        # Cette Queue sert de zone d'attente pour les fichiers détectés.
        # Le Handler joue le rôle de Producteur : il ajoute les tâches avec put().
        self.file_queue = file_queue

    def on_created(self, event):
        # Cette méthode est appelée automatiquement par Watchdog
        # lorsqu'un nouvel élément est créé dans le dossier surveillé.
        #
        # event contient les informations sur l'événement détecté,
        # notamment le chemin de l'élément et le fait qu'il s'agit
        # ou non d'un dossier.

        # On ignore les dossiers : notre traitement concerne uniquement
        # les fichiers qui doivent être ajoutés à la Queue.
        if not event.is_directory:
            # event.src_path représente le chemin du fichier nouvellement créé.
            # On ajoute ce chemin dans la Queue afin qu'un Worker/Consumer
            # puisse récupérer et traiter le fichier plus tard.
            #
            # put() ajoute l'élément à la fin de la Queue selon le principe FIFO
            # (First In, First Out) : le premier fichier ajouté sera traité en premier.
            self.file_queue.put(event.src_path)

    def on_moved(self, event):
        # Cette méthode est appelée automatiquement par Watchdog
        # lorsqu'un élément est déplacé ou renommé.
        #
        # Exemple :
        # fichier temporaire -> fichier final
        #
        # Dans ce cas, le fichier possède un ancien chemin (src_path)
        # et un nouveau chemin (dest_path).

        # Comme dans on_created(), on ignore les dossiers.
        if not event.is_directory:
            # dest_path représente le nouvel emplacement du fichier après
            # le déplacement ou le renommage.
            #
            # On ajoute le nouveau chemin à la Queue afin que le Consumer
            # travaille avec l'emplacement actuel du fichier.
            self.file_queue.put(event.dest_path)
