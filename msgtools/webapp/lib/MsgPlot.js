/*
 * Plots fields of a message.
 */
 class MsgPlot extends BasePlot {
    constructor() {
        super();
        msgtools.DelayedInit.add(this);
    }
    init() {
        var msgName = this.getAttribute('msgName');
        this.msgClass = msgtools.findMessageByName(msgName);

        var fieldNames = this.getAttribute('labels').split(",");
        if(this.hasAttribute('fields')) {
            var fieldNames = this.getAttribute('fields').split(",");
        }
        
        this.fieldInfos = [];
        for(var i=0; i<fieldNames.length; i++) {
            this.fieldInfos.push(msgtools.findFieldInfo(this.msgClass, fieldNames[i]));
        }

        // Register to receive our messages so we can plot fields from them.
        msgtools.MessageClient.dispatch.register(this.msgClass.prototype.MSG_ID, this.plot.bind(this));
    }

    plot(msg) {
        var time = msg.hdr.GetTime();
        var newData = [];
        for(var i=0; i<this.fieldInfos.length; i++) {
            var fieldInfo = this.fieldInfos[i];
            var value = msg[fieldInfo.get]();
            newData.push(value);
        }
        super.plot(time, newData);
    }

}

customElements.define('msgtools-msgplot', MsgPlot);
