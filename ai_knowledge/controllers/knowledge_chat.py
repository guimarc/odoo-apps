# -*- coding: utf-8 -*-
"""
Internal Knowledge Chat search endpoint.

POST /knowledge/chat/search
  JSON body: { "query": "...", "limit": 5 }
  auth: user (internal Odoo session — no API key needed)

Returns:
  { "success": true, "answer": "...", "results": [...] }
"""

import html
import json
import logging
import re

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

STOP_WORDS = {
    "what", "is", "the", "a", "an", "of", "for", "to", "in", "on",
    "and", "or", "please", "show", "me", "do", "does", "how",
    "where", "when", "which", "who", "tell", "about", "give",
    "find", "search", "looking",
}


# ── text helpers ──────────────────────────────────────────────────────────────

def _html_to_text(value):
    if not value:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</div\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>", "\n• ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\r", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _normalize_terms(query):
    query = (query or "").strip().lower()
    raw = re.findall(r"[a-zA-Z0-9._/-]+", query)
    return list(dict.fromkeys(
        t for t in raw if len(t) > 1 and t not in STOP_WORDS
    ))


def _build_context(text, terms, size=1500):
    """Larger excerpt (around the first match) sent to WatsonX as context."""
    return _build_snippet(text, terms, size=size)


def _build_snippet(text, terms, size=400):
    if not text:
        return ""
    lower = text.lower()
    best = -1
    for t in terms:
        pos = lower.find(t.lower())
        if pos != -1 and (best == -1 or pos < best):
            best = pos
    if best == -1:
        return (text[:size] + "...") if len(text) > size else text
    start = max(0, best - 120)
    end = min(len(text), start + size)
    snippet = text[start:end].strip()
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet += "…"
    return snippet


def _score_article(query, terms, title, body_text):
    tl = (title or "").lower()
    bl = (body_text or "").lower()
    ql = (query or "").lower().strip()

    in_title = [t for t in terms if t in tl]
    in_body  = [t for t in terms if t in bl]
    matched  = sorted(set(in_title + in_body))
    if not matched:
        return None

    score = 0
    if ql and ql == tl:          score += 500
    elif ql and ql in tl:        score += 220
    if ql and ql in bl:          score += 120
    score += len(set(in_title)) * 55
    score += len(set(in_body))  * 18
    score += len(matched) * 30
    if terms and len(matched) == len(terms):
        score += 140
    if 80 <= len(body_text) <= 3000:
        score += 25
    if len(body_text) > 5000 and len(matched) <= 1:
        score -= 60
    for t in terms:
        score += min(bl.count(t), 5) * 4

    return {"score": score, "matched": matched}


# ── controller ────────────────────────────────────────────────────────────────

class KnowledgeChatController(http.Controller):

    @http.route(
        '/knowledge/chat/search',
        type='http',
        auth='user',  # pragma: allowlist secret
        methods=['POST'],
        csrf=False,
    )
    def chat_search(self, **kwargs):
        try:
            payload = request.httprequest.get_json(silent=True) or {}
        except Exception:
            payload = {}

        query = (payload.get('query') or '').strip()
        if not query:
            return _resp({'success': False, 'error': 'Empty query.'})

        try:
            limit = max(1, min(int(payload.get('limit', 5)), 10))
        except (TypeError, ValueError):
            limit = 5

        try:
            result = self._search(query, limit)
            return _resp(result)
        except Exception as exc:
            _logger.exception("Knowledge chat search failed")
            return _resp({'success': False, 'error': str(exc)})

    # ── search logic ──────────────────────────────────────────────────────

    def _search(self, query, limit):
        terms = _normalize_terms(query) or [query.lower()]
        env   = request.env
        Article = env['knowledge.article'].sudo()

        base_url = (
            env['ir.config_parameter'].sudo()
            .get_param('web.base.url', '')
            .rstrip('/')
        )

        # Build OR domain across title + body for query and each term
        domain = ['|', ('name', 'ilike', query), ('body', 'ilike', query)]
        for t in terms:
            domain = ['|'] + domain + ['|',
                ('name', 'ilike', t), ('body', 'ilike', t)]

        candidates = Article.search(domain, limit=200)
        _logger.info("Knowledge chat: query=%r terms=%r candidates=%d",
                     query, terms, len(candidates))

        scored = []
        for art in candidates:
            title     = (art.name or '').strip()
            body_text = _html_to_text(art.body or '')
            s         = _score_article(query, terms, title, body_text)
            if not s:
                continue
            matched = s['matched'] or terms
            scored.append({
                'id':      art.id,
                'title':   title,
                'snippet': _build_snippet(body_text, matched),
                'context': _build_context(body_text, matched),
                'url':     f"{base_url}/odoo/knowledge/{art.id}",
                'score':   s['score'],
            })

        scored.sort(key=lambda x: x['score'], reverse=True)
        results = scored[:limit]

        answer = ''
        if results:
            top = results[0]
            watson_text = self._ask_watsonx(query, results[:3])
            if watson_text:
                answer = f"{watson_text}\n\n[Open article]({top['url']})"
            else:
                # Fallback: plain snippet from the top result
                answer = (
                    f"**{top['title']}**\n\n"
                    f"{top['snippet']}\n\n"
                    f"[Open article]({top['url']})"
                )
            if len(results) > 1:
                answer += "\n\n*Other relevant articles:*\n"
                for r in results[1:4]:
                    answer += f"• [{r['title']}]({r['url']})\n"

        for r in results:
            r.pop('context', None)

        return {
            'success': True,
            'query':   query,
            'count':   len(results),
            'answer':  answer,
            'results': results,
        }

    def _ask_watsonx(self, query, articles):
        """Let WatsonX write the answer from the matched articles.

        Returns an empty string if WatsonX is unavailable so the caller can fall back.
        """
        sources = "\n\n".join(
            f"### {a['title']}\n{a['context']}"
            for a in articles
        )
        system = (
            "You are the Knowledge assistant. You help operators find "
            "process instructions quickly. Write ONE short, direct, well organised answer "
            "and then stop.\n"
            "Rules:\n"
            "- Use ONLY the reference material provided. Never invent steps or facts.\n"
            "- Start directly with the answer. No greetings, no 'Based on the articles', "
            "no closing offers such as 'let me know if I can help'.\n"
            "- When there are several steps or requirements, use a short bulleted list "
            "('• ') with one idea per line; otherwise use one or two short sentences.\n"
            "- Say each fact once. Never repeat or rewrite your answer.\n"
            "- Do not mention 'articles', article numbers or sources, and do not add links "
            "or notes; the interface shows them separately.\n"
            "- If the material does not answer the question, reply only: "
            "'I could not find this in the Knowledge articles.'"
        )
        prompt = f"REFERENCE MATERIAL:\n{sources}\n\nQUESTION: {query}"
        try:
            return request.env['ai.knowledge.watsonx'].generate(
                prompt, system=system, max_new_tokens=400, temperature=0.1,
            )
        except Exception:
            _logger.exception("Knowledge chat: WatsonX call failed, using snippet fallback")
            return ''


def _resp(data):
    return Response(
        json.dumps(data, ensure_ascii=False),
        content_type='application/json; charset=utf-8',
        status=200,
    )
