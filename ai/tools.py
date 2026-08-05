import httpx
from langchain_core.tools import tool

@tool
def search_veterinary_adverse_events(
    medication: str,
    search_type: str = 'active_ingredient',
    species: str = "",
    limit: int = 5
) -> str:
    """Searches the FDA for veterinary adverse events reported for a medication.
 
    Args:
        medication: Brand name or active ingredient. E.g.: "Meloxicam", "Rimadyl".
        search_type: "active_ingredient" or "brand_name". Default: "active_ingredient".
        species: Filter by species. E.g.: "Dog", "Cat". Leave empty for all.
        limit: Number of cases (1-10). Default: 5.
    """
    BASE_URL = "https://api.fda.gov/animalandveterinary/event.json"
    limit = max(1, min(limit, 10))

    field = "drug.brand_name" if search_type == "brand_name" else "drug.active_ingredients.name"

    query = f"{field}:{medication}"
    if species:
        query += f' AND animal.species:"{species}"'

    try:
        resp = httpx.get(BASE_URL, params={"search": query, "limit": limit}, timeout=10.0)
        if resp.status_code == 200:
            return resp.text
        return f"Error from FDA API: {resp.status_code} - {resp.text}"
    except Exception as e:
        return f"Error contacting FDA API: {e}"