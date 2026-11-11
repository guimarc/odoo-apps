# -*- coding: utf-8 -*-
from odoo.addons.ai_knowledge.hooks import set_all_articles_full_width


def migrate(cr, version):
    """On update: existing articles become Full Width."""
    set_all_articles_full_width(cr)
