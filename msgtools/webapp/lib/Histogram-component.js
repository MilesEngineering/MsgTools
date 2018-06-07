var svgns = "http://www.w3.org/2000/svg";

class Histogram extends HTMLElement {
    constructor() {
        super();

        var histogram = this;
        
        this.shadow = this.attachShadow({mode: 'open'});

        // This is our internal styling. You could of course modify this arbirarily
        // if you bring a copy of this file into your project, or you could add some
        // more levers and switches to this class/tag to affect the styling.
        var style = document.createElement('style');
        style.textContent = 'rect.bar { fill: steelblue; } svg { padding: 0; margin: 0; }'
        this.shadow.appendChild(style);
        
        this.range_min = parseInt(this.getAttribute('range-min'));
        this.range_max = parseInt(this.getAttribute('range-max'));

        this.display_min = this.range_min;
        this.display_max = this.range_max;

        this.axesarea = 20;

        this.data = { };
        this.maxvalue = 1;

        this.svg = document.createElementNS(svgns, "svg");
        this.svg.style.display = "block";

        this.maing = document.createElementNS(svgns, "g");
        this.svg.appendChild(this.maing);

        this.axesg = document.createElementNS(svgns, "g");
        this.svg.appendChild(this.axesg);

        this.axis = document.createElementNS(svgns, "line");
        this.axis.setAttributeNS(null, "style", "stroke:black; stroke-width:1");
        this.axesg.appendChild(this.axis);

        this.maxticks = 11;
        this.ticks = new Array();
        for(var i=0; i<this.maxticks; i++) {
            var tick = document.createElementNS(svgns, "text");
            tick.setAttributeNS(null, "font-size", 15);
            tick.setAttributeNS(null, "fill", "black");
            tick.setAttributeNS(null, "stroke", "none");
            tick.setAttributeNS(null, "text-anchor", "middle");
            tick.setAttributeNS(null, "x", 1e6);
            tick.textContent = "asdfasdf";
            this.ticks.push(tick);
            this.axesg.appendChild(tick);
        }

        this.histog = document.createElementNS(svgns, "g");
        this.maing.appendChild(this.histog);

        this.bars = { };
        for(var i=this.range_min; i<=this.range_max; i++) {
            this.bars[i] = document.createElementNS(svgns, "rect");
            this.histog.appendChild(this.bars[i]);
            this.bars[i].setAttributeNS(null, "x", i);
            this.bars[i].setAttributeNS(null, "y", 0);
            this.bars[i].setAttributeNS(null, "width", 0.99);
            this.bars[i].setAttributeNS(null, "height", 0);
            this.bars[i].setAttributeNS(null, "class", "bar");
        }
        
        this.shadow.appendChild(this.svg);

        window.addEventListener('resize', this.resize.bind(this));
        this.resize();
    }

    // If you want to pass around a reference to this method on a specific object
    // say, because you're passing it into setTimeout, you'll want to something like
    // var resizereference = myhistogram.resize.bind(myhistogram);
    // setTimeout(resizereference, 1);
    resize() {
        if(this.offsetWidth==0 || this.offsetHeight==0) {
            // forget it
            return;
        }
        this.width = this.offsetWidth;
        this.height = this.offsetHeight;
        this.histoheight = this.height - this.axesarea;

        // adjust/set transforms
        this.svg.setAttributeNS(null, "viewBox", "-10 -10 "+(this.width+10)+" "+(this.height+10));
        this.svg.setAttributeNS(null, "width", this.width);
        this.svg.setAttributeNS(null, "height", this.height);
        this.maing.setAttributeNS(null, "transform", "scale(1 -1) translate(0 "+(-this.histoheight)+")");
    
        this.axis.setAttributeNS(null, "x1", 0);
        this.axis.setAttributeNS(null, "x2", this.width);
        this.axis.setAttributeNS(null, "y1", this.height - (this.axesarea-1));
        this.axis.setAttributeNS(null, "y2", this.height - (this.axesarea-1));

        this.rescale();
    }

    rescale()
    {

          console.log("rescaling %o to %o %o",
          this, this.width/((this.display_max-this.display_min)+1),
          this.histoheight / this.maxvalue);


        var widthunit = this.width/((this.display_max-this.display_min)+1);
    
        this.histog.setAttributeNS(null, "transform", "scale("+widthunit+" "+(this.histoheight / this.maxvalue)+") translate(-"+this.display_min+" 0)");
        
        var tickIncrement = Math.max(1, (this.display_max-this.display_min) / (this.maxticks - 1));
        var i=0;
        var on_the_nose = false;
        for(var i=0; i<this.maxticks; i++) {
            var pos = Math.round(tickIncrement * i) + this.display_min;
            if(pos > this.display_max) {
                break;
            } else {
                if(pos == this.display_max) {
                    on_the_nose = true;
                }
                this.ticks[i].textContent = pos;
                this.ticks[i].setAttributeNS(null, "x", Math.round(tickIncrement * i) * widthunit + widthunit / 2.0);
                this.ticks[i].setAttributeNS(null, "y", this.height);
            }
        }
        if(!on_the_nose && i<this.maxticks) {
            this.ticks[i].textContent = this.display_max;
            this.ticks[i].setAttributeNS(null, "x", this.width - widthunit / 2.0);
            this.ticks[i].setAttributeNS(null, "y", this.height);
            i++;
        }
        for( ; i<this.maxticks; i++) {
            this.ticks[i].textContent = "";
            this.ticks[i].setAttributeNS(null, "x", 1e6);
        }
    }

    plot(value)
    {
        console.log("plotting %o", value);
        value = Math.round(value);
        if(value < this.range_min) { return; }
        if(value > this.range_max) { return; }
        if(value in this.data) {
            this.data[value] += 1;
        } else {
            this.data[value] = 1;
        }
        this.maxvalue = Math.max(this.maxvalue, this.data[value]);

        var bar = this.bars[value];
        bar.setAttributeNS(null, "height", this.data[value]);

        this.rescale();
    }

    changeDomain(new_min, new_max)
    {
        this.display_min = new_min;
        this.display_max = new_max;
        
        this.resize();
    }

    clear()
    {
        for(var k in this.bars) {
            this.bars[k].setAttributeNS(null, "height", 0);
        }
        this.data = { };
        this.maxvalue = 1;
        this.rescale();
    }
}

// This should be run after we're confident that all of the uses of the
// tag have been defined, so that our calls to getAttribute will succeed.
// Best plan is just to import this whole file at the end of your HTML.
customElements.define('plot-histogram', Histogram, { extends: 'div' });
