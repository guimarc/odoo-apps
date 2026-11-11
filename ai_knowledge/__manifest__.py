# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "AI Knowledge",
    'summary': "DOCX and XLSX upload to Knowledge articles, with a WatsonX-powered Help Knowledge chat",
    'author': "Guilherme Marcondes",
    'license': "AGPL-3",
    'website': "https://github.com/guimarc/odoo-apps",
    'version': '18.0.1.0.1',
    'depends': ['knowledge'],
    'demo': [],
    'installable': True,
    'post_init_hook': 'post_init_hook',
    'assets': {
        'web.assets_backend': [
            # DOCX/XLSX upload
            'ai_knowledge/static/src/xml/docx_upload.xml',
            'ai_knowledge/static/src/js/docx_upload.js',
            # Knowledge AI Chat — SCSS first, then XML templates, then JS patch
            'ai_knowledge/static/src/scss/knowledge_chat.scss',
            'ai_knowledge/static/src/xml/knowledge_chat.xml',
            'ai_knowledge/static/src/js/knowledge_chat.js',
        ],
    },
}
