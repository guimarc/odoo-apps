/** @odoo-module */

import { registry } from '@web/core/registry';
import { formView } from '@web/views/form/form_view';
import { FormController } from '@web/views/form/form_controller';
import {patch} from "@web/core/utils/patch";

patch(FormController.prototype,{
    setup() {
         this.canEnableEdit = false;
         super.setup(...arguments);
    },

    async edit_btn() {
      console.log('edit_button');
      this.canEnableEdit = 'true';
      this.updateURL();
    },

    async save(params) {
        const record = this.model.root;
        let saved = false;
        if (this.props.saveRecord) {
            saved = await this.props.saveRecord(record, params);
        } else {
            saved = await record.save(params);
        }
        if (saved && this.props.onSave) {
            this.props.onSave(record, params);
        }
        this.save
        this.props.mode = 'readonly';
        return saved;
    },

    updateURL() {
    console.log('updateURL edit btn');
         if (this.canEnableEdit) {
             this.model.root.config.mode = 'edit';

        }
        else {
            this.model.root.config.mode = 'readonly';
        }
        if (this.props.mode == 'readonly') {
             this.model.root.config.mode = 'readonly';

        }


        this.router.pushState({ id: this.model.root.resId, mode:"readonly"});
    }

})
