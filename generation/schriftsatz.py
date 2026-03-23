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

Formatiere formal und korrekt nach österreichischem Verfahrensrecht.
Verwende korrekte juristische Sprache.
Lasse Platzhalter [___] für unbekannte Details (Namen, Daten, Aktenzeichen).
"""


def generate_schriftsatz(research_text: str) -> str:
    """Generate a formal Austrian legal brief (Schriftsatz) from research text.

    Args:
        research_text: The research/answer text to base the brief on.

    Returns:
        Formatted legal brief as a string.
    """
    logger.info("Generating Schriftsatz from research text (%d chars)", len(research_text))
    try:
        result = generate(
            user_prompt=SCHRIFTSATZ_PROMPT.format(research=research_text),
            system_prompt="Du bist ein österreichischer Rechtsanwalt. Erstelle formelle Schriftsätze.",
            max_tokens=4096,
        )
        logger.info("Schriftsatz generated: %d chars", len(result))
        return result
    except Exception as e:
        logger.error("Failed to generate Schriftsatz: %s", e)
        raise
