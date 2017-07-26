// right now this works with exactly 3 lines.
// it should be modified to work with any number of lines, specified by constructor parameters
// perhaps allow user to pass in an array of names and colors?
var PlotData = function(htmlId, timeLimit, yMin, yMax) {   
    this.timeLimit = timeLimit // seconds
    this.duration = 750
    this.width = 500
    this.height = 200
    
    this.dataSets = {
        X: {
            value: 0,
            color: 'orange',
            data: []
        },
        Y: {
            value: 0,
            color: 'green',
            data: []
        },
        Z: {
            value: 0,
            color: 'red',
            data: []
        }
    }
    this.timestamps = []
    
    var that = this
    
    yAxisLabelWidth = 50;
    xAxisLabelHeight = 20;
    
    this.xScale = d3.scale.linear()
        .domain([-this.timeLimit, 0])
        .range([yAxisLabelWidth, this.width-10])

    this.yScale = d3.scale.linear()
        .domain([yMin, yMax])
        .range([this.height-xAxisLabelHeight, 0])

    this.line = d3.svg.line()
        .interpolate('linear')
        .x(function(d, i) {
            timeOffset = -(that.now - that.timestamps[i]) / 1000.0
            return that.xScale(timeOffset);
        })
        .y(function(d) {
            return that.yScale(d)
        })

    this.svg = d3.select(htmlId).append('svg')
        .attr('class', 'chart')
        .attr('width', this.width)
        .attr('height', this.height + 0)

    this.xAxis = this.svg.append('g')
        .attr('class', 'x axis')
        .attr('transform', 'translate(0,' + (this.height-xAxisLabelHeight) + ')')
        .call(that.xScale.axis = d3.svg.axis().scale(that.xScale).orient('bottom'))

    this.yAxis = this.svg.append('g')
        .attr('class', 'y axis')
        .attr('transform', 'translate(' + 50 + ',0)')
        .call(that.yScale.axis = d3.svg.axis().scale(that.yScale).orient('left'))

    this.paths = this.svg.append('g')

        
    for (var name in this.dataSets) {
        let group = this.dataSets[name]
        group.path = this.paths.append('path')
            .data([group.data])
            .attr('class', name + ' group')
            .style('stroke', group.color)
    }
};

PlotData.prototype.plot = function(time, newData){
    this.now = time;
    // remove data older than timeLimit
    while(this.timestamps[0] < time - this.timeLimit*1000)
    {
        for (var name in this.dataSets)
        {
            this.dataSets[name].data.shift();
        }
        this.timestamps.shift();
    }
    // Add new values
    var dataNum = 0;
    this.timestamps.push(time);
    for (var name in this.dataSets)
    {
        this.dataSets[name].data.push(newData[dataNum]);
        this.dataSets[name].path.attr('d', this.line);
        dataNum++;
    }
}
