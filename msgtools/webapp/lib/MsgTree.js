if (typeof MsgTree !== "undefined") {
    console.log('MsgTree already loaded')
} else {
function createChildElement(parent, childName) {
    child = document.createElement(childName);
    parent.appendChild(child);
    return child;
}

class MsgTree extends HTMLElement {
    constructor() {
        super();
        this.filter = this.hasAttribute('filter') ? this.getAttribute('filter') : '';
        this.shadow = this.attachShadow({mode: 'open'});
        msgtools.DelayedInit.add(this);
        this.handler = this.getAttribute('handler');
    }
    init() {
        let r = function(msgtree, domelem, filter, onclick, depth, displaydepth) {
            domelem = createChildElement(domelem, 'ul');
            // Don't attach onclick on the UL, only do it on the children LIs
            //domelem.onclick = onclick;
            domelem.setAttribute('style', 'cursor: pointer;');
            let style = 'display: none; cursor: pointer;'
            if(depth <= displaydepth) {
                style = 'display: list; cursor: pointer;';
            }
            for(const name of Object.keys(msgtree).sort()) {
                // skip the 'Network' messages, we don't need them.
                if(depth==0 && name == 'Network') {
                    continue;
                }
                let value=msgtree[name];
                if(value.prototype == undefined) {
                    let node = createChildElement(domelem, 'li');
                    node.onclick = onclick;
                    node.setAttribute('style', style);
                    node.textContent = name;
                    r(value, node, filter, onclick, depth+1, displaydepth);
                } else {
                    if(filter == '' || value.name.startsWith(filter)) {
                        let node = createChildElement(domelem, 'li');
                        node.setAttribute('style', style);
                        node.onclick = onclick;
                        node.textContent = value.name; //value.prototype.MsgName();
                        node.msgname = value.prototype.MsgName();
                    }
                }
            }
        };
        let displayDepth = this.hasAttribute('displayDepth') ? this.getAttribute('displayDepth') : 0;
        r(msgtools.msgs, this.shadow, this.filter, this.ontreeclick.bind(this), 0, displayDepth);
        this.msgBody = createChildElement(this.shadow, 'div');
    }
    ontreeclick(e) {
        e.stopPropagation();
        let node = e.target;
        if(node.msgname != undefined) {
            this.handleMsgClick(node.msgname);
        }
        
        let c = node.children;
        if(c[0] != undefined) {
            c = c[0].children;
        }
        for(let i=0; i<c.length; i++) {
            let child = c[i];
            if(child.hasAttribute("style") && !child.getAttribute("style").includes("display: none;")) {
                child.setAttribute("style", "display: none; cursor: pointer;");
            } else {
                child.setAttribute("style", "display: list; cursor: pointer;");
            }
        }
    }
    handleMsgClick(msgname) {
        //console.log('click on ' + msgname);
        let msgclass = msgtools.findMessageByName(msgname);
        //console.log(msgclass);
        if(this.handler != undefined) {
            let h = '<'+this.handler+" showMsgName=true msgName='"+msgname+"'></"+this.handler+'>';
            this.msgBody.innerHTML = h;
        }
    }
}

customElements.define('msgtools-msgtree', MsgTree);
}
