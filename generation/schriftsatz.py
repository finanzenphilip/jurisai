"""Schriftsatz (legal brief) generator based on research results."""
from __future__ import annotations

import logging

from generation.claude_client import generate

logger = logging.getLogger(__name__)

SCHRIFTSATZ_PROMPT = """Du bist ein erfahrener österreichischer Rechtsanwalt.
Erstelle basierend auf der folgenden Rechtsrecherche einen formellen Schriftsatz-Entwurf.

RECHTSRECHERCHE:
{research}

AUFGABE:
Erstelle einen professionellen Schriftsatz (Stellungnahme/Einspruch) mit:

1. KOPF: An [Gericht], GZ [Aktenzeichen], Datum
2. BETREFF: Kurze Bezeichnung
3. SACHVERHALT: Darstellung des Sachverhalts
4. RECHTLICHE BEURTEILUNG: Juristische Argumentation mit Zitaten der Rechtsprechung
5. ANTRAG: Konkreter Antrag

WICHTIG:
- Formatiere formal und korrekt nach österreichischem Verfahrensrecht
- Verwende korrekte juristische Sprache und Terminologie
- Lasse Platzhalter [___] für unbekannte Details (Namen, Daten, Aktenzeichen)
- Zitiere NUR Entscheidungen, die in der Rechtsrecherche tatsächlich vorkommen
- Erfinde KEINE Geschäftszahlen oder Urteile
- Markiere Stellen, die vom Anwalt geprüft werden müssen, mit [PRÜFEN]
"""


def generate_schriftsatz(research_text: str) -> str:
    """Generate a formal Austrian legal brief (Schriftsatz) from research text.

    Args:
        research_text: The research/answer text to base the brief on.

    Returns:
        Formatted legal brief as a string.
    """
    from config import CLAUDE_MAX_TOKENS

    logger.info("Generating Schriftsatz from research text (%d chars)", len(research_text))
    try:
        result = generate(
            user_prompt=SCHRIFTSATZ_PROMPT.format(research=research_text),
            system_prompt="Du bist ein erfahrener österreichischer Rechtsanwalt. Erstelle formelle, korrekte Schriftsätze. Erfinde NIEMALS Geschäftszahlen oder Urteile.",
            max_tokens=CLAUDE_MAX_TOKENS,
        )
        logger.info("Schriftsatz generated: %d chars", len(result))
        return result
    except Exception as e:
        logger.error("Failed to generate Schriftsatz: %s", e)
        raise
