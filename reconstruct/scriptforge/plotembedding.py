"""The plot-embedding schema: 52 genres + 24 dimensions, each scored 0–5.

Transcribed from `plotemb.txt`. This replaces the ad-hoc narrative vector of
the original story root with a fixed, interpretable coordinate system that is
identical across every work in the corpus — which is what makes the corpus
aggregable, queryable, and usable as a generation control surface.

The scale is uniform and the anchors matter, so they are handed to the model
verbatim rather than paraphrased:

    0 Absent · 1 Trace · 2 Minor · 3 Moderate · 4 Strong · 5 Defining/Core

The load-bearing distinction is between **presence** and **structural
consequence**. A single chase that changes nothing is a 1. Several set pieces
that shape turns across acts is a 3. "Remove it and the story's identity
collapses" is a 5. A model left to its own devices scores everything 3–4; the
rubric text is what prevents that, so it is never abbreviated in the prompt.
"""

from __future__ import annotations

SCALE = {
    0: "Absent — the element does not operate in this work at all.",
    1: "Trace — appears once as colour; changes no outcome and no structure.",
    2: "Minor — touches a subplot or a few scenes; the core engine is elsewhere.",
    3: "Moderate — recurs and shapes turns in multiple acts, but does not lead.",
    4: "Strong — drives acts; decisions and reversals regularly hinge on it.",
    5: "Defining/Core — the spine. Remove it and the story's identity collapses.",
}

# --------------------------------------------------------------------------
# A) 52 genres, grouped as in the source
# --------------------------------------------------------------------------

GENRE_GROUPS: dict[str, dict[str, str]] = {
    "core": {
        "action_adventure": "Fast-paced physical danger, daring feats, high-stakes missions or journeys; problems solved through action under pressure.",
        "comedy": "Designed to amuse; wit, irony, farce and situational absurdity structure scenes and release tension.",
        "crime": "Illegal acts, the criminal ecosystem, or justice systems confronting them — heists, investigations, syndicates.",
        "drama": "Realistic, character-driven conflict and growth; emotions, relationships and choices carry the story.",
        "fantasy": "Magic, mythic beings or supernatural systems under internally consistent rules; secondary worlds or hidden strata of our own.",
        "historical_fiction": "Anchored in a real era where period constraints, events and figures shape choices.",
        "horror": "Designed to evoke fear, dread or nausea; threats the characters cannot fully understand or control.",
        "mystery": "Puzzles and investigation reveal hidden truths; the audience is cued to notice clues and anticipate reveals.",
        "romance": "A central love relationship develops through obstacles toward commitment or separation that defines the resolution.",
        "science_fiction": "Speculative technology or science alters society, ethics or survival; logic extrapolates from a central novum.",
        "thriller": "Sustained danger, reversals and time pressure create persistent anxiety and forward pull.",
        "western": "Frontier and liminal settings, rugged justice, community against outlaws; landscape as moral crucible.",
        "young_adult": "Teen point of view; identity, belonging and agency against authority anchor the conflicts.",
    },
    "speculative_hybrid": {
        "apocalyptic": "Catastrophe reshapes society; survival, scarcity and rebuilding dictate norms and ethics.",
        "cyberpunk": "High tech, low life — corporate power, hackers, augmentation and urban stratification define conflict.",
        "dark_fantasy": "Fantasy steeped in horror and corruption; morally grey magic where power carries rot or cost.",
        "dystopian": "Oppressive regimes and engineered conformity; surveillance, propaganda and scarcity structure life and resistance.",
        "epic_fantasy": "Vast scope, fate-of-nations conflict, prophecy and lineage, multi-faction politics over long arcs.",
        "gothic": "Brooding settings, secrets, decay and uneasy romance or mystery; place haunted by its history.",
        "low_fantasy": "Magical intrusion disturbs an otherwise realistic world; secrecy and overlap create tension.",
        "magical_realism": "Unexplained marvels occur in a realistic setting and are accepted as ordinary.",
        "mythic": "Draws on myth and legend; archetypes, trials and cyclical structures inform plot and symbol.",
        "space_opera": "Romantic large-scale adventure in space: empires, fleets, found families, melodramatic heroism.",
        "steampunk": "Alternate industrial age with steam tech, brass automata and class tension; invention and spectacle matter.",
        "sword_and_sorcery": "Fast-moving adventure with personal-scale magic and combat; roguish heroes, treasure, peril.",
        "time_travel": "Journeys across eras or loops; paradox risk, branching timelines or fixed points drive stakes.",
    },
    "suspense_intrigue": {
        "detective": "An investigator solves a case by gathering clues, testing hypotheses and unmasking the culprit.",
        "espionage": "Covert operations, tradecraft, deception and geopolitics drive high-stakes missions.",
        "legal_thriller": "Courtrooms and legal process are the battleground; outcomes hinge on procedure, precedent and advocacy.",
        "political_thriller": "Conspiracies, power struggles and public optics inside institutions propel danger and decision.",
        "psychological_thriller": "Tension centres on perception, identity, trust and manipulation; reality is blurred.",
        "techno_thriller": "Advanced technology, cyberwarfare or complex systems drive the threat and the tactics against it.",
    },
    "relationship_life": {
        "womens_fiction": "Contemporary women's lives — career, friendship, family, love — told with voice, humour and growth.",
        "coming_of_age": "A young protagonist moves toward maturity; identity, agency and belonging tested by rites of passage.",
        "family_drama": "Bonds, secrets and obligations within families generate conflict and change across generations.",
        "paranormal_romance": "A central love story with a supernatural being or power dynamic; mortality, secrecy, otherworld rules.",
    },
    "art_performance": {
        "dance_fiction": "Dancers, training and performance culture as the arena where ambition, rivalry and artistry are tested.",
        "music_fiction": "Music-making is central, or musical numbers carry story beats and emotional turns.",
        "showbiz_drama": "The entertainment industry as the setting where image, ambition and commerce collide.",
    },
    "adult": {
        "erotic_romance": "A love story where explicit intimacy and emotional development are interdependent.",
        "erotica": "Sexual encounters and fantasies are the primary focus; plot scaffolds intimate situations.",
        "softcore_erotic": "Sensually charged with limited explicitness; suggestion, mood and implication over graphic detail.",
        "hardcore_pornographic": "Focus almost exclusively on explicit sexual acts; non-sexual stakes minimal.",
    },
    "horror_variants": {
        "body_horror": "Fear centres on grotesque or uncontrollable change to the body — disease, mutation, invasive transformation.",
        "paranormal_horror": "Supernatural forces — ghosts, curses, entities — menace characters under uncertain, dangerous rules.",
        "slasher": "A killer targets victims; stalking and violent set pieces escalate fear and survival stakes.",
        "psychological_horror": "Fear derives from the mind — paranoia, intrusive thought, eroding sanity, ambiguous reality.",
    },
    "niche_mixed": {
        "satire": "Humour, irony and exaggeration expose flaws in individuals, institutions or culture from a critical position.",
        "sports_fiction": "Athletic competition is central; training, teamwork, discipline and season arcs determine identity and outcome.",
        "surreal": "Dream logic and strange juxtaposition override conventional causality; symbolism guides meaning.",
        "tragedy": "A protagonist's flaw or fate leads to downfall or irrevocable loss; catharsis through pity and fear.",
        "war_fiction": "Soldiers, battles and the social and psychological costs of warfare form the crucible.",
    },
}

GENRES: dict[str, str] = {k: v for group in GENRE_GROUPS.values() for k, v in group.items()}

# --------------------------------------------------------------------------
# B) 24 non-genre dimensions
# --------------------------------------------------------------------------

DIMENSION_GROUPS: dict[str, dict[str, str]] = {
    "emotional_tone": {
        "valence": "Positivity ↔ negativity of the whole. 0 pervasively bleak, ending without relief; 3 balanced, gains and losses share weight; 5 warmly optimistic, restorative and deserved without naivety.",
        "arousal": "Calm ↔ intensity. 0 tranquil, stakes seldom press; 3 regular moderate tension pushing choices; 5 relentless, crises chain with minimal relief.",
        "emotional_range": "Variety of feeling states. 0 monotone; 3 clear diversity across acts and POVs; 5 very wide and nuanced, ambivalent states common and purposeful.",
        "emotional_depth": "How deeply feelings are explored. 0 surface labels that don't alter choices; 3 regular introspection shaping behaviour; 5 transformative insight reframing identity and theme.",
        "bittersweetness": "Joy and sorrow intertwined. 0 univalent; 3 recurring bittersweet thread colouring turns; 5 the primary lens, sweetness married to grief in outcomes.",
    },
    "tension_engagement": {
        "suspense_threat": "0 outcomes feel assured; 3 steady threat informs choices throughout; 5 edge-of-seat danger in most scenes, safety rare and temporary.",
        "pacing_intensity": "0 very slow, change infrequent; 3 brisk momentum, frequent developments; 5 breakneck, cascading events with minimal downtime.",
        "mystery_complexity": "0 nothing to figure out; 3 engaging puzzle with planted clues and satisfying reveal; 5 intricate central puzzle whose reveals recontextualise earlier scenes.",
        "conflict_density": "0 few collisions of goals or values; 3 steady conflict across acts and threads; 5 near-constant escalating conflict where choices always cost something.",
        "cliffhanger_frequency": "0 scenes resolve cleanly; 3 common hooks at sequence ends; 5 almost every scene ends on unresolved stakes.",
    },
    "thematic_moral": {
        "romantic_content": "0 none; 3 significant subplot shaping choices; 5 core arc, resolution hinges on the relationship's fate.",
        "sexual_content": "0 none; 2 suggestive, fade to black; 3 implied intimacy influencing stakes; 4 non-explicit depiction on the page; 5 explicit and central enough to shape tone and outcomes.",
        "violence_level": "0 none beyond talk; 3 realistic moderate violence with visible impact; 5 extreme or disturbing violence central to tone and theme.",
        "moral_ambiguity": "0 moral lines clear; 3 balanced ambiguity, compelling cases coexist; 5 pervasive greyness, values irreconcilably clash.",
        "philosophical_depth": "0 no engagement with big ideas; 3 regular inquiry steering choices; 5 deep sustained exploration shaping structure and meaning.",
    },
    "character_relationships": {
        "character_complexity": "0 flat types with single traits; 3 multi-dimensional leads with agency and costs; 5 exceptional realism, motivations evolve under pressure.",
        "transformation_arc": "0 no change in belief or behaviour; 3 clear growth redirecting goals; 5 profound change reframing identity and theme.",
        "relationship_centrality": "0 incidental colour; 3 regularly plot-relevant and choice-shaping; 5 the primary engine of plot and meaning.",
        "diversity_representation": "0 monoculture; 3 moderate diversity in meaningful roles; 5 highly inclusive, identities central and nuanced.",
        "empathy_elicitation": "0 detachment; 3 regular engagement, the reader feels with the cast; 5 deep visceral empathy heightening every turn.",
    },
    "structural_style": {
        "narrative_complexity": "0 simple linear single thread; 3 multiple intertwined plots handled clearly; 5 highly layered yet coherent, structure amplifies meaning.",
        "worldbuilding_detail": "0 bare-bones and generic; 3 moderate detail with consistent consequences; 5 encyclopedic depth, setting behaves like a character.",
        "humor_presence": "0 no intentional humour; 3 regular comedic beats shaping rhythm; 5 humour a major engine of engagement.",
        "symbolism_allegory": "0 none beyond literal action; 3 recurring symbols guiding interpretation; 5 dense layered allegory, images evolve and carry argument.",
    },
}

DIMENSIONS: dict[str, str] = {k: v for g in DIMENSION_GROUPS.values() for k, v in g.items()}

AGE_RATINGS = {
    "G": "All ages. No violence or sex; very mild peril; clean language; conflicts resolve safely.",
    "PG": "Mild peril or themes; very mild language; discreet affection; intense moments brief and bounded.",
    "PG-13": "Moderate violence; brief non-graphic sexual content; stronger language; higher thematic intensity without explicit detail.",
    "R": "Strong violence or language; sexual content or nudity; drug use; mature themes with sustained intensity.",
    "NC-17": "Explicit sexual content or extreme sustained graphic violence; unsuitable for minors.",
}


# --------------------------------------------------------------------------
# Schema
# --------------------------------------------------------------------------

_SCORE = {"type": "integer", "minimum": 0, "maximum": 5}

_ENTRY = {
    "type": "object", "additionalProperties": False,
    "required": ["score"],
    "properties": {
        "score": _SCORE,
        "evidence": {"type": "string",
                     "description": "≤25 words naming the concrete thing in THIS story that "
                                    "justifies the score. Required for any score ≥1."},
    },
}

PLOT_EMBEDDING_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["genres", "dimensions", "age_rating", "dominant"],
    "description": (
        "The plot embedding: a fixed interpretable coordinate system, identical across "
        "every work in the corpus. Every genre and dimension scored 0-5 on the shared "
        "scale. Scores of 0 need no evidence; every score ≥1 must name what in this "
        "story justifies it."
    ),
    "properties": {
        "genres": {
            "type": "object", "additionalProperties": False,
            "required": sorted(GENRES),
            "properties": {k: _ENTRY for k in sorted(GENRES)},
        },
        "dimensions": {
            "type": "object", "additionalProperties": False,
            "required": sorted(DIMENSIONS),
            "properties": {k: _ENTRY for k in sorted(DIMENSIONS)},
        },
        "age_rating": {"enum": list(AGE_RATINGS)},
        "dominant": {
            "type": "array", "minItems": 1, "maxItems": 5,
            "description": "The genre keys scoring 4 or 5, strongest first. These are what the "
                           "work IS; everything else is seasoning.",
            "items": {"type": "string"},
        },
    },
}


def rubric_text(compact: bool = False) -> str:
    """The rubric handed to the model. Never abbreviate the anchors."""
    lines = [
        "PLOT EMBEDDING — score EVERY key below on this scale:",
        "",
    ]
    lines += [f"  {n} = {t}" for n, t in SCALE.items()]
    lines += [
        "",
        "The distinction that matters is PRESENCE versus STRUCTURAL CONSEQUENCE.",
        "A single chase that changes nothing is 1, not 3. Several set pieces that shape",
        "turns across acts is 3. Only 'remove it and the story's identity collapses' is 5.",
        "Most keys in most works are 0. A work that scores 3+ on twenty genres has been",
        "scored by someone avoiding commitment — be decisive and score honestly low.",
        "Any score ≥1 needs `evidence`: ≤25 words naming the concrete thing in THIS story.",
        "",
        "A) GENRES (52)",
    ]
    for group, members in GENRE_GROUPS.items():
        lines.append(f"  [{group}]")
        for k, d in members.items():
            lines.append(f"    {k}: {d}" if not compact else f"    {k}")
    lines += ["", "B) NON-GENRE DIMENSIONS (24)"]
    for group, members in DIMENSION_GROUPS.items():
        lines.append(f"  [{group}]")
        for k, d in members.items():
            lines.append(f"    {k}: {d}" if not compact else f"    {k}")
    lines += ["", "C) AGE RATING (choose exactly one)"]
    lines += [f"    {k}: {v}" for k, v in AGE_RATINGS.items()]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Analysis helpers
# --------------------------------------------------------------------------

def vector(embedding: dict) -> list[int]:
    """Flatten to a fixed-length numeric vector: 52 genres + 24 dimensions."""
    g = embedding.get("genres", {})
    d = embedding.get("dimensions", {})
    return ([g.get(k, {}).get("score", 0) for k in sorted(GENRES)] +
            [d.get(k, {}).get("score", 0) for k in sorted(DIMENSIONS)])


def profile(embedding: dict, threshold: int = 3) -> dict:
    """Human-readable summary: what actually scores."""
    g = embedding.get("genres", {})
    d = embedding.get("dimensions", {})
    hot_g = sorted(((k, v.get("score", 0)) for k, v in g.items() if v.get("score", 0) >= threshold),
                   key=lambda x: -x[1])
    hot_d = sorted(((k, v.get("score", 0)) for k, v in d.items() if v.get("score", 0) >= threshold),
                   key=lambda x: -x[1])
    return {
        "dominant_genres": hot_g,
        "salient_dimensions": hot_d,
        "age_rating": embedding.get("age_rating"),
        "genre_mass": sum(v.get("score", 0) for v in g.values()),
        "nonzero_genres": sum(1 for v in g.values() if v.get("score", 0) > 0),
    }


def normalize_embedding(embedding: dict) -> list[str]:
    """Repair the parts that are mechanically derivable, return what was fixed.

    `dominant` is a projection of the genre scores, not an independent judgement,
    and models get it wrong reliably — they list a thematically salient genre
    that scored 3, or forget one that scored 4. Deriving it removes a whole class
    of validation noise without touching anything the model actually decided.
    """
    fixed: list[str] = []
    genres = embedding.get("genres", {})
    want = sorted((k for k, v in genres.items() if v.get("score", 0) >= 4),
                  key=lambda k: (-genres[k].get("score", 0), k))
    if embedding.get("dominant") != want:
        fixed.append(f"dominant: {embedding.get('dominant')} -> {want}")
        embedding["dominant"] = want
    return fixed


def validate_embedding(embedding: dict) -> list[str]:
    """Checks the rubric cannot enforce on its own."""
    errors: list[str] = []
    g = embedding.get("genres", {})
    d = embedding.get("dimensions", {})

    for name, block, ref in (("genres", g, GENRES), ("dimensions", d, DIMENSIONS)):
        missing = sorted(set(ref) - set(block))
        if missing:
            errors.append(f"{name}: {len(missing)} key(s) not scored, e.g. {missing[:5]}")
        for k, v in block.items():
            if k not in ref:
                errors.append(f"{name}.{k}: not a key of the schema")
                continue
            s = v.get("score")
            if not isinstance(s, int) or not 0 <= s <= 5:
                errors.append(f"{name}.{k}: score {s!r} outside 0-5")
            elif s >= 1 and not (v.get("evidence") or "").strip():
                errors.append(f"{name}.{k}: scored {s} with no evidence")

    dominant = embedding.get("dominant") or []
    strong = {k for k, v in g.items() if v.get("score", 0) >= 4}
    for k in dominant:
        if k not in GENRES:
            errors.append(f"dominant: {k!r} is not a genre key")
        elif k not in strong:
            errors.append(f"dominant: {k!r} listed but scores below 4")
    for k in sorted(strong - set(dominant)):
        errors.append(f"dominant: {k!r} scores ≥4 but is not listed")

    if embedding.get("age_rating") not in AGE_RATINGS:
        errors.append(f"age_rating {embedding.get('age_rating')!r} is not one of {list(AGE_RATINGS)}")

    # A work that is "strong" in fifteen genres has not been scored, it has been hedged.
    if len(strong) > 6:
        errors.append(f"{len(strong)} genres score ≥4 — the embedding is hedging, not scoring")
    return errors
