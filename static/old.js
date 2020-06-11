// bar chart tutorial: https://jsfiddle.net/matehu/w7h81xz2/ https://blog.risingstack.com/d3-js-tutorial-bar-charts-with-javascript/

var data = {{data}}
var barHeight = 20;
var bar = d3.select('svg').selectAll('rect').data(data).enter().append('rect').attr('width', function(d) {  return d; }).attr('height', barHeight - 1).attr('transform', function(d, i) { return "translate(0," + i * barHeight + ")";          });





d3.select('#btn')        .on('click', function () {            d3.select('body')               .append('h3')               .text('Today is a beautiful day!!');        });

// bar chart

const sample = [
    {
      language: 'Rust',
      value: 78.9,
      color: '#000000'
    },
    {
      language: 'Kotlin',
      value: 75.1,
      color: '#00a2ee'
    },
    {
      language: 'Python',
      value: 68.0,
      color: '#fbcb39'
    },
    {
      language: 'TypeScript',
      value: 67.0,
      color: '#007bc8'
    },
    {
      language: 'Go',
      value: 65.6,
      color: '#65cedb'
    },
    {
      language: 'Swift',
      value: 65.1,
      color: '#ff6e52'
    },
    {
      language: 'JavaScript',
      value: 61.9,
      color: '#f9de3f'
    },
    {
      language: 'C#',
      value: 60.4,
      color: '#5d2f8e'
    },
    {
      language: 'F#',
      value: 59.6,
      color: '#008fc9'
    },
    {
      language: 'Clojure',
      value: 59.6,
      color: '#507dca'
    }
  ];

  
const margin = 60;
const width = 500- 2 * margin;
const height = 500 - 2 * margin;    

const chart = keywordsContainer.append('g')
.attr('transform', `translate(${margin}, ${margin})`);

const yScale = d3.scaleLinear()
.range([height, 0])
.domain([0, 100]);

chart.append('g')
.call(d3.axisLeft(yScale));

const xScale = d3.scaleBand()
.range([0, width])
.domain(sample.map((s) => s.language))
.padding(0.2)

chart.append('g')
.attr('transform', `translate(0, ${height})`)
.call(d3.axisBottom(xScale));

const barGroups = chart.selectAll()
.data(sample)
.enter()
.append('g')


chart.selectAll()
.data(sample)
.enter()
.append('rect')
.attr('x', (s) => xScale(s.language))
.attr('y', (s) => yScale(s.value))
.attr('height', (s) => height - yScale(s.value))
.attr('width', xScale.bandwidth())

chart.append('g')
.attr('class', 'grid')
.call(d3.axisLeft()
    .scale(yScale)
    .tickSize(-width, 0, 0)
    .tickFormat(''))

keywordsContainer.append('text')
.attr('x', -(height / 2) - margin)
.attr('y', margin / 2.4)
.attr('transform', 'rotate(-90)')
.attr('text-anchor', 'middle')
.text('Love meter (%)')

keywordsContainer.append('text')
.attr('x', width / 2 + margin)
.attr('y', 40)
.attr('text-anchor', 'middle')
.text('Most loved programming languages in 2018')

svgElement
.on('mouseenter', function (actual, i) {
    d3.select(this).attr('opacity', 0.5)
})
.on('mouseleave', function (actual, i) {
    d3.select(this).attr('opacity', 1)
})