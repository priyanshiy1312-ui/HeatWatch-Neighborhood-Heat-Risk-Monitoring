"""Plain-language advisories (English/Hindi). Amazon Bedrock when enabled, template otherwise."""
import logging

from . import config as C
from .recommender import nearest

log = logging.getLogger("heatwatch.advisory")
_cache: dict = {}
WHEN = {"en": ["today", "tomorrow", "the day after tomorrow"], "hi": ["आज", "कल", "परसों"]}

TEMPLATES = {
    "en": {
        "Extreme": "{ward}: extreme heat risk {when} ({temp}°C, feels like {fl}°C). Avoid outdoor work from 12 to 4 PM, drink water often, and keep elderly people and children in a cool place.{place}",
        "High": "{ward}: high heat risk {when} ({temp}°C). Avoid going out in the afternoon, drink plenty of water and wear light clothes.{place}",
        "Moderate": "{ward}: warm weather {when} ({temp}°C). Do not stay in the sun for long and drink enough water.",
        "Low": "{ward}: heat risk is low {when} ({temp}°C). Keep drinking water regularly.",
    },
    "hi": {
        "Extreme": "{ward} में {when} अत्यधिक गर्मी का खतरा है ({temp}°C, महसूस होगा {fl}°C)। दोपहर 12 से 4 बजे तक बाहर काम न करें, बार-बार पानी पिएं और बुज़ुर्गों व बच्चों को ठंडी जगह पर रखें।{place}",
        "High": "{ward} में {when} तेज़ गर्मी रहेगी ({temp}°C)। दोपहर में बाहर जाने से बचें, खूब पानी पिएं और हल्के कपड़े पहनें।{place}",
        "Moderate": "{ward} में {when} गर्मी रहेगी ({temp}°C)। धूप में लंबे समय तक न रहें और पर्याप्त पानी पिएं।",
        "Low": "{ward} में {when} गर्मी का खतरा कम है ({temp}°C)। फिर भी पानी पीते रहें।",
    },
}
PLACE = {"en": " Nearest water point: {name}, about {m} m away.",
         "hi": " नज़दीकी पानी का स्थान: {name}, लगभग {m} मीटर दूर।"}


def template_advisory(row: dict, lang: str, day: int, resources: list) -> str:
    wp, m = nearest(row, resources, "water")
    place = PLACE[lang].format(name=wp["name"], m=m) if wp else ""
    return TEMPLATES[lang][row["band"]].format(
        ward=row["name"], when=WHEN[lang][day], temp=round(row["temp_c"]),
        fl=round(row["feels_like_c"]), place=place)


def _bedrock(prompt: str) -> str:
    import boto3  # imported lazily so local runs need no AWS setup
    client = boto3.client("bedrock-runtime")
    resp = client.converse(modelId=C.BEDROCK_MODEL_ID,
                           messages=[{"role": "user", "content": [{"text": prompt}]}],
                           inferenceConfig={"maxTokens": 220, "temperature": 0.3})
    return resp["output"]["message"]["content"][0]["text"].strip()


def get_advisory(row: dict, lang: str, day: int, resources: list) -> dict:
    """Returns {'text', 'source': 'bedrock'|'template', 'lang'}."""
    lang = lang if lang in TEMPLATES else "en"
    key = (row["id"], row["date"], row["band"], lang)
    if key in _cache:
        return _cache[key]
    base = template_advisory(row, lang, day, resources)
    result = {"text": base, "source": "template", "lang": lang}
    if C.BEDROCK_ENABLED:
        language = "Hindi (Devanagari script)" if lang == "hi" else "English"
        prompt = (f"Rewrite this heat advisory in simple {language} for residents of an Indian city, "
                  f"in at most 45 words, calm and clear, as one SMS. Keep every number and place name "
                  f"exactly as given. Do not add medical claims or new facts.\n\nAdvisory: {base}")
        try:
            result = {"text": _bedrock(prompt), "source": "bedrock", "lang": lang}
        except Exception as exc:  # never fail the demo because of a model error
            log.warning("Bedrock unavailable (%s); using template", exc)
    _cache[key] = result
    return result
