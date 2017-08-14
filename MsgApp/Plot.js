// right now this works with exactly 3 lines.
// it should be modified to work with any number of lines, specified by constructor parameters
// perhaps allow user to pass in an array of names and colors?
var PlotData = function(htmlId, timeLimit, yMin, yMax) {   
    this.htmlId = htmlId;
    this.parent = $(htmlId)[0];
    this.timeLimit = timeLimit; // seconds
    this.duration = 750;
    this.width = 500;
    this.height = 200;
    this.yMin = yMin;
    this.yMax = yMax;
    
    // #a09344
    // #7f64b9
    // #c36785
    this.dataSets = {
        X: {
            value: 0,
            color: 'rgb(219,109,0)',
            data: [],
            pathData: []
        },
        Y: {
            value: 0,
            color: '#000000',
            data: [],
            pathData: []
        },
        Z: {
            value: 0,
            color: 'rgb(0,109,219)',
            data: [],
            pathData: []
        }
    }
    this.timestamps = [];

    this.shift = null;
    this.yAxisLabelWidth = 50;
    this.xAxisLabelHeight = 20;

    this.svg = d3.select(this.htmlId).append('svg')
    .attr('class', 'chart');

    this.redraw = 0;
    var plot = this;
    PlotData.prototype.resize = function()
    {
        plot.width = plot.parent.offsetWidth;
        plot.height = plot.parent.offsetHeight;
        $(plot.htmlId+">svg").empty();
        this.pixelPerSecond = ((plot.width-2.0*plot.yAxisLabelWidth)/plot.timeLimit);
        plot.initFromData();
        this.redraw = 0;
    }

    window.addEventListener('resize', this.resize);
    this.resize();
};

PlotData.prototype.initFromData = function()
{
    this.svg.attr("viewBox", "0 0 "+(this.width)+" "+(this.height));

    this.xScale = d3.scale.linear()
        .domain([-this.timeLimit, 0])
        .range([this.yAxisLabelWidth, this.width-this.yAxisLabelWidth])

    this.yScale = d3.scale.linear()
        .domain([this.yMin, this.yMax])
        .range([this.height-this.xAxisLabelHeight, 0])

    var that = this;

    this.xAxis = this.svg.append('g')
        .attr('class', 'x axis')
        .attr('transform', 'translate(0,' + (this.height-this.xAxisLabelHeight) + ')')
        .call(that.xScale.axis = d3.svg.axis().scale(that.xScale).orient('bottom'))

    this.yAxis = this.svg.append('g')
        .attr('class', 'y axis')
        .attr('transform', 'translate(' + this.yAxisLabelWidth + ',0)')
        .call(that.yScale.axis = d3.svg.axis().scale(that.yScale).orient('left'))

    this.yAxisR = this.svg.append('g')
        .attr('class', 'y axis')
    .attr('transform', 'translate(' + (this.width-this.yAxisLabelWidth) + ',0)')
        .call(that.yScale.axis = d3.svg.axis().scale(that.yScale).orient('right'))

    this.paths = this.svg.append('g');

    for (var name in this.dataSets) {
        let group = this.dataSets[name]
        group.path = this.paths.append('path')
            .attr('d', 'M 0,0')
            .attr('class', name + ' group')
            .style('stroke', group.color)
            .style('stroke-width', 1);
    } 

    this.xlabel = this.svg.append('text')
    .attr('class', 'value xvalue')
    .attr('x', this.yAxisLabelWidth+10)
    .attr('y', 5)
    .attr('fill', 'rgb(219,109,0)')
    .attr('dominant-baseline', 'text-before-edge')
    .text('X ');

    this.ylabel = this.svg.append('text')
    .attr('class', 'value yvalue')
    .attr('x', this.yAxisLabelWidth+10)
    .attr('y', 20)
    .attr('fill', '#000000')
    .attr('dominant-baseline', 'text-before-edge')
    .text('Y ');

    this.zlabel = this.svg.append('text')
    .attr('class', 'value zvalue')
    .attr('x', this.yAxisLabelWidth+10)
    .attr('y', 35)
    .attr('fill', 'rgb(0,109,219)')
    .attr('dominant-baseline', 'text-before-edge')
    .text('Z ');

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

PlotData.prototype.adjustTimeLimit = function(newLimit) {
    this.timeLimit = Math.abs(newLimit);
    $(this.htmlId+">svg").empty();
    this.pixelPerSecond = ((this.width-2.0*this.yAxisLabelWidth)/this.timeLimit);
    this.initFromData();
}

PlotData.prototype.plot = function(time, newData) {
    time /= 1000.0;
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
