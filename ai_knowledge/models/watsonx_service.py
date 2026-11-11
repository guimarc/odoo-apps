# -*- coding: utf-8 -*-
"""
Generic WatsonX text-generation service for AI Knowledge.

Credentials are read from the Odoo server configuration (odoo.conf):
    watson_id  = <WatsonX API key>
    project_id = <watsonx.ai project id>

Usage:
    text = self.env['ai.knowledge.watsonx'].generate(prompt, max_new_tokens=500)
"""

import logging
import re

from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools.config import config

_logger = logging.getLogger(__name__)

WATSONX_URL = "https://us-south.ml.cloud.ibm.com"
WATSONX_MODEL_ID = "meta-llama/llama-3-3-70b-instruct"

# Llama 3 chat template: the model ends its turn with <|eot_id|> instead of
# continuing to invent new "ANSWER ..." blocks.
_EOT = "<|eot_id|>"
_STOP_SEQUENCES = [_EOT, "ANSWER REWRITTEN", "\nQUESTION:", "\nARTICLES:"]
# Safety net: if the model still starts a new block, cut the text there.
_RUNAWAY_RE = re.compile(r"\n\s*(ANSWER[^\n]*:|QUESTION:|ARTICLES:)", re.IGNORECASE)


class AiKnowledgeWatsonx(models.AbstractModel):
    _name = 'ai.knowledge.watsonx'
    _description = 'AI Knowledge WatsonX Service'

    @api.model
    def _get_watson_model(self):
        """Initialize and return the WatsonX model."""
        # Imported lazily so the module can be installed without the SDK.
        try:
            from ibm_watsonx_ai import Credentials
            from ibm_watsonx_ai.foundation_models import ModelInference
        except ImportError as exc:
            raise UserError(
                "The 'ibm_watsonx_ai' Python package is not installed on the server."
            ) from exc

        watson_id = config.get("watson_id")
        project_id = config.get("project_id")
        if not watson_id or not project_id:
            raise UserError(
                "WatsonX is not configured: set 'watson_id' and 'project_id' in the Odoo configuration file."
            )

        creds = Credentials(url=WATSONX_URL, api_key=watson_id)
        return ModelInference(
            model_id=WATSONX_MODEL_ID,
            credentials=creds,
            project_id=project_id,
        )

    @api.model
    def generate(self, prompt, system=None, max_new_tokens=500, temperature=0.1,
                 stop_sequences=None):
        """Send ``prompt`` to WatsonX and return the generated text.

        ``system`` is an optional system instruction. The prompt is wrapped in the
        Llama 3 chat template so the model answers once and stops.
        """
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
        from ibm_watsonx_ai.foundation_models.utils.enums import DecodingMethods

        params = {
            GenParams.DECODING_METHOD: DecodingMethods.GREEDY,
            GenParams.MAX_NEW_TOKENS: max_new_tokens,
            GenParams.TEMPERATURE: temperature,
            GenParams.REPETITION_PENALTY: 1.1,
            GenParams.STOP_SEQUENCES: stop_sequences or _STOP_SEQUENCES,
        }

        chat_prompt = "<|begin_of_text|>"
        if system:
            chat_prompt += f"<|start_header_id|>system<|end_header_id|>\n\n{system}{_EOT}"
        chat_prompt += (
            f"<|start_header_id|>user<|end_header_id|>\n\n{prompt}{_EOT}"
            "<|start_header_id|>assistant<|end_header_id|>\n\n"
        )

        model = self._get_watson_model()
        response = model.generate_text(prompt=chat_prompt, params=params)
        return self._clean(response)

    @api.model
    def _clean(self, text):
        """Drop template tokens and any runaway continuation."""
        text = (text or "").replace(_EOT, "")
        text = _RUNAWAY_RE.split(text, maxsplit=1)[0]
        return text.strip()
