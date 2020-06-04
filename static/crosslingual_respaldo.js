
    ///////////////////////////////////
    ///////////////Pyldavis code

    // Set global margins used for everything

    mdswidth = 530,
    mdsheight = 450,
    barwidth = 450,
    barheight = 530,
    termwidth = 90, // width to add between two panels to display terms
    mdsarea = mdsheight * mdswidth;


    color1 = "#1f77b4", // baseline color for default topic circles and overall term frequencies
    color2 = "#d62728"; // 'highlight' color for selected topics and term-topic frequencies

    // proportion of area of MDS plot to which the sum of default topic circle areas is set
    var circle_prop = 0.25;
    var word_prop = 0.25;
    
    // current topic highlighted
    

    vis_state = {
        lambda: 1,
        topic: 1,
        term: ""
    };


    
    // opacity of topic circles:
    var base_opacity = 0.3,
    highlight_opacity = 0.6;
    // set the number of topics to global variable K:
    K = PreparedData_dict['mdsDat'].x.length;

    // R is the number of top relevant (or salient) words whose bars we display
    R = Math.min(PreparedData_dict['R'], 20);

    // get topic order
    var topic_order = PreparedData_dict['topic.order']

    // a (K x 5) matrix with columns x, y, topics, Freq, cluster (where x and y are locations for left panel)
    var mdsData = [];
    for (var i = 0; i < K; i++) {
        var obj = {};
        for (var key in PreparedData_dict['mdsDat']) {
            obj[key] = PreparedData_dict['mdsDat'][key][i];
        }
        mdsData.push(obj);
    }
    
    
                      
    // a huge matrix with 3 columns: Term, Topic, Freq, where Freq is all non-zero probabilities of topics given terms
    // for the terms that appear in the barcharts for this data
    var mdsData3 = [];
    for (var i = 0; i < PreparedData_dict['token.table'].Term.length; i++) {
        var obj = {};
        for (var key in PreparedData_dict['token.table']) {
            obj[key] = PreparedData_dict['token.table'][key][i];
        }
        mdsData3.push(obj);
    }

        
    

    // large data for the widths of bars in bar-charts. 6 columns: Term, logprob, loglift, Freq, Total, Category
    // Contains all possible terms for topics in (1, 2, ..., k) and lambda in the user-supplied grid of lambda values
    // which defaults to (0, 0.01, 0.02, ..., 0.99, 1).
    var lamData = [];
    for (var i = 0; i < PreparedData_dict['tinfo'].Term.length; i++) {
        var obj = {};
        for (var key in PreparedData_dict['tinfo']) {
            obj[key] = PreparedData_dict['tinfo'][key][i];
        }
        lamData.push(obj);
    }
    var dat3 = lamData.slice(0, R);


     // create linear scaling to pixels (and add some padding on outer region of scatterplot)
    var xrange = d3.extent(mdsData, function(d) {
         return d.x;
    }); //d3.extent returns min and max of an array
    var xdiff = xrange[1] - xrange[0],
        xpad = 0.15;
    var yrange = d3.extent(mdsData, function(d) {
        return d.y;
    });

    var ydiff = yrange[1] - yrange[0],
    ypad = 0.15;

    if (xdiff > ydiff) {
        var xScale = d3.scaleLinear()
                .range([0, mdswidth])
                .domain([xrange[0] - xpad * xdiff, xrange[1] + xpad * xdiff]);

        var yScale = d3.scaleLinear()
                .range([mdsheight, 0])
                .domain([yrange[0] - 0.5*(xdiff - ydiff) - ypad*xdiff, yrange[1] + 0.5*(xdiff - ydiff) + ypad*xdiff]);
    } else {
        var xScale = d3.scaleLinear()
                .range([0, mdswidth])
                .domain([xrange[0] - 0.5*(ydiff - xdiff) - xpad*ydiff, xrange[1] + 0.5*(ydiff - xdiff) + xpad*ydiff]);

        var yScale = d3.scaleLinear()
                .range([mdsheight, 0])
                .domain([yrange[0] - ypad * ydiff, yrange[1] + ypad * ydiff]);
    }
    

//http://hdnrnzk.me/2012/07/04/creating-a-bar-graph-using-d3js/

    var chartContainer = d3.select("#chartContainer").append("svg")
                                                     .attr("height", "100%")
                                                     .attr("width", "100%")

    var svgContainer = d3.select("#svgContainer").append("svg")
                                                 .attr("height", "100%")
                                                 .attr("width", "100%")
                                        
    svgContainer.append("text")
    .text("Intertopic Distance Map (via multidimensional scaling)")
    .attr("x", mdswidth/2 )
    .attr("y", 30)
    .style("font-size", "16px")
    .style("text-anchor", "middle");

    svgContainer.append("line") // draw x-axis
    .attr("x1", 0)
    .attr("x2", mdswidth)
    .attr("y1", mdsheight / 2)
    .attr("y2", mdsheight / 2)
    .attr("stroke", "gray")
    .attr("opacity", 0.3);


    svgContainer.append("text") // label x-axis
    .attr("x", 0)
    .attr("y", mdsheight/2 - 5)
    .text(PreparedData_dict['plot.opts'].xlab)
    .attr("fill", "gray");

    
    svgContainer.append("line") // draw y-axis
    .attr("x1", mdswidth / 2)
    .attr("x2", mdswidth / 2)
    .attr("y1", 0)
    .attr("y2", mdsheight)
    .attr("stroke", "gray")
    .attr("opacity", 0.3);
    svgContainer.append("text") // label y-axis
    .attr("x", mdswidth/2 + 5)
    .attr("y", 17)
    .text(PreparedData_dict['plot.opts'].ylab)
    .attr("fill", "gray");


    var points = svgContainer.selectAll("points")
                                .data(mdsData)
                                .enter();

                      // text to indicate topic
    points.append("text")
    .attr("class", "txt")
    .attr("x", function(d) {
        return (xScale(+d.x));
    })
    .attr("y", function(d) {
        return (yScale(+d.y) + 4);
    })
    .attr("stroke", "black")
    .attr("opacity", 1)
    .style("text-anchor", "middle")
    .style("font-size", "11px")
    .style("fontWeight", 100)
    .text(function(d) {
        return d.topics;
    });

    // draw circles
    points.append("circle")
        .attr("class", "dot")
        .style("opacity", function(d){
            if(d.topics == vis_state.topic){
                return highlight_opacity
            } else{
                return base_opacity
            }
        })
        .style("fill", function(d){
            if(d.topics == vis_state.topic){
                return color2
            } else{
                return color1
            }
        })
        .attr("r", function(d) {
            //return (rScaleMargin(+d.Freq));
            return (Math.sqrt((d.Freq/100)*mdswidth*mdsheight*circle_prop/Math.PI));
        })
        .attr("cx", function(d) {
            return (xScale(+d.x));
        })
        .attr("cy", function(d) {
            return (yScale(+d.y));
        })
        .attr("stroke", "black")
        .attr("id", function(d) {
            return (d.topics);
        })
        .on('mouseover', function (d) {
            real_topic_id = topic_order[d.topics-1]-1
            //selectTopic(real_topic_id)                 
            //topic_on(this)
                
                })

            
        .on('mouseout', function (d) {
            
              //  topic_off(this)
        })
        .on("click",function(d){
            
            real_topic_id = topic_order[d.topics-1]-1//Ojo! los topicos fueron ordenados de mayor a menor frecuencia, por eso que el orden cambia            
            var old_topic = document.getElementById("last_topic_selected").innerHTML;
            topic_off(document.getElementById(old_topic));
            document.getElementById("last_topic_selected").innerHTML = d.topics; //d.topics es el id del topico que aparece en la pantalla (no coincide con el orden del dataframe)                        
            selectTopic(real_topic_id)
            topic_on(this)
        });
        
    
    function topic_on(circle){
        circle.style.opacity = highlight_opacity;
        circle.style.fill = color2;
    }
        
    function topic_off(circle){
        circle.style.opacity = base_opacity;
        circle.style.fill=color1;
    }

    // new definitions based on fixing the sum of the areas of the default topic circles:
    var newSmall = Math.sqrt(0.02*mdsarea*circle_prop/Math.PI);
    var newMedium = Math.sqrt(0.05*mdsarea*circle_prop/Math.PI);
    var newLarge = Math.sqrt(0.10*mdsarea*circle_prop/Math.PI);
    var cx = 10 + newLarge,
        cx2 = cx + 1.5 * newLarge;
  
    var circleGuide = function(rSize, size) {
            svgContainer.append("circle")
            .attr('class', "circleGuide" + size)
            .attr('r', rSize)
            .attr('cx', cx)
            .attr('cy', mdsheight + rSize)
            .style('fill', 'none')
            .style('stroke-dasharray', '2 2')
            .style('stroke', '#999');
            svgContainer.append("line")
            .attr('class', "lineGuide" + size)
            .attr("x1", cx)
            .attr("x2", cx2)
            .attr("y1", mdsheight + 2 * rSize)
            .attr("y2", mdsheight + 2 * rSize)
            .style("stroke", "gray")
            .style("opacity", 0.3);
    };

    circleGuide(newSmall, "Small");
    circleGuide(newMedium, "Medium");
    circleGuide(newLarge, "Large");

    var defaultLabelSmall = "2%";
    var defaultLabelMedium = "5%";
    var defaultLabelLarge = "10%";

    
    svgContainer.append("text")
        .attr("x", 10)
        .attr("y", mdsheight - 10)
        .attr('class', "circleGuideTitle")
        .style("text-anchor", "left")
        .style("fontWeight", "bold")
        .text("Marginal topic distribution");
    svgContainer.append("text")
        .attr("x", cx2 + 10)
        .attr("y", mdsheight + 2 * newSmall)
        .attr('class', "circleGuideLabelSmall")
        .style("text-anchor", "start")
        .text(defaultLabelSmall);
    svgContainer.append("text")
        .attr("x", cx2 + 10)
        .attr("y", mdsheight + 2 * newMedium)
        .attr('class', "circleGuideLabelMedium")
        .style("text-anchor", "start")
        .text(defaultLabelMedium);
    svgContainer.append("text")
        .attr("x", cx2 + 10)
        .attr("y", mdsheight + 2 * newLarge)
        .attr('class', "circleGuideLabelLarge")
        .style("text-anchor", "start")
        .text(defaultLabelLarge);


  

    document.getElementById("demo").innerHTML = 'Number of topics '+num_topics;
    document.getElementById("last_topic_selected").innerHTML = vis_state.topic;
    //document.getElementById("toolbar_label").innerHTML = '0';
    //tool bar
    
    //d3.select('#editbutton')        
    //.on('click', selectTopic("funciona") );                                                


    
    //console.log(topKeywordsDict[topic_id])

    //console.log(topKeywordsDict[topic_id].map((s)=>s.probability))
    //keywords barchart
    console.log(PreparedData_dict)



    
    function updateTopKeywords(topic_id){
               

        chartContainer.select("g").remove();
          
        const margin = 60;
        const width = 500- 2 * margin;
        const height = 500 - 2 * margin;    
        
        const chart = chartContainer.append('g')
        .attr('transform', `translate(${margin}, ${margin})`);
        
        const yScale = d3.scaleLinear()
        .range([0,height])
        .domain([0, d3.max(topKeywordsDict[topic_id].map((s)=>s.probability))]); //margin

        chart.append('g')
        .call(d3.axisTop(yScale));
        
        const xScale = d3.scaleBand()
        .range([0, width])
        .domain(topKeywordsDict[topic_id].map((s) => s.term))
        .padding(0.2)
        
        chart.append('g')
        .attr('transform', `translate(0,0)`)
        .call(d3.axisLeft(xScale));
        
        
        const barGroups = chart.selectAll()
        .data(topKeywordsDict[topic_id])
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

    }

    //initialize
    topic_id = 0
    selectTopic(topic_id)
    //console.log(relevantDocumentsDict[topic_id].map((s)=>s.topic_perc_contrib))
    //console.log(relevantDocumentsDict[topic_id].map((s)=>s.text))
    
    

    function selectTopic(label){
      document.getElementById("toolbar_label").innerHTML = label;    
      
      updateTopKeywords(label)
      updateRelevantDocuments(label)

  }
  //Show relevant documents
  /*$(function(){
    $('#table').bootstrapTable({
        data: relevantDocumentsDict[0]
    });
  });*/

  function updateRelevantDocuments(topic_id){
    
    $('.tableRelevantDocumentsClass').bootstrapTable("destroy");
    $('.tableRelevantDocumentsClass').bootstrapTable({
      data: relevantDocumentsDict[topic_id]
    });
  }    


                    
                    
