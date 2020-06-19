
//http://hdnrnzk.me/2012/07/04/creating-a-bar-graph-using-d3js/
    var svgContainer = d3.select("body").append("svg")
                                        .attr("width", 500)
                                        .attr("height", 500)
                                        .attr("style","outline:thin solid red;");
                svgContainer.append("line")
                            .attr("x1",0)
                            .attr("y1",250)
                            .attr("x2",500)
                            .attr("y2",250)
                            .attr("stroke-width",2)
                            .attr("stroke","grey")

                svgContainer.append("line")
                            .attr("x1",250)
                            .attr("y1",0)
                            .attr("x2",250)
                            .attr("y2",500)
                            .attr("stroke-width",2)
                            .attr("stroke","grey")                            


                svgContainer.append("text")
                            .attr("x",0)
                            .attr("y",245)
                            .text("PC1");

                svgContainer.append("text")
                .attr("x",250)
                .attr("y",15)
                .text("PC2");
    
    var circles = svgContainer.selectAll("circle")
                            .data(jsonCircles['circles'])
                            .enter()
                            .append("circle");

    var circleAttributes = circles
                        .attr("cx", function (d) { return d.x_axis; })
                        .attr("cy", function (d) { return d.y_axis; })
                        .attr("r", function (d) { return d.radius; })
                        .style("fill", function(d) { return d.color; })
                        .style("stroke", function(d) { return d.bordercolor; })
                        .style("fill-opacity", function(d) { return d.fill_opacity; })
                        .on('mouseover', function (d) {
                            d3.select(this).transition()
                                 .duration('50')
                                 .attr('opacity', "0.6" )})
                        .on('mouseout', function (d) {
                        d3.select(this).transition()
                                .duration('50')
                                .attr('opacity', "1.0" )})
                        .on("click",function(d){
                            selectTopic(d.label)
                        });
                        
                        
    var myText = svgContainer.selectAll(".mytext")
                    .data(jsonCircles['circles'])
                    .enter()
                    .append("text")
                    //the rest of your code

                    myText.style("fill", "black")
                    .attr("width", "10")
                    .attr("height", "10")
                    .attr("x", function(d) { return d.x_axis-5;  })
                    .attr("y", function(d) { return d.y_axis+5;  })
                    .text(function(d) { return d.label;  }); //function(d) { return d.name; }


    function selectTopic(label){
        document.getElementById("toolbar_label").innerHTML = label;    
    }



    document.getElementById("demo").innerHTML = 'Number of topics '+num_topics;
    document.getElementById("toolbar_label").innerHTML = 'toolbaaar';
    //tool bar
    
    d3.select('#editbutton')        
    .on('click', selectTopic("funciona") );                                                


    
    topic_id = 0
    console.log(sample[topic_id])

    console.log(sample[topic_id].map((s)=>s.probability))
    //keywords barchart

    var chartContainer = d3.select("body").append("svg")
                        .attr("width", 500)
                        .attr("height", 500)
                        .attr("style","outline:thin solid red;");                                        



                      
                        
                      const margin = 60;
                      const width = 500- 2 * margin;
                      const height = 500 - 2 * margin;    
                      
                      const chart = chartContainer.append('g')
                      .attr('transform', `translate(${margin}, ${margin})`);
                      
                      const yScale = d3.scaleLinear()
                      .range([0,height])
                      .domain([0, d3.max(sample[topic_id].map((s)=>s.probability))]); //margin
    
                      chart.append('g')
                      .call(d3.axisTop(yScale));
                      
                      const xScale = d3.scaleBand()
                      .range([0, width])
                      .domain(sample[topic_id].map((s) => s.term))
                      .padding(0.2)
                      
                      chart.append('g')
                      .attr('transform', `translate(0,0)`)
                      .call(d3.axisLeft(xScale));
                      
                      
                      const barGroups = chart.selectAll()
                      .data(sample[topic_id])
                      .enter()
                      .append('g')
                
                      barGroups
                      .append('rect')
                      .attr('class','bar')
                      .attr('x', (s) => 0)//.attr('x', (s) => xScale(s.term))
                      .attr('y', (s) => xScale(s.term)) //.attr('y', (s) => yScale(s.probability))
                      .attr('width', (s) => yScale(s.probability)) //(s) => height - yScale(s.probability)
                      .attr('height', xScale.bandwidth()) //xScale.bandwidth()
                      .on('mouseenter', function (actual, i) {
                        d3.selectAll('.probability')
                          .attr('opacity', 0)
                        
                          d3.select(this)
                          .transition()
                          .duration(100)
                          .attr('opacity', 0.8)
                          .attr('y', (a) => xScale(a.term))
                          .attr('height', xScale.bandwidth())

                          const y = yScale(actual.probability)
          
                          line = chart.append('line')
                            .attr('id', 'limit')
                            .attr('y1', 0) // 0
                            .attr('x1', y) // y
                            .attr('y2', height) // width
                            .attr('x2', y) // y
                  
                      })
                      .on('mouseleave', function () {
                        d3.selectAll('.probability')
                          .attr('opacity', 1)
                
                        d3.select(this)
                          .transition()
                          .duration(100)
                          .attr('opacity', 1)
                          .attr('y', (a) => xScale(a.term))
                          .attr('height', xScale.bandwidth())

                        chart.selectAll('#limit').remove()

                      })


                      chart.append('g')
                      .attr('class', 'grid')
                      .call(d3.axisTop()
                          .scale(yScale)
                          .tickSize(-width, 0, 0)
                          .tickFormat(''))
                    
                    
