"""Exemples simples du lien entre data science et algèbre linéaire.

Installation : pip install numpy
"""

import numpy as np


def operations_sur_les_vecteurs():
	"""Un vecteur peut représenter les caractéristiques d'un objet."""
	taille_etudiant = np.array([1.75, 68])
	moyenne_etudiant = np.array([1.70, 65])

	print("1) Vecteurs")
	print("Caractéristiques de l'étudiant :", taille_etudiant)
	print("Différence avec la moyenne :", taille_etudiant - moyenne_etudiant)
	print("Distance euclidienne :", np.linalg.norm(taille_etudiant - moyenne_etudiant))
	print(
		"Explication : en data science, les lignes d'un jeu de données sont souvent "
		"des vecteurs de caractéristiques.\n"
	)


def produit_scalaire_et_score():
	"""Calculer un score à partir de plusieurs caractéristiques."""
	caracteristiques = np.array([8, 7, 9], dtype=float)
	poids = np.array([0.2, 0.3, 0.5])
	score = caracteristiques @ poids

	print("2) Produit scalaire et score")
	print("Caractéristiques :", caracteristiques)
	print("Poids du modèle :", poids)
	print(f"Score calculé : {score:.2f}")
	print(
		"Explication : le produit scalaire multiplie chaque caractéristique par "
		"son poids, puis additionne les résultats. C'est le principe d'un modèle "
		"linéaire utilisé pour calculer un score.\n"
	)


def transformation_par_une_matrice():
	"""Transformer des coordonnées avec une matrice."""
	points = np.array(
		[
			[1, 0],
			[0, 1],
			[1, 1],
            [2, 3],
            [3, 2]
		],
		dtype=float,
	)
	matrice_echelle = np.array([[2, 0], [0, 3]], dtype=float)
	points_transformes = points @ matrice_echelle
	print("3) Transformation matricielle")
	print("Points avant transformation :\n", points)
	print("Points après transformation :\n", points_transformes)
	print(	"Explication : une matrice peut transformer toutes les lignes d'un jeu de données en une seule opération. Ici, la première variable est multipliée par 2 et la deuxième par 3.\n")


def classification_par_distance():
	"""Classer un nouvel exemple selon ses voisins les plus proches."""
	donnees = np.array(
		[
			[1, 1],
			[2, 1],
			[8, 8],
			[9, 8],
		],
		dtype=float,
	)
	classes = np.array(["petit", "petit", "grand", "grand"])
	nouvel_exemple = np.array([2, 2], dtype=float)
	distances = np.linalg.norm(donnees - nouvel_exemple, axis=1)
	indice_plus_proche = np.argmin(distances)

	print("4) Classification par distance")
	print("Nouvel exemple :", nouvel_exemple)
	print("Distances aux exemples connus :", np.round(distances, 2))
	print("Classe prédite :", classes[indice_plus_proche])
	print("Explication : chaque ligne est un vecteur. La distance euclidienne mesure la ressemblance entre deux vecteurs ; l'exemple le plus proche donne la classe prédite.\n")


def descente_de_gradient():
	"""Trouver progressivement le meilleur coefficient d'une droite."""
	heures = np.array([1, 2, 3, 4], dtype=float)
	notes = np.array([50, 60, 70, 80], dtype=float)
	X = np.column_stack((np.ones(heures.size), heures))
	parametres = np.zeros(2)
	pas = 0.01

	for _ in range(1000):
		predictions = X @ parametres
		erreurs = predictions - notes
		gradient = (2 / heures.size) * (X.T @ erreurs)
		parametres -= pas * gradient

	print("5) Descente de gradient")
	print("Paramètres appris [biais, coefficient] :", np.round(parametres, 2))
	print(f"Prédiction pour 5 heures : {np.array([1, 5]) @ parametres:.2f}")
	print(
		"Explication : le gradient indique dans quelle direction l'erreur augmente. "
		"On avance dans la direction opposée pour réduire l'erreur. La colonne de 1 "
		"permet d'apprendre le biais. Cette méthode est utilisée pour entraîner de "
		"nombreux modèles de machine learning.\n"
	)


def regression_lineaire():
	"""Prédire une note à partir du nombre d'heures étudiées."""
	heures = np.array([1, 2, 3, 4, 5], dtype=float)
	notes = np.array([52, 58, 65, 72, 80], dtype=float)

	# X contient une colonne de 1 pour le biais et une colonne pour les heures.
	X = np.column_stack((np.ones(heures.size), heures))

	# theta minimise l'erreur entre les notes observées et X @ theta.
	theta = np.linalg.pinv(X) @ notes
	prediction = np.array([1, 6]) @ theta

	print("6) Régression linéaire")
	print("Matrice X :\n", X)
	print("Paramètres [biais, coefficient] :", theta)
	print(f"Note prédite pour 6 heures : {prediction:.2f}")
	print(
		"Explication : la multiplication matricielle X @ theta combine les "
		"caractéristiques pour produire une prédiction.\n"
	)


def reduction_de_dimension():
	"""Résumer plusieurs variables grâce à la première composante principale."""
	donnees = np.array(
		[
			[10, 100],
			[12, 120],
			[14, 140],
			[16, 160],
		],
		dtype=float,
	)
	donnees_centrees = donnees - donnees.mean(axis=0)
	_, _, vecteurs_principaux = np.linalg.svd(donnees_centrees, full_matrices=False)
	projection = donnees_centrees @ vecteurs_principaux[0]

	print("7) PCA et réduction de dimension")
	print("Projection sur une seule dimension :", np.round(projection, 2))
	print(
		"Explication : la SVD trouve une direction importante dans les données. "
		"La projection conserve l'information principale avec moins de variables.\n"
	)


if __name__ == "__main__":
	operations_sur_les_vecteurs()
	produit_scalaire_et_score()
	transformation_par_une_matrice()
	classification_par_distance()
	descente_de_gradient()
	regression_lineaire()
	reduction_de_dimension()
