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
                this.fieldInfos.push(fi);
                fieldNames.push(fi.name);
            }
        } else {
            for(var i=0; i<this.fieldNames.length; i++) {
                fi = msgtools.findFieldInfo(this.msgClass, fieldNames[i]);
                this.fieldInfos.push(fi);
            }
        }
        
        this.fieldNames = fieldNames;

        this.fields = [];
        this.createFields();
    }
}

/*
 * Displays field values for a message. 
 */
class MsgLabels extends MsgElement {
    constructor() {
        super();
    }
    init() {
        super.init();

        // Register to receive our messages so we can display fields.
        msgtools.MessagingClient.dispatch.register(this.msgClass.prototype.MSG_ID, this.processMsg.bind(this));
    }
    processMsg(msg) {
        for(var i=0; i<this.fieldInfos.length; i++) {
            var fieldInfo = this.fieldInfos[i];
            var value = msg[fieldInfo.get]();
            this.fields[i].textContent = value;
            // TODO Check red and yellow limits
            //console.log(fieldInfo.name + ": " + value);
        }
    }
    checkAging(now) {
        if(now > this.rxTime + this.maxAge()) {
            //TODO turn purple
        }
    }
}

/*
 * Displays as row
 */
class MsgLabelsRow extends MsgLabels {
    createFields() {
        var table = document.createElement('table');
        table.setAttribute('border', 1);
        if(this.showMsgName) {
            var tr = document.createElement('tr');
            var td = document.createElement('td');
            td.textContent = this.msgName;
            td.setAttribute('colspan', this.fieldInfos.length);
            tr.appendChild(td);
            table.appendChild(tr);
        }
        if(this.showHeader) {
            var row = document.createElement('tr');
            for(var i=0; i<this.fieldNames.length; i++) {
                var td = document.createElement('td');
                td.textContent = this.fieldNames[i];
                row.appendChild(td);
            }
            table.appendChild(row);
        }
        var row = document.createElement('tr');
        for(var i=0; i<this.fieldInfos.length; i++) {
            var fieldInfo = this.fieldInfos[i];
            var fname = this.getAttribute('id') +"_"+ this.msgName +"_"+ fieldInfo.name;
            var td = document.createElement('td');
            td.textContent = '?';
            this.fields.push(td);
            row.appendChild(td);
        }
        table.appendChild(row);

        this.shadow.appendChild(table);
    }
}

/*
 * Displays as column.
 */
class MsgLabelsColumn extends MsgLabels {
    createFields() {
        var table = document.createElement('table');
        table.setAttribute('border', 1);
        if(this.showMsgName) {
            var row = document.createElement('tr');
            var td = document.createElement('td');
            td.setAttribute('colspan', '2');
            td.textContent = this.msgName;
            row.appendChild(td);
            table.appendChild(row);
        }
        for(var i=0; i<this.fieldInfos.length; i++) {
            var row = document.createElement('tr');
            if(this.showHeader) {
                var td = document.createElement('td');
                td.textContent = this.fieldNames[i];
                row.appendChild(td);
            }
            var td = document.createElement('td');
            td.textContent = '?';
            this.fields.push(td);
            row.appendChild(td);
            table.appendChild(row);
        }
        this.shadow.appendChild(table);
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
        console.log("MsgEdit.Send: "+msgtools.toJSON(msg));
    }
    sendButton() {
        var i = document.createElement('input');
        i.setAttribute('type', 'button');
        i.setAttribute('value', 'Send');
        i.setAttribute('style', 'width: 100%');
        i.onclick = this.sendClicked.bind(this);
        return i;
    }
}

/*
 * Edit field values for a message in a row.
 */
class MsgEditRow extends MsgEdit {
    createFields() {
        var table = document.createElement('table');
        table.setAttribute('border', 1);
        if(this.showMsgName) {
            var row = document.createElement('tr');
            var td = document.createElement('td');
            td.setAttribute('colspan', this.fieldInfos.length);
            td.textContent = this.msgName;
            row.appendChild(td);
            table.appendChild(row);
        }
        if(this.showHeader) {
            var row = document.createElement('tr');
            for(var i=0; i<this.fieldNames.length; i++) {
                var td = document.createElement('td');
                td.textContent = this.fieldNames[i];
                row.appendChild(td);
            }
            table.appendChild(row);
        }
        var row = document.createElement('tr');
        for(var i=0; i<this.fieldInfos.length; i++) {
            var fieldInfo = this.fieldInfos[i];
            var fname = this.getAttribute('id') +"_"+ this.msgName +"_"+ fieldInfo.name;
            var td = document.createElement('td');
            row.appendChild(td);
            var textEdit = document.createElement('input');
            textEdit.setAttribute('type', 'text');
            textEdit.setAttribute('id', fname);
            this.fields.push(textEdit);
            td.appendChild(textEdit);
        }
        table.appendChild(row);
        var row = document.createElement('tr');
        var td = document.createElement('td');
        td.setAttribute('colspan', this.fieldInfos.length);
        td.appendChild(this.sendButton());
        row.appendChild(td);
        table.appendChild(row);

        this.shadow.appendChild(table);
    }
}

/*
 * Edit field values for a message in a column.
 */
class MsgEditColumn extends MsgEdit {
    createFields() {
        var table = document.createElement('table');
        table.setAttribute('border', 1);
        if(this.showMsgName) {
            var row = document.createElement('tr');
            var td = document.createElement('td');
            td.setAttribute('colspan', '2');
            td.textContent = this.msgName;
            row.appendChild(td);
            table.appendChild(row);
        }
        for(var i=0; i<this.fieldInfos.length; i++) {
            var fieldInfo = this.fieldInfos[i];
            var fname = this.getAttribute('id') +"_"+ this.msgName +"_"+ fieldInfo.name;
            var row = document.createElement('tr');
            if(this.showHeader)
                var td = document.createElement('td');
                td.textContent = this.fieldNames[i];
                row.appendChild(td);
            var td = document.createElement('td');
            var textEdit = document.createElement('input');
            textEdit.setAttribute('type', 'text');
            textEdit.setAttribute('id', fname);
            this.fields.push(textEdit);
            td.appendChild(textEdit);
            row.appendChild(td);
            table.appendChild(row);
        }
        var row = document.createElement('tr');
        var td = document.createElement('td');
        td.setAttribute('colspan', '2');
        td.appendChild(this.sendButton());
        row.appendChild(td);
        table.appendChild(row);

        this.shadow.appendChild(table);
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
