function createChildElement(parent, childName) {
    child = document.createElement(childName)
    parent.appendChild(child)
    return child
}

/*
 * Creates a widget based on definition of a message.
 */
class MsgElement extends HTMLElement {
    constructor() {
        super();
        this.msgName = this.getAttribute('msgName');
        this.showHeader = this.hasAttribute('showHeader') ? this.getAttribute('showHeader').toLowerCase() === 'true' : true;
        this.showMsgName = this.hasAttribute('showMsgName') ? this.getAttribute('showMsgName').toLowerCase() === 'true' : false;
        this.shadow = this.attachShadow({mode: 'open'});
        msgtools.DelayedInit.add(this);
    }
    init() {
        this.msgClass = msgtools.findMessageByName(this.msgName);
        
        var fieldNames;
        if(this.hasAttribute('fields')) {
            fieldNames = this.getAttribute('fields').split(",");
        } else {
            fieldNames = [];
        }

        // list of Field Info objects from auto-generated JavaScript code.
        this.fieldInfos = [];
        if(fieldNames.length === 0) {
            for(var i=0; i<this.msgClass.prototype.fields.length; i++) {
                var fi = this.msgClass.prototype.fields[i];
                this.fieldInfos.push(fi);
                fieldNames.push(fi.name);
            }
        } else {
            for(var i=0; i<fieldNames.length; i++) {
                fi = msgtools.findFieldInfo(this.msgClass, fieldNames[i]);
                this.fieldInfos.push(fi);
            }
        }
        this.fieldNames = fieldNames;

        // list with a HTML element for each field
        this.fields = [];

        // a table that holds everything else
        this.table = createChildElement(this.shadow, 'table');
        if(this.hasAttribute('border')) {
            this.table.setAttribute('border', this.getAttribute('border'));
        } else {
            //TODO default border for table
            //this.table.setAttribute('border', 1);
        }
        this.createFields();
    }
}

/*
 * Displays field values for a message. 
 */
class MsgLabels extends MsgElement {
    constructor() {
        super();

        // used for coloring display according to age.
        if(this.hasAttribute('maxAge')) {
            this.maxAge = parseFloat(this.getAttribute('maxAge'));
        } else {
            this.maxAge = -1;
        }
        // time of last reception
        this.rxTime = 0;
    }
    init() {
        super.init();

        // Register to receive our messages so we can display fields.
        msgtools.MessageClient.dispatch.register(this.msgClass.prototype.MSG_ID, this.processMsg.bind(this));
    }
    processMsg(msg) {
        for(var i=0; i<this.fieldInfos.length; i++) {
            var fieldInfo = this.fieldInfos[i];
            var value = msg[fieldInfo.get]();
            this.fields[i].textContent = value;
            var color = 'black'
            if(fieldInfo.type === "enumeration") {
                let int_value = msg[fieldInfo.get](true);
                // if value was the same as int_value, then it didn't get decoded,
                // which should count as a red value
                if(int_value === value) {
                    color = 'red';
                }
                value = int_value;
            }
            if(value < fieldInfo.minVal || value > fieldInfo.maxVal) {
                color = 'red';
            }
            //TODO Need a way to check yellow limits
            else if (value < fieldInfo.minVal || value > fieldInfo.maxVal) {
                color = 'yellow';
            }
            this.fields[i].setAttribute('style', 'color: '+color);
        }
        if(this.maxAge>0) {
            timer.start(this.maxAge, this.rxTimeout.bind(this));
        }
    }
    rxTimeout() {
        if(now > this.rxTime + this.maxAge()) {
            for(var i=0; i<this.fieldInfos.length; i++) {
                this.fields[i].setAttribute('style', 'color: purple');
            }
        }
    }
}

/*
 * Displays as row
 */
class MsgLabelsRow extends MsgLabels {
    createFields() {
        if(this.showMsgName) {
            var tr = createChildElement(this.table, 'tr');
            var td = createChildElement(tr, 'td');
            td.setAttribute('colspan', this.fieldInfos.length);
            td.textContent = this.msgName;
        }
        if(this.showHeader) {
            var tr = createChildElement(this.table, 'tr');
            for(var i=0; i<this.fieldNames.length; i++) {
                var td = createChildElement(tr, 'td');
                td.textContent = this.fieldNames[i];
            }
        }
        var tr = createChildElement(this.table, 'tr');
        for(var i=0; i<this.fieldInfos.length; i++) {
            var td = createChildElement(tr, 'td');
            td.textContent = '?';
            this.fields.push(td);
        }
    }
}

/*
 * Displays as column.
 */
class MsgLabelsColumn extends MsgLabels {
    createFields() {
        if(this.showMsgName) {
            var tr = createChildElement(this.table, 'tr');
            var td = createChildElement(tr, 'td');
            td.setAttribute('colspan', '2');
            td.textContent = this.msgName;
        }
        for(var i=0; i<this.fieldInfos.length; i++) {
            var tr = createChildElement(this.table, 'tr');
            if(this.showHeader) {
                var td = createChildElement(tr, 'td');
                td.textContent = this.fieldNames[i];
            }
            var td = createChildElement(tr, 'td');
            td.textContent = '?';
            this.fields.push(td);
        }
    }
}

/*
 * Edit field values for a message. 
 */
class MsgEdit extends MsgElement {
    constructor() {
        super();
    }
    init() {
        super.init();
    }
    sendClicked() {
        var msg = new this.msgClass();
        for(var i=0; i<this.fieldInfos.length; i++) {
            var fieldInfo = this.fieldInfos[i];
            var value = this.fields[i].value;
            msg[fieldInfo.set](value);
        }
        //console.log("MsgEdit.Send: "+msgtools.toJSON(msg));
        msgtools.client.sendMessage(msg);
    }
    editWidget(fieldInfo) {
        var w;
        if(fieldInfo.type === "enumeration") {
            // make a dropdown list for enums
            w = document.createElement('select');
            let lookup = fieldInfo.enumLookup[0]; // forward lookup is #0
            for(var name in lookup) {
                var value = lookup[name];
                var option = createChildElement(w, 'option');
                option.setAttribute('value', value);
                option.textContent = name;
            }
        } else {
            // make a text edit for anything else
            w = document.createElement('input');
            w.setAttribute('type', 'text');
        }
        return w;
    }
    sendButton() {
        var sendBtn = document.createElement('input');
        sendBtn.setAttribute('type', 'button');
        sendBtn.setAttribute('value', 'Send');
        sendBtn.onclick = this.sendClicked.bind(this);
        sendBtn.setAttribute('style', 'width: 100%');
        return sendBtn;
    }
}

/*
 * Edit field values for a message in a row.
 */
class MsgEditRow extends MsgEdit {
    createFields() {
        if(this.showMsgName) {
            var tr = createChildElement(this.table, 'tr');
            var td = createChildElement(tr, 'td');
            td.setAttribute('colspan', this.fieldInfos.length);
            td.textContent = this.msgName;
        }
        if(this.showHeader) {
            var tr = createChildElement(this.table, 'tr');
            for(var i=0; i<this.fieldNames.length; i++) {
                var td = createChildElement(tr, 'td');
                td.textContent = this.fieldNames[i];
            }
        }
        var tr = createChildElement(this.table, 'tr');
        for(var i=0; i<this.fieldInfos.length; i++) {
            var fieldInfo = this.fieldInfos[i];
            var td = createChildElement(tr, 'td');
            var editWidget = this.editWidget(fieldInfo);
            this.fields.push(editWidget);
            td.appendChild(editWidget);
        }
        var tr = createChildElement(this.table, 'tr');
        var td = createChildElement(tr, 'td');
        td.setAttribute('colspan', this.fieldInfos.length);
        td.appendChild(this.sendButton());
    }
}

/*
 * Edit field values for a message in a column.
 */
class MsgEditColumn extends MsgEdit {
    createFields() {
        if(this.showMsgName) {
            var tr = createChildElement(this.table, 'tr');
            var td = createChildElement(tr, 'td');
            td.setAttribute('colspan', '2');
            td.textContent = this.msgName;
        }
        for(var i=0; i<this.fieldInfos.length; i++) {
            var fieldInfo = this.fieldInfos[i];
            var tr = createChildElement(this.table, 'tr');
            if(this.showHeader) {
                var td = createChildElement(tr, 'td');
                td.textContent = this.fieldNames[i];
            }
            var td = createChildElement(tr, 'td');
            var editWidget = this.editWidget(fieldInfo);
            this.fields.push(editWidget);
            td.appendChild(editWidget);
        }
        var tr = createChildElement(this.table, 'tr');
        var td = createChildElement(tr, 'td');
        td.setAttribute('colspan', '2');
        td.appendChild(this.sendButton());
    }
}


// This should be run after we're confident that all of the uses of the
// tag have been defined, so that our calls to getAttribute will succeed.
// (Also after any remaining dependencies are loaded.)
// Best plan is just to import this whole file at the end of your HTML.
customElements.define('msgtools-msglabelsrow', MsgLabelsRow);
customElements.define('msgtools-msglabelscolumn', MsgLabelsColumn);
customElements.define('msgtools-msgeditrow', MsgEditRow);
customElements.define('msgtools-msgeditcolumn', MsgEditColumn);
