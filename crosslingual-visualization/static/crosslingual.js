

    var svgContainer = d3.select("body").append("svg")
                                        .attr("width", 500)
                                        .attr("height", 500)
                                        .attr("style","outline:thin solid red;");

    var keywordsContainer = d3.select("body").append("svg")
                            .attr("width",500)
                            .attr("height",500)
                            .attr("style","outline:thin solid blue;");
                                    
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
                            alert("on click "+d.index);
                        });
                        
                        

    const textElems = svgContainer.append('circle')
                                .selectAll('text')
                                .data(jsonCircles['circles'])
                                .enter().append('text')
                                .text('prueba')
                                .attr('font-size',8)//font size
                                .attr('x', 100)//positions text towards the left of the center of the circle
                                .attr('y',40)                        


    




    document.getElementById("demo").innerHTML = 'Number of topics '+num_topics;
    
                                                