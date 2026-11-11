/** @odoo-module */

import config from "web.config";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { FormRenderer } from '@web/views/form/form_renderer';
import { KnowledgeCoverDialog } from '@knowledge/components/cover_selector/knowledge_cover_dialog';
import KnowledgeTreePanelMixin from '@knowledge/js/tools/tree_panel_mixin';
import { patch } from "@web/core/utils/patch";
import MoveArticleDialog from "@knowledge/components/move_article_dialog/move_article_dialog";
import PermissionPanel from '@knowledge/components/permission_panel/permission_panel';
import { sprintf } from '@web/core/utils/strings';
import { useService } from "@web/core/utils/hooks";

const { onMounted, onPatched, onWillDestroy, useEffect, useRef, useState } = owl;

patch(FormRenderer.prototype, 'knowledge_doc_upload_ai', {

      async save() {
               await this.props.record.save()
           }
});

