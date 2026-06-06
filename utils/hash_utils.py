
import hashlib


def compute_hash_from_bytes(data: bytes, algorithm: str = "sha256") -> str:
    """
    Calcule le hash d'un contenu binaire (bytes).

    Arguments :
        data (bytes)      : le contenu du fichier sous forme binaire
        algorithm (str)   : l'algorithme à utiliser (par défaut "sha256")

    Retourne :
        str : le hash en hexadécimal (ex: "a3f5b2c1d4...")

    Qu'est-ce que SHA-256 ?
    C'est l'algorithme de hachage le plus utilisé dans l'industrie.
    Il produit une empreinte de 64 caractères hexadécimaux.
    Il est très rapide à calculer et pratiquement impossible à falsifier.

    Pourquoi passer des "bytes" et pas une chaîne de texte ?
    Parce que les fichiers (PDF, HTML, CSV...) ne sont pas toujours
    du texte pur. Les bytes représentent le contenu brut universel,
    peu importe l'encodage ou le type de fichier.
    """
    hasher = hashlib.new(algorithm)
    hasher.update(data)
    return hasher.hexdigest()


def compute_hash_from_file(file_path: str, algorithm: str = "sha256") -> str:
    """
    Calcule le hash d'un fichier sur le disque.

    Arguments :
        file_path (str)   : chemin vers le fichier (ex: "raw_data/web/page.html")
        algorithm (str)   : l'algorithme à utiliser (par défaut "sha256")

    Retourne :
        str : le hash en hexadécimal

    Pourquoi lire par blocs de 8192 bytes ?
    Si on lit tout le fichier d'un coup en mémoire, et que le fichier
    est très gros (un PDF de 500 MB par exemple), cela peut faire planter
    le programme par manque de mémoire. Lire par blocs de 8192 bytes
    (= 8 kilooctets) est une taille standard efficace qui fonctionne
    pour tous les types et tailles de fichiers.
    """
    hasher = hashlib.new(algorithm)

    with open(file_path, "rb") as f:   # "rb" = read binary (lecture binaire)
        while True:
            block = f.read(8192)       # lire 8192 bytes à la fois
            if not block:              # si le bloc est vide, on a atteint la fin
                break
            hasher.update(block)       # ajouter ce bloc au calcul du hash

    return hasher.hexdigest()


def compute_hash_from_text(text: str, encoding: str = "utf-8") -> str:
    """
    Calcule le hash d'une chaîne de texte.

    Arguments :
        text (str)       : le texte à hasher (ex: contenu HTML d'une page)
        encoding (str)   : l'encodage du texte (par défaut "utf-8")

    Retourne :
        str : le hash en hexadécimal

    Pourquoi cette fonction en plus de compute_hash_from_bytes ?
    Parce que le Membre chargee de la tache de (scraping web)  aura besion de récupère du texte HTML
    directement en mémoire, pas un fichier sur le disque. Il est plus
    pratique pour lui d'appeler compute_hash_from_text(html_content)
    plutôt que de sauvegarder d'abord dans un fichier puis calculer le hash.

    Cette fonction encode d'abord le texte en bytes, puis appelle
    compute_hash_from_bytes. Cela garantit que la méthode de calcul
    est toujours la même.
    """
    data = text.encode(encoding)
    return compute_hash_from_bytes(data)