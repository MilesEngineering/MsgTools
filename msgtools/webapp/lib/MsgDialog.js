/*
 * A dialog box with a close button.
 */
class MsgDialog extends HTMLElement {
    constructor() {
        super();

        var closeBtn = document.createElement('input');
        closeBtn.setAttribute('type', 'button');
        closeBtn.setAttribute('value', 'Close');
        closeBtn.onclick = this.closeClicked.bind(this);
        closeBtn.setAttribute('style', 'width: 100%');
        
        this.appendChild(closeBtn);

        // only add style settings if they're not already specified.
        function appendStyle(style, attr, val) {
            //TODO How to tell if one string is in another in JS?
            /*var contains = attr in style;
            console.log("contains: " + contains);
            if (contains) {
                console.log("style has " + attr);
                return style;
            }*/
            return style + attr + ": " + val + ";";
        }
        var style = "";
        style = appendStyle(style, 'position', 'fixed');
        style = appendStyle(style, 'top', '25%');
        style = appendStyle(style, 'left', '40%');
        style = appendStyle(style, 'right', 'auto');
        style = appendStyle(style, 'margin', 'auto');
        style = appendStyle(style, 'background-color', '#fff');
        style = appendStyle(style, 'border', '5px solid grey');
        //TODO Once appendStyle checks for properties existing, this needs to move
        //     before all the appendStyle calls.
        if(this.hasAttribute("style")) {
            style += this.getAttribute("style") + ";";
        }
        this.baseStyle = style;
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

customElements.define('msgtools-dialog', MsgDialog);
