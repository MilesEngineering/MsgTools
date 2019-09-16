/*
 * Plots fields of a message.
 */
if (typeof MsgPlot !== "undefined") {
    console.log('MsgPlot already loaded')
} else {

 class MsgPlot extends MsgBasePlot {
    constructor() {
        super();
        msgtools.DelayedInit.add(this);
    }
    init() {
        var msgName = this.getAttribute('msgName');
        this.msgClass = msgtools.findMessageByName(msgName);
        this.fieldInfos = [];

        if(this.hasAttribute('labels')) {
            var fieldNames = this.getAttribute('labels').split(",");
        }
        if(this.hasAttribute('fields')) {
            var fieldNames = this.getAttribute('fields').split(",");
        }
        if(fieldNames == undefined) {
            let labels = [];
            for(var i=0; i<this.msgClass.prototype.fields.length; i++) {
                var fi = this.msgClass.prototype.fields[i];
                this.fieldInfos.push(fi);
                labels.push(fi.name);
            }
            this.configureDataSets(labels);
            this.resize();
        } else {
            for(var i=0; i<fieldNames.length; i++) {
                this.fieldInfos.push(msgtools.findFieldInfo(this.msgClass, fieldNames[i]));
            }
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

}