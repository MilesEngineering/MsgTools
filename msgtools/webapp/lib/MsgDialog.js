/*
 * A dialog box with a close button.
 */
if (typeof MsgDialog !== "undefined") {
    console.log('MsgDialog already loaded')
} else {

class MsgDialog extends HTMLElement {
    constructor() {
        super();

        var closeBtn = document.createElement('input');
        closeBtn.setAttribute('type', 'button');
        closeBtn.setAttribute('value', 'Close');
        closeBtn.onclick = this.closeClicked.bind(this);
        closeBtn.setAttribute('style', 'width: 100%');
        
        this.appendChild(closeBtn);

        var inline_style = "";
        if(this.hasAttribute("style")) {
            inline_style += this.getAttribute("style") + ";";
        }
        var computed_style = getComputedStyle(this);
        inline_style = appendStyle(inline_style, computed_style, 'position', 'fixed');
        inline_style = appendStyle(inline_style, computed_style, 'top', '25%');
        inline_style = appendStyle(inline_style, computed_style, 'left', '40%');
        inline_style = appendStyle(inline_style, computed_style, 'background-color', '#fff');
        inline_style = appendStyle(inline_style, computed_style, 'border', '5px solid grey');
        this.baseStyle = inline_style;
        this.show(false);
    }
    show(s) {
        var showString = "none";
        if(s) {
            showString = "block";
        }
        var style = this.baseStyle + "display: " + showString;
        this.setAttribute('style', style);
    }
    closeClicked() {
        this.show(false);
    }
}
window.MsgDialog = MsgDialog;

customElements.define('msgtools-dialog', MsgDialog);

// only add style settings if they're not already specified as inline or computed style.
function appendStyle(style, computed_style, prop, val) {
    if (style.includes(prop)) {
        return style;
    }
    var computed_property = computed_style.getPropertyValue(prop);
    if (computed_property) {
        // do override if it's a default value when CSS is empty
        if (prop == 'position' && computed_property == 'static') {
        } else if ((prop == 'top' || prop == 'left') && computed_property == 'auto') {
        } else if (prop == 'border' && computed_property == "0px none rgb(0, 0, 0)") {
        } else if (prop == 'background-color' && computed_property == "rgba(0, 0, 0, 0)") {
        } else {
            console.log(`${prop} has CSS value ${computed_property}, not overriding`);
            return style;
        }
    }
    return style + prop + ": " + val + ";";
}
}
