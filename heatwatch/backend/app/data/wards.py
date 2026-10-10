"""Load ward polygons + inputs from data/wards.geojson (SAMPLE/proxy values, see scripts/)."""
import json
from functools import lru_cache

from .. import config as C
from ..models import WardInputs


@lru_cache(maxsize=1)
def load_wards() -> list[dict]:
    """Return [{'inputs': WardInputs, 'geometry': {...}}] for every ward."""
    gj = json.loads((C.DATA_DIR / "wards.geojson").read_text())
    return [{"inputs": WardInputs(**f["properties"]), "geometry": f["geometry"]}
            for f in gj["features"]]
