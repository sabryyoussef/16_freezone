odoo.define('ks_curved_backend_theme_enter.KsZoomBtnVisibility', function (require) {
"use strict";

    window.onhashchange = function() {
        if ($(".o_content").length && document.querySelector(".o_content div:last-child")) {
            if ($(".ks-zoom-view").hasClass('d-none'))
                $(".ks-zoom-view").removeClass('d-none');

            document
                .querySelector(".o_content div:last-child")
                .removeAttribute("style");
                if (document.querySelector(".ks-zoom-per"))
                    document.querySelector(".ks-zoom-per").innerText = "100%";
        }
        else{
            if ($(".ks-zoom-view").length){
                $(".ks-zoom-view").addClass('d-none');
            }
        }
    }
});