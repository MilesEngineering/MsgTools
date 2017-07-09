var Histogram = function(htmlId, minVal, maxVal) {
    
    this.htmlId = htmlId;
    
    this.minVal = minVal;
    this.maxVal = maxVal;

    this.data = d3.range(10).map(d3.randomNormal(50, 10));

    this.margin = {top: 10, right: 30, bottom: 30, left: 30}
    this.width = 960
    this.height = 500

    this.svg = d3.select(htmlId).append('svg')
        .attr('class', 'chart')
        .attr('width', this.width)
        .attr('height', this.height)

    this.width += - this.margin.left - this.margin.right
    this.height += - this.margin.top - this.margin.bottom
    
    this.initFromData()
}

Histogram.prototype.initFromData = function()
{
    this.g = this.svg.append("g").attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")");

    var that = this

    this.x = d3.scaleLinear()
        .domain([this.minVal, this.maxVal])
        .rangeRound([0, that.width]);

    this.bins = d3.histogram()
        .domain(that.x.domain())
        .thresholds(that.x.ticks(20))
        (this.data);

    this.y = d3.scaleLinear()
        .domain([0, d3.max(this.bins, function(d) { return d.length; })])
        .range([this.height, 0]);

    this.bar = this.g.selectAll(".bar")
      .data(this.bins)
      .enter().append("g")
        .attr("class", "bar")
        .attr("transform", function(d) { return "translate(" + that.x(d.x0) + "," + that.y(d.length) + ")"; });

    this.bar.append("rect")
        .attr("x", 1)
        .attr("width", that.x(that.bins[0].x1) - that.x(that.bins[0].x0) - 1)
        .attr("height", function(d) { return that.height - that.y(d.length); });

    var formatCount = d3.format(",.0f");

    this.bar.append("text")
        .attr("dy", ".75em")
        .attr("y", 6)
        .attr("x", (that.x(that.bins[0].x1) - that.x(that.bins[0].x0)) / 2)
        .attr("text-anchor", "middle")
        .text(function(d) { return formatCount(d.length); });

    this.g.append("g")
        .attr("class", "axis axis--x")
        .attr("transform", "translate(0," + that.height + ")")
        .call(d3.axisBottom(that.x));
}

Histogram.prototype.plot = function(data){
    console.log("Got " + data)
    this.data.push(data)
    $(this.htmlId+">svg").empty();
    this.initFromData()
}

Histogram.prototype.clear = function(){
    this.data = [];
    $(this.htmlId+">svg").empty();
    this.initFromData()
}
