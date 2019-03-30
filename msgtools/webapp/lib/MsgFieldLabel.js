/*
 * Displays values of fields of messages, in rows or columns (or just one).
 */
 class MsgFieldLabel extends HTMLElement {
    constructor() {
        super();
        msgtools.DelayedInit.add(this);
    }
    init() {
        var msgName = this.getAttribute('msgName');
        this.msgClass = msgtools.findMessageByName(msgName);
        
        var fieldNames;
        if(this.hasAttribute('fields')) {
            fieldNames = this.getAttribute('fields').split(",");
        } else {
            fieldNames = [];
        }

        this.row = false;
        if(fieldNames.length > 1) {
            if(this.hasAttribute("row")) {
                row_attr = this.getAttribute("row");
                if(row_attr.toLowerCase() === 'true') {
                    this.row = true;
                } else {
                    console.log("row is " + row_attr);
                }
            }
        }
        
        if(this.hasAttribute('maxAge')) {
            this.maxAge = parseFloat(this.getAttribute('maxAge'));
        } else {
            this.maxAge = -1;
        }
        this.rxTime = 0;

        this.fieldInfos = [];
        if(fieldNames.length === 0) {
            for(var i=0; i<this.msgClass.prototype.fields.length; i++) {
                var fi = this.msgClass.prototype.fields[i];
                console.log(fi);
                this.fieldInfos.push(fi);
            }
        } else {
            for(var i=0; i<this.fieldInfos.length; i++) {
                fi = msgtools.findFieldInfo(this.msgClass, fieldNames[i]);
                this.fieldInfos.push(fi);
            }
        }
    
        // Register to receive our messages so we can display fields.
        msgtools.MessagingClient.dispatch.register(this.msgClass.prototype.MSG_ID, this.processMsg.bind(this));
    }

    processMsg(msg) {
        //TODO use this.row (boolean for row vs. column)
        for(var i=0; i<this.fieldInfos.length; i++) {
            var fieldInfo = this.fieldInfos[i];
            var value = msg[fieldInfo.get]();
            // TODO Check red and yellow limits
            console.log(fieldInfo.name + ": " + value);
        }
    }
    
    checkAging(now) {
        if(now > this.rxTime + this.maxAge()) {
            //TODO turn purple
        }
    }
}

// This should be run after we're confident that all of the uses of the
// tag have been defined, so that our calls to getAttribute will succeed.
// (Also after any remaining dependencies are loaded.)
// Best plan is just to import this whole file at the end of your HTML.
customElements.define('msgtools-msgfieldlabel', MsgFieldLabel);
