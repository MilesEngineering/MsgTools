/*
 * Plots a time series of data, with configurable number of lines and names.
 */

if (typeof MsgBasePlot !== "undefined") {
    console.log('MsgBasePlot already loaded');
} else {
var svgns = "http://www.w3.org/2000/svg";
class MsgBasePlot extends HTMLElement {
    constructor() {
        super();

        this.shadow = this.attachShadow({mode: 'open'});

        var style = document.createElement('style');
        style.textContent = `
svg {
   font-family: monospace;
}

.axis {
   stroke-width: 1;
}

.axis .tick line {
   stroke: black;
}

.axis .tick text {
   fill: black;
   font-size: 0.7em;
}

.axis .domain {
   fill: none;
   stroke: black;
}

.group {
   fill: none;
   stroke: black;
   stroke-width: 1.5;
}`;
        this.shadow.appendChild(style);
        
        if(this.hasAttribute('timeLimit')) {
            this.timeLimit = parseFloat(this.getAttribute('timeLimit')); // seconds
        } else {
            this.timeLimit = 20.0;
        }
        this.duration = 750;
        if(this.hasAttribute('yMin') || this.hasAttribute('yMax')) {
            this.yMin = parseFloat(this.getAttribute('yMin'));
            this.yMax = parseFloat(this.getAttribute('yMax'));
            this.autoscale = 0;
        } else {
            this.yMin = 0;
            this.yMax = 1;
            this.autoscale = 1;
        }
    
        // #a09344
        // #7f64b9
        // #c36785
        this.dataSets = {};
        if(this.hasAttribute('labels')) {
            let labels = this.getAttribute('labels').split(",");
            this.configureDataSets(labels);
        }
        this.timestamps = [];

        this.shift = null;
        this.yAxisLabelWidth = 50;
        this.xAxisLabelHeight = 20;

        this.svg = document.createElementNS(svgns, 'svg');
        this.svg.setAttribute('class', 'chart');
        this.shadow.appendChild(this.svg);
        this.svg_selector = d3.select(this.svg);

        window.addEventListener('resize', this.resize.bind(this));
        window.addEventListener('visibilitychange', this.resize.bind(this));
        this.resize();
    }
    
    configureDataSets(labels)
    {
        let colors = ['red','blue','green','orange','purple','hotpink','cyan','limegreen','magenta','darkred','darkblue','darkgreen','darkorange','darkpurple'];
        var color=0;
        for (var i in labels) {
            var label = labels[i];
            this.dataSets[label] = {
                value: 0,
                color: colors[color],
                data: [],
                pathData: [],
                name: label
            }
            color++;
        }
    }

    resize()
    {
        // if the element is hidden, don't do anything.
        if(this.offsetParent === null) {
            return;
        }
        var rect = this.parentElement.getBoundingClientRect();
        //console.log(rect);
        //console.log(this.getBoundingClientRect());
        this.width = rect.width;
        this.height = rect.height;
        if(this.hasAttribute('height')) {
            var height = this.getAttribute('height');
            if(height.includes("%")) {
                this.height = this.height * height.replace("%","") / 100;
            } else {
                this.height = height;
            }
        }
        if(this.hasAttribute('width')) {
            var width = this.getAttribute('width');
            if(width.includes("%")) {
                this.width = this.width * width.replace("%","") / 100;
            } else {
                this.width = width;
            }
        }
        this.emptySVG();
        this.pixelPerSecond = ((this.width-2.0*this.yAxisLabelWidth)/this.timeLimit);
        this.initFromData();
    }

    initFromData()
    {
        this.svg.setAttribute("viewBox", "0 0 "+(this.width)+" "+(this.height));

        this.xScale = d3.scale.linear()
            .domain([-this.timeLimit, 0])
            .range([this.yAxisLabelWidth, this.width-this.yAxisLabelWidth])

        this.yScale = d3.scale.linear()
            .domain([this.yMin, this.yMax])
            .range([this.height-this.xAxisLabelHeight, 0])

        var that = this;

        this.xAxis = this.svg_selector.append('g')
            .attr('class', 'x axis')
            .attr('transform', 'translate(0,' + (this.height-this.xAxisLabelHeight) + ')')
            .call(that.xScale.axis = d3.svg.axis().scale(that.xScale).orient('bottom'));

        this.yAxis = this.svg_selector.append('g')
            .attr('class', 'y axis')
            .attr('transform', 'translate(' + this.yAxisLabelWidth + ',0)')
            .call(that.yScale.axis = d3.svg.axis().scale(that.yScale).orient('left'));

        this.yAxisR = this.svg_selector.append('g')
            .attr('class', 'y axis')
            .attr('transform', 'translate(' + (this.width-this.yAxisLabelWidth) + ',0)')
            .call(that.yScale.axis = d3.svg.axis().scale(that.yScale).orient('right'));

        this.paths = this.svg_selector.append('g');

        this.labels = {};
        var y = 5;
        for (var name in this.dataSets) {
            let group = this.dataSets[name];
            group.path = this.paths.append('path')
                .attr('d', 'M 0,0')
                .attr('class', name + ' group')
                .style('stroke', group.color)
                .style('stroke-width', 1);
            
            this.labels[name] = 
                this.svg_selector.append('text')
                    .attr('class', 'value xvalue')
                    .attr('x', this.yAxisLabelWidth+10)
                    .attr('y', y)
                    .attr('fill', group.color)
                    .attr('dominant-baseline', 'text-before-edge')
                    .text(name);
            y += 15;
        }

        for (var name in this.dataSets)
        {
            this.dataSets[name].pathData = [ ];
            for(var i=0; i<this.timestamps.length; i++) {
                this.dataSets[name].pathData.push(((this.timestamps[i]-this.shift)*this.pixelPerSecond)+","+this.yScale(this.dataSets[name].data[i]));
            }
            if(this.timestamps.length>2) {
                this.dataSets[name].path.attr("d", "M "+(this.dataSets[name].pathData.join(" L ")));
            }
        }
    }

    setValues(values) {
        var i = 0;
        for (var name in this.labels) {
            var val = values[i];
            this.labels[name].text((val < 0 ? name : name+' ') + Math.round(val));
            i += 1;
        }
    }
    
    autoscaleYAxis() {
        var newMin = Number.POSITIVE_INFINITY;
        var newMax = Number.NEGATIVE_INFINITY;
        var hit_limit = 0;
        for (var name in this.labels) {
            for(i in this.dataSets[name].data) {
                var val = this.dataSets[name].data[i];
                if(val < newMin) {
                    newMin = val;
                }
                if(val > newMax) {
                    newMax = val;
                }
            }
        }
        if((newMax > this.yMax || newMax < this.yMax)||
           (newMin < this.yMin || newMin > this.yMin)) {
            this.yMax = newMax;
            this.yMin = newMin;
            this.yScale = d3.scale.linear()
                .domain([this.yMin, this.yMax])
                .range([this.height-this.xAxisLabelHeight, 0])
            this.emptySVG();
            this.initFromData();
        }
    }
    
    adjustTimeLimit(newLimit) {
        this.timeLimit = Math.abs(newLimit);
        this.emptySVG();
        this.pixelPerSecond = ((this.width-2.0*this.yAxisLabelWidth)/this.timeLimit);
        this.initFromData();
    }

    emptySVG() {
        while(this.svg.lastChild) {
            this.svg.removeChild(this.svg.lastChild);
        }
    }

    plot(time, newData) {
        if(this.autoscale) {
            this.autoscaleYAxis();
        }
        this.setValues(newData);
        //time /= 1000.0;
        this.now = time;
        // Add new values
        if(this.shift === null) {
            this.shift = time;
        }
        // the performance of this approach comes from not having to recompute
        // the path data with every update. 
        this.paths.attr('transform', 'translate('+(this.width-this.yAxisLabelWidth-(time-this.shift)*this.pixelPerSecond)+' 0)');

        // figure out how many of the initial items are expired
        var expired = 0;
        for(var past of this.timestamps) {
            if(past < (time - this.timeLimit)) {
                expired ++;
            } else {
                break;
            }
        }

        // trim off expired items
        this.timestamps.splice(0, expired);
        for(var name in this.dataSets) {
            this.dataSets[name].data.splice(0, expired);
            this.dataSets[name].pathData.splice(0, expired);
        }
        
        this.timestamps.push(time);
        var dataNum = 0;
        for (var name in this.dataSets)
        {
            var value = newData[dataNum++];
            this.dataSets[name].data.push(value);
            // append a chunk of svg path data to the list
            this.dataSets[name].pathData.push(((time-this.shift)*this.pixelPerSecond)+","+this.yScale(value));

            // convert the entire list into svg path data. just string concat
            this.dataSets[name].path.attr("d", "M "+(this.dataSets[name].pathData.join(" L ")));
        }
    }
}

// This should be run after we're confident that all of the uses of the
// tag have been defined, so that our calls to getAttribute will succeed.
// (Also after any remaining dependencies are loaded.)
// Best plan is just to import this whole file at the end of your HTML.
customElements.define('msgtools-plot', MsgBasePlot);
window.MsgBasePlot = MsgBasePlot;
}
