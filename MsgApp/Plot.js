// right now this works with exactly 3 lines.
// it should be modified to work with any number of lines, specified by constructor parameters
// perhaps allow user to pass in an array of names and colors?
var PlotData = function(htmlId) {
    this.limit = 60 * 1
    this.duration = 750
    this.now = new Date(Date.now() - this.duration)
    this.width = 500
    this.height = 200
    
    this.groups = {
        X: {
            value: 0,
            color: 'orange',
            data: d3.range(this.limit).map(function() {
                return 0
            })
        },
        Y: {
            value: 0,
            color: 'green',
            data: d3.range(this.limit).map(function() {
                return 0
            })
        },
        Z: {
            value: 0,
            color: 'grey',
            data: d3.range(this.limit).map(function() {
                return 0
            })
        }
    }
    
    var that = this
    this.xScale = d3.time.scale()
        .domain([that.now - (that.limit - 2), that.now - that.duration])
        .range([0, this.width])

    this.yScale = d3.scale.linear()
        .domain([-8192, 8192])
        .range([this.height, 0])

    this.line = d3.svg.line()
        .interpolate('linear')
        .x(function(d, i) {
            return that.xScale(that.now - (that.limit - 1 - i) * that.duration)
        })
        .y(function(d) {
            return that.yScale(d)
        })

    this.svg = d3.select(htmlId).append('svg')
        .attr('class', 'chart')
        .attr('width', this.width)
        .attr('height', this.height + 50)

    this.axis = this.svg.append('g')
        .attr('class', 'x axis')
        .attr('transform', 'translate(0,' + this.height + ')')
        .call(that.xScale.axis = d3.svg.axis().scale(that.xScale).orient('bottom'))

    this.paths = this.svg.append('g')

    for (var name in this.groups) {
        var group = this.groups[name]
        group.path = this.paths.append('path')
            .data([group.data])
            .attr('class', name + ' group')
            .style('stroke', group.color)
    }
};

PlotData.prototype.plot = function(time, data){
    this.now = time
    // Add new values
    var dataNum = 0
    for (var name in this.groups)
    {
        this.groups[name].data.push(data[dataNum])
        this.groups[name].path.attr('d', this.line)
        dataNum++
    }

    // Shift domain
    this.xScale.domain([time - (this.limit - 2) * this.duration, time - this.duration])

    // Remove oldest data point from each group
    for (var name in this.groups)
    {
        this.groups[name].data.shift()
    }
}
