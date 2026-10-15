"""Deterministic, inspectable proposal recipes. Interest is not inferred taste."""

from copy import deepcopy

from .common import digest

SEEDS = [
    (
        "포근한 숲길 안내자",
        "Soft rounded storybook character with gentle broad face",
        "short fluffy wavy hair",
        "layered leaf-shaped cape over roomy tunic",
        "moss green, warm cream and muted ochre",
        "rounded compact silhouette with practical boots",
    ),
    (
        "날렵한 도시 탐험가",
        "Graphic angular animated character with narrow expressive face",
        "asymmetric swept undercut",
        "structured cropped jacket and tapered trousers",
        "charcoal, cool teal and coral accent",
        "tall lean silhouette with crisp geometric seams",
    ),
    (
        "차분한 별빛 여행자",
        "Elegant stylized character with long oval face and calm eyes",
        "long flowing hair with a small star clip",
        "long split travelling coat over a fitted waistcoat",
        "midnight blue, silver and dusty violet",
        "long curved silhouette and layered draping panels",
    ),
    (
        "장난스러운 기계 수리공",
        "Playful chibi-inspired character with compact face and bold brows",
        "chunky coiled hair tied high",
        "oversized utility overalls and short work cape",
        "warm rust, cream and navy",
        "short sturdy silhouette with oversized pockets",
    ),
    (
        "도자기 정원 지킴이",
        "Minimal sculptural character with soft geometric facial planes",
        "smooth bell-shaped bob",
        "wide bell coat over a pleated long skirt",
        "porcelain white, sage and pale peach",
        "broad bell silhouette with clean graphic edges",
    ),
    (
        "낡은 책방의 마법사",
        "Whimsical mature animation-inspired character with pronounced curved nose",
        "loose shoulder-length curls",
        "asymmetric knit vest, long sleeves and layered skirt-trousers",
        "plum, walnut and faded gold",
        "relaxed sloped silhouette with rounded layers",
    ),
    (
        "가벼운 바람 항해사",
        "Bright stylized character with a wide friendly face",
        "braided hair gathered into two low loops",
        "short sailor-like poncho and flowing culottes",
        "cloud blue, ivory and burnt orange",
        "airy triangular silhouette with clear open spaces",
    ),
    (
        "조용한 수정 기록자",
        "Sleek fantastical character with sharp cheek planes and soft eyes",
        "sculpted straight hair with long side locks",
        "high-collared layered robe with articulated shoulder pieces",
        "deep indigo, pale mint and copper",
        "slender column silhouette with offset shoulder volume",
    ),
]
PART_KEYS = {
    "face": "face.design",
    "hair": "hair.design",
    "outfit": "outfit.design",
    "body": "body.design",
    "accessories": "accessories.design",
    "palette": "palette.intent",
}
VARIANTS = {
    "face": [
        "a broader soft face with low cheek volume and gently spaced eyes",
        "a longer face with a defined jaw and compact eyes",
        "a round compact face with stronger brows and a small angular chin",
        "an oval face with a narrow chin and broad softly curved cheeks",
    ],
    "hair": [
        "a clean chin-length geometric bob with an asymmetric side part",
        "two thick low braids with loose curled ends",
        "a high swept crest with short close sides",
        "a broad shoulder-length wavy mass with a low tied section",
    ],
    "outfit": [
        "a cropped structured vest over a long pleated tunic and tapered trousers",
        "a wide flowing cape over a fitted high-collar coat",
        "a short layered utility jacket over broad culottes and sturdy boots",
        "a long asymmetrical wrap coat with slim sleeves and a high waist",
    ],
    "body": [
        "a compact rounded body silhouette with shorter limbs",
        "a tall narrow body silhouette with long relaxed limbs",
        "a sturdy broad-shouldered silhouette with a long torso",
        "a gently tapered silhouette with broader lower-body volume",
    ],
    "accessories": [
        "one small asymmetric leaf brooch attached at the collar",
        "a pair of articulated shoulder clasps and a narrow waist pouch",
        "a single sculptural ear ornament and a compact belt case",
        "a broad woven sash and an offset rounded satchel",
    ],
    "palette": [
        "warm ivory, muted burgundy and soft gold",
        "deep teal, pale gray and burnt orange",
        "dusty lavender, cream and forest green",
        "charcoal, pale blue and copper",
    ],
}


def prop(value):
    return {
        "value": value,
        "state": "proposed",
        "sourceEventIds": [],
        "sourceDepictionLinkIds": [],
        "notes": "",
    }


def seed(index, brief=""):
    title, face, hair, outfit, palette, body = SEEDS[index % len(SEEDS)]
    cycle = index // len(SEEDS)
    if cycle:
        hair = SEEDS[(index + cycle) % len(SEEDS)][2]
        outfit = SEEDS[(index + 2 * cycle) % len(SEEDS)][3]
        palette = SEEDS[(index + 3 * cycle) % len(SEEDS)][4]
        title += " · 새 해석"
    return title, {
        "morphology": "humanoid",
        "properties": {
            "design.description": prop("Reusable stylized avatar character. " + brief),
            "face.design": prop(face),
            "hair.design": prop(hair),
            "outfit.design": prop(outfit),
            "palette.intent": prop(palette),
            "body.design": prop(body),
        },
        "componentRelations": [],
        "unresolvedDecisions": [
            "Unseen rear construction, attachments and model implementation remain unspecified."
        ],
    }


def develop(source, part, step, preserved, frozen_keys):
    spec = deepcopy(source)
    key = PART_KEYS[part]
    if part in preserved or key in frozen_keys:
        raise ValueError(
            "보존한 부분은 먼저 명시적으로 해제하거나 다른 부분을 바꿔 주세요."
        )
    before = spec["properties"].get(key, {}).get("value")
    choices = VARIANTS[part]
    value = next(
        choices[(step + i) % len(choices)]
        for i in range(len(choices))
        if choices[(step + i) % len(choices)] != before
    )
    spec["properties"][key] = prop(value)
    # A silhouette/hair/outfit change is intended design variation, never camera variation.
    return spec


def signature(spec):
    return digest(
        {
            "morphology": spec["morphology"],
            "properties": {
                key: value["value"]
                for key, value in spec["properties"].items()
                if key != "design.description"
            },
            "relations": spec["componentRelations"],
        }
    )
