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
        var div = document.createElement('div');
        this.appendChild(div);
        for(var i=0; i<this.tabNames.length; i++) {
            var tabBtn = document.createElement('input');
            tabBtn.setAttribute('type', 'button');
            tabBtn.setAttribute('value', this.tabNames[i]);
            tabBtn.onclick = this.tabClicked.bind(this, i);
            div.appendChild(tabBtn);
        }
        this.tabClicked(0);
    }
    tabClicked(tab) {
        for(var i=0; i<this.tabNames.length; i++) {
            this.show(i, i == tab);
        }
    }
    show(tab, s) {
        var showString = "none";
        if(s) {
            showString = "block";
        }
        var style = "display: " + showString;
        this.children[tab].setAttribute('style', style);
    }
}

customElements.define('msgtools-tabs', MsgTabs);
