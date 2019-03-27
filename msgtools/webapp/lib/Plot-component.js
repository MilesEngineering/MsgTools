// right now this works with exactly 3 lines.
// it should be modified to work with any number of lines, specified by constructor parameters
// perhaps allow user to pass in an array of names and colors?
var svgns = "http://www.w3.org/2000/svg";
class TimeSeries extends HTMLDivElement {
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
        
        this.timeLimit = parseFloat(this.getAttribute('timeLimit')); // seconds
        this.duration = 750;
        this.yMin = parseFloat(this.getAttribute('yMin'));
        this.yMax = parseFloat(this.getAttribute('yMax'));;
    
        // #a09344
        // #7f64b9
        // #c36785
        let labels = this.getAttribute('labels').split(",");
        let colors = ['rgb(219,109,0)', '#000000', 'rgb(0,109,219)', 'rgb(109,219,0)','rgb(109,0,219)'];
        var color=0;
        this.dataSets = {};
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
        this.timestamps = [];

        this.shift = null;
        this.yAxisLabelWidth = 50;
        this.xAxisLabelHeight = 20;

        this.svg = document.createElementNS(svgns, 'svg');
        this.svg.setAttribute('class', 'chart');
        this.shadow.appendChild(this.svg);
        this.svg_selector = d3.select(this.svg);

        window.addEventListener('resize', this.resize.bind(this));
        this.resize();
    }

    resize()
    {
        var p = this.parentElement;
        this.width = p.clientWidth - parseFloat(window.getComputedStyle(p, null).getPropertyValue('padding-left')) - parseFloat(window.getComputedStyle(p, null).getPropertyValue('padding-right'));
        this.height = p.clientHeight - parseFloat(window.getComputedStyle(p, null).getPropertyValue('padding-top')) - parseFloat(window.getComputedStyle(p, null).getPropertyValue('padding-bottom'));
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
            console.log("name: " + name);
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
            console.log("name: " + name)
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
        var hit_limit = 0;
        for (var name in this.labels) {
            var val = values[i];
            this.labels[name].text((val < 0 ? name : name+' ') + Math.round(val));
            i += 1;
            if(val < this.yMin) {
                this.yMin = val;
                hit_limit = 1;
            }
            if(val > this.yMax) {
                this.yMax = val;
                hit_limit = 1;
            }
        }
        // TODO This doesn't work, it only changes where the point is put on screen,
        // it doesn't change points already plotted, and it doesn't change axis labels
        if(0 && hit_limit) {
            this.yScale = d3.scale.linear()
                .domain([this.yMin, this.yMax])
                .range([this.height-this.xAxisLabelHeight, 0])
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
customElements.define('plot-timeseries', TimeSeries, { extends: 'div' });
