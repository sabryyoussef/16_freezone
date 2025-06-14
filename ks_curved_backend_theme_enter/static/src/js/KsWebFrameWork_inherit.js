/** @odoo-module **/

import { BlockUI } from "@web/core/ui/block_ui";

var { patch } = require("web.utils");
var session = require("web.session");
const { tags, xml } = owl;

// todo: Patch the remaining methods from the below commented code
patch(BlockUI.prototype, "o_blockUI", {
  setup() {
    /**
     * @override to add current loader information.
     */
    this._super();
    this.ks_loader = session["ks_current_loader"];
  },
});

/**
 * Update template for custom loaders.
 */

BlockUI.template = xml`
<div t-att-class="state.blockUI ? 'o_blockUI' : ''">
<t t-if="state.blockUI">
  <div class="o_spinner">
    <img t-if="ks_loader=='ks_loader_default'" src="/web/static/img/spin.png" alt="Loading..."/>
    
    <div t-if="ks_loader=='ks_loader_1'" t-att-class="ks_loader">
        <div class="spinner-border"></div>
    </div>
    
    <div t-if="ks_loader=='ks_loader_2'" t-att-class="ks_loader">
        <div class="round">
            <div class="rol"></div>
            <div class="rol"></div>
            <div class="rol"></div>
            <div class="rol"></div>
            <div class="dots">
                <div></div>
                <div></div>
                <div></div>
            </div>
        </div>
    </div>

    <div t-if="ks_loader=='ks_loader_3'" t-att-class="ks_loader">
        <div class="dots-move">
            <div class="dot-1"></div>
            <div class="dot-2"></div>
            <div class="dot-3"></div>
        </div>
    </div>

    <div t-if="ks_loader=='ks_loader_4'" t-att-class="ks_loader">
        <div class="babalas">
            <div class="babala-1"></div>
            <div class="babala-2"></div>
            <div class="babala-3"></div>
            <div class="babala-4"></div>
            <div class="babala-5"></div>
        </div>
    </div>

    <div t-if="ks_loader=='ks_loader_5'" t-att-class="ks_loader">
        <div class="two_dots">
            <div class="dot-1"></div>
            <div class="dot-2"></div>
        </div>
    </div>

    <div t-if="ks_loader=='ks_loader_6'" t-att-class="ks_loader">
        <div class="square_loader">
            <div class="square_loaderbar">
                <div class="dot-1"></div>
                <div class="dot-2"></div>
                <div class="dot-3"></div>
                <div class="dot-4"></div>
            </div>
        </div>
    </div>

    <div t-if="ks_loader=='ks_loader_7'" t-att-class="ks_loader">
        <section class="double-circle-loader">
            <div class="loader loader-6">
            <div class="loader-inner"></div>
            </div>
        </section>
    </div>

  </div>
  <div class="o_message mt-5">
      <t t-out="state.line1"/> <br/>
      <t t-out="state.line2"/>
  </div>
</t>
</div>`;
