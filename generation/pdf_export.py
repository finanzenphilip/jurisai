"""Export chat messages as a printable HTML document."""
from __future__ import annotations

import html as html_module
from datetime import datetime


def generate_export_html(
    messages: list,
    title: str = "RIS Legal AI -- Rechtsrecherche",
) -> str:
    """Generate a printable HTML document from chat messages.

    Args:
        messages: List of message dicts with 'role' and 'content' keys,
                  optionally 'sources' and 'gesetz_sources'.
        title: Document title.

    Returns:
        Complete HTML string ready for download / printing.
    """
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    # Build message rows
    rows: list[str] = []
    for msg in messages:
        role = msg.get("role", "")
        content = html_module.escape(msg.get("content", ""))
        # Convert basic markdown bold **text** to <strong>
        import re
        content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
        # Convert newlines to <br>
        content = content.replace("\n", "<br>\n")

        if role == "user":
            role_label = "Frage"
            role_class = "user"
        else:
            role_label = "Antwort"
            role_class = "assistant"

        row = f"""
        <div class="message {role_class}">
            <div class="role-label">{role_label}</div>
            <div class="content">{content}</div>
        </div>"""

        # Append source references for assistant messages
        sources = msg.get("sources", [])
        gesetz_sources = msg.get("gesetz_sources", [])

        if sources or gesetz_sources:
            source_parts: list[str] = []
            if gesetz_sources:
                source_parts.append('<div class="sources-section"><strong>Gesetze:</strong><ul>')
                for g in gesetz_sources:
                    label = html_module.escape(
                        f"{g.get('kurztitel', '')} {g.get('paragraph', '')}"
                    )
                    url = g.get("url", "")
                    if url:
                        source_parts.append(f'<li><a href="{html_module.escape(url)}">{label}</a></li>')
                    else:
                        source_parts.append(f"<li>{label}</li>")
                source_parts.append("</ul></div>")

            if sources:
                source_parts.append('<div class="sources-section"><strong>Gerichtsentscheidungen:</strong><ul>')
                for s in sources:
                    gz = html_module.escape(s.get("geschaeftszahl", ""))
                    gericht = html_module.escape(s.get("gericht", ""))
                    datum = html_module.escape(s.get("datum", ""))
                    url = s.get("url", "")
                    if url:
                        source_parts.append(
                            f'<li>{gericht} <a href="{html_module.escape(url)}">{gz}</a> -- {datum}</li>'
                        )
                    else:
                        source_parts.append(f"<li>{gericht} {gz} -- {datum}</li>")
                source_parts.append("</ul></div>")

            row += "\n".join(source_parts)

        rows.append(row)

    messages_html = "\n".join(rows)

    html_doc = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html_module.escape(title)}</title>
<style>
    @media print {{
        body {{ margin: 20mm; }}
        .no-print {{ display: none; }}
    }}
    * {{ box-sizing: border-box; }}
    body {{
        font-family: "Georgia", "Times New Roman", serif;
        font-size: 12pt;
        line-height: 1.6;
        color: #1a1a1a;
        max-width: 800px;
        margin: 0 auto;
        padding: 40px 30px;
        background: #fff;
    }}
    .header {{
        border-bottom: 2px solid #1a1a1a;
        padding-bottom: 15px;
        margin-bottom: 30px;
    }}
    .header h1 {{
        font-size: 18pt;
        margin: 0 0 5px 0;
    }}
    .header .meta {{
        font-size: 10pt;
        color: #555;
    }}
    .message {{
        margin-bottom: 25px;
        padding: 15px 20px;
        border-left: 3px solid #ccc;
    }}
    .message.user {{
        border-left-color: #2563eb;
        background: #f8fafc;
    }}
    .message.assistant {{
        border-left-color: #059669;
        background: #f0fdf4;
    }}
    .role-label {{
        font-size: 9pt;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #666;
        margin-bottom: 8px;
    }}
    .content {{
        font-size: 11pt;
    }}
    .sources-section {{
        margin-top: 10px;
        padding: 10px 15px;
        background: #fafafa;
        border: 1px solid #e5e7eb;
        font-size: 10pt;
    }}
    .sources-section ul {{
        margin: 5px 0;
        padding-left: 20px;
    }}
    .sources-section li {{
        margin-bottom: 3px;
    }}
    a {{
        color: #2563eb;
        text-decoration: none;
    }}
    a:hover {{
        text-decoration: underline;
    }}
    .disclaimer {{
        margin-top: 40px;
        padding-top: 15px;
        border-top: 1px solid #ccc;
        font-size: 9pt;
        color: #888;
        text-align: center;
    }}
</style>
</head>
<body>
<div class="header">
    <h1>{html_module.escape(title)}</h1>
    <div class="meta">Exportiert am {now}</div>
</div>

{messages_html}

<div class="disclaimer">
    Diese Recherche dient der Information und ersetzt keine anwaltliche Beratung.
    Fuer konkrete Rechtsfaelle konsultieren Sie einen Rechtsanwalt.<br>
    Erstellt mit RIS Legal AI
</div>
</body>
</html>"""

    return html_doc
