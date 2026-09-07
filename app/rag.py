from dataclasses import dataclass


@dataclass(frozen=True)
class RegulationChunk:
    title: str
    citation: str
    text: str
    keywords: tuple[str, ...]


REGULATION_INDEX: tuple[RegulationChunk, ...] = (
    RegulationChunk(
        title="Plastic Waste Management Rules",
        citation="Plastic Waste Management Rules, 2016, Rule 9",
        text="Producers, importers, and brand owners must establish extended producer responsibility for plastic packaging.",
        keywords=("plastic", "packaging", "epr", "producer"),
    ),
    RegulationChunk(
        title="E-Waste Management Rules",
        citation="E-Waste Management Rules, 2022, Rule 11",
        text="Producers must meet extended producer responsibility targets through registered recyclers and maintain records.",
        keywords=("e-waste", "electronic", "recycler", "epr"),
    ),
    RegulationChunk(
        title="Solid Waste Management Rules",
        citation="Solid Waste Management Rules, 2016, Rule 4",
        text="Waste generators must segregate waste into biodegradable, non-biodegradable, and domestic hazardous streams.",
        keywords=("segregation", "organic", "biodegradable", "municipal"),
    ),
)


def query_regulations(query: str) -> list[RegulationChunk]:
    terms = {term.lower() for term in query.split() if len(term) > 2}
    ranked = sorted(
        REGULATION_INDEX,
        key=lambda chunk: len(terms.intersection(chunk.keywords)),
        reverse=True,
    )
    return [chunk for chunk in ranked if terms.intersection(chunk.keywords)][:3]
