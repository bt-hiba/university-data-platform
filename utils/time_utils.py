
from datetime import datetime, timezone

def get_utc_now() -> datetime:
    """
    Retourne la date et heure actuelles en UTC (temps universel coordonné).

    Pourquoi UTC et pas l'heure locale ?
    Parce que l'heure locale change selon le fuseau horaire et l'heure d'été.
    UTC est un standard international stable, utilisé dans tous les systèmes
    de données professionnels. Cela évite des bugs étranges si le serveur
    est dans un pays et les données dans un autre.
    """
    return datetime.now(timezone.utc)


def get_timestamp_str() -> str:
    """
    Retourne le timestamp actuel sous forme de chaîne de caractères lisible.
    Format : "2026-06-05T14:30:00+00:00"

    Ce format s'appelle ISO 8601. C'est le standard international pour
    représenter une date et heure. Il est lisible par les humains ET
    par toutes les bibliothèques Python, les bases de données, etc.

    Utilisé dans les logs et les métadonnées pour savoir quand
    une ingestion a eu lieu.
    """
    return get_utc_now().isoformat()


def get_date_parts() -> dict:
    """
    Retourne les composantes de la date actuelle dans un dictionnaire.

    Retourne :
        dict avec les clés : year, month, day

    Exemple de valeur retournée :
        {"year": "2026", "month": "06", "day": "05"}

    Pourquoi les mois et jours ont-ils 2 chiffres ("06" et pas "6") ?
    zfill(2) ajoute un zéro devant si nécessaire. Cela garantit que le
    chemin MinIO est toujours correct.
    """
    now = get_utc_now()
    return {
        "year":  str(now.year),
        "month": str(now.month).zfill(2),
        "day":   str(now.day).zfill(2)
    }


def build_minio_date_path(source: str) -> str:
    """
    Construit le chemin partitionné par date pour MinIO.

    Argument :
        source (str) : le nom de la source de données (ex: "um5", "openalex", "csv")

    Retourne :
        str : chemin partitionné (ex: "source=um5/year=2026/month=06/day=05")

    Pourquoi partitionner par date ?
    C'est une convention standard dans les data lakes. Ça permet de :
    - retrouver rapidement les données d'un jour donné
    - rejouer (reprocesser) uniquement les données d'une période
    - ne pas mélanger les données de différents jours dans un même dossier

    Ce chemin correspond exactement au format demandé  :
        s3://raw-web-html/source=faculty_site/year=2026/month=03/day=25/...
    """
    parts = get_date_parts()
    return (
        f"source={source}/"
        f"year={parts['year']}/"
        f"month={parts['month']}/"
        f"day={parts['day']}"
    )