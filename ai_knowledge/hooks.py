# -*- coding: utf-8 -*-


def set_all_articles_full_width(cr):
    """Set every existing Knowledge article to Full Width."""
    cr.execute(
        "UPDATE knowledge_article SET full_width = TRUE WHERE full_width IS DISTINCT FROM TRUE"
    )


def post_init_hook(env):
    """On install: existing articles become Full Width."""
    set_all_articles_full_width(env.cr)
