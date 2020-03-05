        
var data = {{data}}
var barHeight = 20;
var bar = d3.select('svg').selectAll('rect').data(data).enter().append('rect').attr('width', function(d) {  return d; }).attr('height', barHeight - 1).attr('transform', function(d, i) { return "translate(0," + i * barHeight + ")";          });





d3.select('#btn')        .on('click', function () {            d3.select('body')               .append('h3')               .text('Today is a beautiful day!!');        });

