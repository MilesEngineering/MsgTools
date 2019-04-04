/*
 * A container with a set of buttons, and when a button is clicked, only the
 * child at the same index as the button is shown, all others are hidden.
 * This resembles a tab widget in action, but without the borders and visualization
 * of the appropriate button being shaded to designate which tab is selected.
 */
class MsgTabs extends HTMLElement {
    constructor() {
        super();

        this.tabNames = this.getAttribute('tabNames').split(',');
        var computed_style = getComputedStyle(this);
        var baseStyle = 'border: 1px solid #ccc;';
        if(this.hasAttribute("style")) {
            baseStyle = this.getAttribute("style")+";";
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
