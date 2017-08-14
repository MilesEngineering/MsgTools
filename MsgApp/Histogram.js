var Histogram = function(htmlId, minVal, maxVal) {
    
    this.htmlId = htmlId;
    
    this.minVal = minVal;
    this.maxVal = maxVal;

    this.data = [];

    this.parent = $(htmlId)[0];

    this.svg = d3.select(htmlId).append('svg').attr('class', 'chart');

    var histogram = this;

    this.resize = function() {
        // there's probably a better test to do here.
        if(histogram.parent.parentElement.style.display == "none")
            return;
        // basically these offset values don't make any sense if we're
        // hidden.
        histogram.width = histogram.parent.offsetWidth - 10;
        histogram.height = histogram.parent.offsetHeight - 20;
        $(histogram.htmlId+">svg").empty();
        histogram.initFromData();
    };

    window.addEventListener('resize', this.resize);
    this.resize();
}

Histogram.prototype.initFromData = function()
{
    this.g = this.svg.append("g");

    this.svg.attr("viewBox", "0 0 "+(this.width+10)+" "+(this.height+20));

    var that = this

    this.x = d3.scaleLinear()
        .domain([this.minVal, this.maxVal])
        .rangeRound([5, that.width]);

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

Histogram.prototype.changeDomain = function(lo, hi) {
    if(this.width === undefined)
        return;
    this.minVal = lo;
    this.maxVal = hi;
    this.x = d3.scaleLinear()
    .domain([this.minVal, this.maxVal])
    .rangeRound([5, this.width]);

    $(this.htmlId+">svg").empty();
    this.initFromData()
}

Histogram.prototype.plot = function(data){
    this.data.push(data)
    $(this.htmlId+">svg").empty();
    this.initFromData()
}

Histogram.prototype.clear = function(){
    this.data = [];
    $(this.htmlId+">svg").empty();
    this.initFromData()
}
