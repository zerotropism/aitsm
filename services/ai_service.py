import json
import re

from sqlalchemy.orm import Session

from core.llm import invoke
from models.kb_article import KBArticle
from models.ticket import Ticket
from schemas.kb_article import KBSearchResult
from services.kb_service import search_kb


def triage_ticket(db: Session, ticket_id: str) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise ValueError(f"Ticket {ticket_id} not found")

    system = (
        "Tu es un agent ITSM expert. Analyse le ticket et retourne UNIQUEMENT un JSON "
        'sans texte autour : {"category": "<catégorie courte>", '
        '"priority": "low|medium|high|critical"}'
    )
    text = f"Titre: {ticket.title}\nDescription: {ticket.description}"

    raw = invoke(text, system_prompt=system)

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        data = json.loads(match.group())
        ticket.category = data.get("category", ticket.category)
        if data.get("priority") in ("low", "medium", "high", "critical"):
            ticket.priority = data["priority"]

    ticket.ai_triage_done = True
    db.commit()
    db.refresh(ticket)
    return ticket


def suggest_kb_articles(db: Session, ticket_id: str) -> list[KBSearchResult]:
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise ValueError(f"Ticket {ticket_id} not found")
    query = f"{ticket.title} {ticket.description}"
    return search_kb(db, query, n_results=3)


def draft_kb_article(db: Session, ticket_id: str, author_id: str) -> KBArticle:
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise ValueError(f"Ticket {ticket_id} not found")

    system = (
        "Tu es un rédacteur de base de connaissances ITSM. "
        "Rédige un article en Markdown structuré (titre H1, sections claires, "
        "étapes numérotées si besoin). Retourne uniquement le contenu Markdown."
        "Rédige l'article en français."
    )
    text = (
        f"Titre du ticket: {ticket.title}\n"
        f"Description: {ticket.description}\n"
        f"Résolution: {ticket.resolution or 'Non renseignée'}"
    )

    content = invoke(text, system_prompt=system)

    # Extract H1 title from content if any or fallback to ticket title
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ticket.title

    article = KBArticle(
        title=title,
        content=content,
        tags="[]",
        status="draft",
        author_id=author_id,
        source_ticket_id=ticket.id,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def deflect(db: Session, query: str) -> list[KBSearchResult]:
    return search_kb(db, query, n_results=5)


def suggest_reply(db: Session, ticket_id: str) -> str:
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise ValueError(f"Ticket {ticket_id} not found")

    # Contexte KB : articles les plus proches du ticket
    kb_results = search_kb(db, f"{ticket.title} {ticket.description}", n_results=3)
    kb_context = (
        "\n\n".join(f"Article : {r.article.title}\n{r.article.content[:500]}" for r in kb_results)
        if kb_results
        else "Aucun article KB pertinent trouvé."
    )

    system = (
        "Tu es un agent support ITSM. Rédige une réponse professionnelle, concise et bienveillante "
        "à envoyer au demandeur du ticket. Utilise les articles KB fournis si pertinents. "
        "Rédige en français. Retourne uniquement le texte de la réponse, sans introduction."
    )
    text = (
        f"Ticket : {ticket.title}\n"
        f"Description : {ticket.description}\n\n"
        f"Articles KB disponibles :\n{kb_context}"
    )

    return invoke(text, system_prompt=system)
