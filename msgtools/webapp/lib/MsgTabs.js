/*
 * A crude approximation of a tab widget:
 * A container with a row of buttons at the top. When a button is clicked, only the
 * child at the same index as the button is shown, all other children are hidden.
 */
if (typeof MsgTabs !== "undefined") {
    console.log('MsgTabs already loaded')
} else {

class MsgTabs extends HTMLElement {
    constructor() {
        super();

        this.tabNames = this.getAttribute('tabNames').split(',');
        //TODO This is a mess!  we want to specify border here, unless it was specified inline or
        //TODO in css.  It's hard to tell if it was specified in css, though, because it can just
        //TODO be a default
        var computed_style = getComputedStyle(this);
        var baseStyle = 'border: 1px solid #ccc;';
        if(this.hasAttribute("style")) {
            var inline_style = this.getAttribute("style");
            if(inline_style.replace(' ','').includes('border:')) {
                baseStyle = inline_style+";";
            } else {
                baseStyle = inline_style+";"+baseStyle;
            }
            var computed_style = getComputedStyle(this);
            var computed_property = computed_style.getPropertyValue('border');
            if(computed_property) {
                if(computed_property == "0px none rgb(0, 0, 0)"){
                }
            }
            // This is weird but if the MsgTabs has a style, the browsers adds stubby vertical lines
            // above and below it, and they look weird.  Clearing the style here but putting it on
            // the children makes it look ok.
            this.setAttribute('style', '');
        }
        this.tabButtons = [];
        var buttonContainer = document.createElement('div');
        buttonContainer.setAttribute('style', baseStyle);
        this.insertBefore(buttonContainer, this.firstChild);
        for(var tab=0; tab<this.tabNames.length; tab++) {
            var tabBtn = document.createElement('input');
            tabBtn.setAttribute('type', 'button');
            tabBtn.setAttribute('value', this.tabNames[tab]);
            tabBtn.onclick = this.tabClicked.bind(this, tab);
            buttonContainer.appendChild(tabBtn);
            this.tabButtons.push(tabBtn);
            var childNumber = tab+1;
            var div = this.children[childNumber];
            div.baseStyle = baseStyle + div.getAttribute('style');
        }
        this.tabButtonStyle =
            `background-color: inherit;
             border: none;
             outline: none;
             cursor: pointer;
             padding: 14px 16px;
             transition: 0.3s;`
        this.tabClicked(0);
    }
    tabClicked(tab) {
        for(var i=0; i<this.tabNames.length; i++) {
            this.show(i, i == tab);
        }
    }
    show(tab, s) {
        var showString = "none";
        var tabButtonStyle = this.tabButtonStyle;
        if(s) {
            showString = "block";
            tabButtonStyle += "background-color: #ccc;";
        } else {
        }
        var style = "; display: " + showString;
        var childNumber = tab+1;
        var child = this.children[childNumber];
        child.setAttribute('style', child.baseStyle + style);
        this.tabButtons[tab].setAttribute('style', tabButtonStyle);
    }
}

customElements.define('msgtools-tabs', MsgTabs);
}
