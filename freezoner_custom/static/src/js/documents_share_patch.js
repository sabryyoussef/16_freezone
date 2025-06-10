///** @odoo-module **/
//
//import { patch } from "@web/core/utils/patch";
//import { useService } from "@web/core/utils/hooks";
//import { DocumentsController } from "@documents/views/documents_controller";  // Correct import
//
//console.log("Module loaded: Share fullscreen patch");  // Debug log
//
//patch(DocumentsController.prototype, "documents_share_fullscreen_patch", {
//    setup() {
//        this._super.apply(this, arguments);
//        this.orm = useService("orm");
//        this.action = useService("action");
//    },
//
//    async onClickShareDomain() {
//        console.log("Share button clicked");  // Debug log
//        const act = await this.orm.call("documents.share", "open_share_popup", [
//            {
//                domain: this.env.searchModel.domain,
//                folder_id: this.env.searchModel.getSelectedFolderId(),
//                tag_ids: [this.env.model.x2ManyCommands.replaceWith(
//                    this.env.searchModel.getSelectedTagIds()
//                )],
//                type: this.env.model.root.selection.length ? "ids" : "domain",
//                document_ids: this.env.model.root.selection.length
//                    ? [[6, 0, await this.env.model.root.getResIds(true)]]
//                    : false,
//            },
//        ]);
//        this.action.doAction(act);
//    },
//});