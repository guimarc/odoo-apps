/** @odoo-module **/
/**
 * Patches the Knowledge sidebar to add an "Upload Document" button above
 * "Browse Templates". Clicking it opens a small dialog where the user
 * picks a .docx/.xlsx file, optionally selects a parent Workspace article
 * from a dropdown, and submits.
 * The controller /knowledge/upload_docx converts it and creates the article.
 */

import { Component, useState, useRef, onWillStart } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { KnowledgeSidebar } from "@knowledge/components/sidebar/sidebar";
import { _t } from "@web/core/l10n/translation";

// ── Upload Dialog ─────────────────────────────────────────────────────────────

class DocxUploadDialog extends Component {
    static template = "knowledge_doc_upload_ai.DocxUploadDialog";
    static components = { Dialog };
    static props = {
        close: Function,
        onArticleCreated: { type: Function, optional: true },
    };

    setup() {
        this.notification = useService("notification");
        this.action = useService("action");
        this.orm = useService("orm");
        this.state = useState({
            parentId: "",
            workspaceArticles: [],
            fileName: "",
            uploading: false,
            error: "",
        });
        this.fileInput = useRef("fileInput");

        onWillStart(async () => {
            this.state.workspaceArticles = await this.loadWorkspaceArticles();
        });
    }

    /**
     * Root Workspaces (no parent) the user can write to, sorted by name.
     */
    async loadWorkspaceArticles() {
        const records = await this.orm.searchRead(
            "knowledge.article",
            [
                ["category", "=", "workspace"],
                ["parent_id", "=", false],
                ["is_article_item", "=", false],
                // Templates (Browse Templates) are stored as articles with no `name`
                ["is_template", "=", false],
                ["name", "!=", false],
                // Only articles where the user can actually create children
                ["user_has_write_access", "=", true],
            ],
            ["id", "name"]
        );
        return records
            .map((r) => ({ id: r.id, label: r.name }))
            .sort((a, b) => a.label.localeCompare(b.label));
    }

    onFileChange(ev) {
        const file = ev.target.files[0];
        this.state.fileName = file ? file.name : "";
        this.state.error = "";
    }

    async onSubmit() {
        const file = this.fileInput.el && this.fileInput.el.files[0];
        if (!file) {
            this.state.error = _t("Please select a .docx or .xlsx file.");
            return;
        }
        const name = file.name.toLowerCase();
        if (!name.endsWith(".docx") && !name.endsWith(".xlsx")) {
            this.state.error = _t("Only .docx and .xlsx files are supported.");
            return;
        }

        this.state.uploading = true;
        this.state.error = "";

        try {
            const formData = new FormData();
            formData.append("file", file);
            formData.append("parent_id", this.state.parentId);

            const resp = await fetch("/knowledge/upload_docx", {
                method: "POST",
                body: formData,
            });
            const data = await resp.json();

            if (data.success) {
                this.notification.add(
                    _t('Article "%s" created successfully!', data.title),
                    { type: "success" }
                );
                this.props.close();
                // Navigate to the new article
                this.action.doAction({
                    type: "ir.actions.act_window",
                    res_model: "knowledge.article",
                    res_id: data.article_id,
                    views: [[false, "form"]],
                    target: "current",
                });
                if (this.props.onArticleCreated) {
                    this.props.onArticleCreated(data.article_id);
                }
            } else {
                this.state.error = data.error || _t("Upload failed.");
            }
        } catch (err) {
            this.state.error = _t("Network error: ") + err.message;
        } finally {
            this.state.uploading = false;
        }
    }
}

// ── Sidebar Patch ─────────────────────────────────────────────────────────────

patch(KnowledgeSidebar.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialog = useService("dialog");
    },

    openDocxUploadDialog() {
        this.dialog.add(DocxUploadDialog, {
            onArticleCreated: (articleId) => {
                // Reload the sidebar article list to show the new article
                this.loadArticles();
            },
        });
    },
});

// Register the dialog component so its template is found
KnowledgeSidebar.components = {
    ...KnowledgeSidebar.components,
    DocxUploadDialog,
};
