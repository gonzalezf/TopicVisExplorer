/* Original code taken from https://github.com/cpsievert/LDAvis */
/* Copyright 2013, AT&T Intellectual Property */
/* MIT Licence */

'use strict';
var LDAvis = function(to_select, data_or_file_name) {

        // This section sets up the logic for event handling
    var vis_state = {
            lambda: 0.6,
            min_value_filtering:-1.0,
            max_value_filtering: 1.0,
            lambda_lambda_topic_similarity:0.8, //que tanta info tiene vector top keywords y que tanta info tiene vector top relevant documents
            lambda_topic_similarity:0.0, //este filtra las lineas (el ancho que de similitud). If this value is very low, it is going to show all the paths. 
            topic: 1,
            term: ""
        };

    // Set up a few 'global' variables to hold the data:
    var K, // number of topics
        mdsData, // (x,y) locations and topic proportions
        mdsData3, // topic proportions for all terms in the viz
        lamData, // all terms that are among the top-R most relevant for all topics, lambda values
        lambda = {
            old: 0.6,
            current: 0.6
        },
        
        lambda_lambda_topic_similarity = {  //pondera la importancia de vector documento y vector top relevant keywords
            old: 0.8,
            current: 0.8
        },

        lambda_topic_similarity = { //mide la similitud de los paths en el sankey diagram
            old: 0.9,
            current: 0.9

        },
        color1 = "#1f77b4", // baseline color for default topic circles and overall term frequencies
        color2 = "#d62728"; // 'highlight' color for selected topics and term-topic frequencies

    // Set the duration of each half of the transition:
    var duration = 750;

    // Set global margins used for everything
    var margin = {
        top: 30,
        right: 30,
        bottom: 70,
        left: 30
    },
        mdswidth = 530, //530 //LA IDEA ES ELIMINAR MDSWIFTH Y MEDSHEIGHT. ESTO DEBE SER RESPONSIVE!!
        mdsheight = 530,
        barwidth = 530, //LA IDEA ES ELIMINAR TODO ESTO QUE ES BAR WIDTH, BARHEIGHT, ETC.
        barheight = 530,
        termwidth = 90; // width to add between two panels to display terms
        
    // controls how big the maximum circle can be
    // doesn't depend on data, only on mds width and height:
    var rMax = 60;

    // proportion of area of MDS plot to which the sum of default topic circle areas is set
    var circle_prop = 0.20;
    

    // opacity of topic circles:
    var base_opacity = 0.2,
        highlight_opacity = 0.6;

    // lambda selection names are specific to *this* vis
    
    var lambda_select = to_select + "-lambda";

    // get rid of the # in the to_select (useful) for setting ID values
    var visID = to_select.replace("#", "");
    var topicID = visID + "-topic";
    var lambdaID = visID + "-lambda";
    var lambdaIDRightPanel =  lambdaID+"RightPanel"; 



    var termID = visID + "-term";
    
    var topicEdit = topicID+"-edit";
    var topicEdit2 = topicID+"-edit_2";
    var topicSplit = topicID+"-split";
    var topicMerge = topicID+"-merge";

    

    var leftPanelID = visID + "-leftpanel";
    var barFreqsID = "barplot_1";
    var barFreqsID_2 = "barplot_2"
    var topID = visID + "-top";
    var lambdaInputID = visID + "-lambdaInput";
    //var lambdaZeroID = visID + "-lambdaZero";
    var lambdaZeroID = "relevanceSliderTexto";

    var sliderDivID = "RelevanceSliderContenedor";
    var lambdaLabelID = "RelevanceSliderLabel";

    var min_target_node_value = Infinity;

    var number_terms_sankey = 20
    var number_terms_mdsplot = 20

    //esto se ocupa en la comparación de un corpus
    var topic_id_model_1 = -1
    var topic_id_model_2 = -1

    /////////////////////////
    ////topic mergin
    var merging_topic_1 = -1
    var merging_topic_2 = -1

    var splitting_topic = -1

    var hacer_merge = false

    var last_clicked_model_1 = -1
    var last_clicked_model_2 = -1


    //rename topic variables
    var renameTopicId = -1
    var name_topics_circles = {}
    var name_topics_sankey = {}

    var isSettingInitial = true

    var number_top_keywords_name = 3

    
    var real_last_clicked_sankey_model_1
    var real_last_clicked_sankey_model_2

    var BarPlotPanelDivId = 'BarPlotPanelDiv'


    //topic similarity metric proposed

    var sliderDivIDLambdaTopicSimilarity = "sliderDivLambdaTopicSimilarity"
    //to_select = BarPlotPanelDivId
    
    
    

    // sort array according to a specified object key name
    // Note that default is decreasing sort, set decreasing = -1 for increasing
    // adpated from http://stackoverflow.com/questions/16648076/sort-array-on-key-value
    function fancysort(key_name, decreasing) {
        decreasing = (typeof decreasing === "undefined") ? 1 : decreasing;
        return function(a, b) {
            if (a[key_name] < b[key_name])
                return 1 * decreasing;
            if (a[key_name] > b[key_name])
                return -1 * decreasing;
            return 0;
        };
    }
    

    function visualize(data) {

        // set the number of topics to global variable K:
        //console.log("ESTA ES LA DATA QUE RECIBE", data)
        
        K = data['mdsDat'].x.length;

        // R is the number of top relevant (or salient) words whose bars we display
        var R = Math.min(data['R'], 20);

        // a (K x 5) matrix with columns x, y, topics, Freq, cluster (where x and y are locations for left panel)
        mdsData = [];
        for (var i = 0; i < K; i++) {
            var obj = {};
            for (var key in data['mdsDat']) {
                obj[key] = data['mdsDat'][key][i];
            }
            mdsData.push(obj);
        }

        // a huge matrix with 3 columns: Term, Topic, Freq, where Freq is all non-zero probabilities of topics given terms
        // for the terms that appear in the barcharts for this data
        mdsData3 = [];
        for (var i = 0; i < data['token.table'].Term.length; i++) {
            var obj = {};
            for (var key in data['token.table']) {
                obj[key] = data['token.table'][key][i];
            }
            mdsData3.push(obj);
        }

    
        // large data for the widths of bars in bar-charts. 6 columns: Term, logprob, loglift, Freq, Total, Category
        // Contains all possible terms for topics in (1, 2, ..., k) and lambda in the user-supplied grid of lambda values
        // which defaults to (0, 0.01, 0.02, ..., 0.99, 1).
        lamData = [];
        for (var i = 0; i < data['tinfo'].Term.length; i++) {
            var obj = {};
            for (var key in data['tinfo']) {
                obj[key] = data['tinfo'][key][i];
            }
            lamData.push(obj);
        }
        
        var dat3 = lamData.slice(0, R);


        var points2 = d3.select("#name_topics")
                    .data(mdsData)
                    .enter();

        points2.append("circle")
                .attr("class", "dot")
                .style("opacity", 0.2)
                .style("fill", color1)
                .attr("r", function(d) {
                    //return (rScaleMargin(+d.Freq));
                    return 0;
                })
                .attr("cx", function(d) {
                    //console.log("D.X", +d.x, new_positions[topic_order[d.topics-1]-1][0])
                    //return (xScale(+d.x));
                    return 0;
                })
                .attr("cy", function(d) {
                    //return (yScale(+d.y));
                    return 0;
                })
                .attr("stroke", "black")
                .attr("id", function(d) {
                    var dat2 = lamData.filter(function(e) {
                        return e.Category == "Topic"+d.topics;
                    });
                    

                    // define relevance:
                    for (var i = 0; i < dat2.length; i++) {
                        dat2[i].relevance = lambda.current * dat2[i].logprob +
                            (1 - lambda.current) * dat2[i].loglift;
                    }
        
                    // sort by relevance:
                    dat2.sort(fancysort("relevance"));

                    // truncate to the top R tokens:
                    var top_terms = dat2.slice(0, number_top_keywords_name);
                    //console.log("ESTOS SON LOS TOP TERMS", top_terms)
                    var name_string = '';

                    for (var i=0; i < top_terms.length; i++){
                        //console.log(top_terms[i].Term)
                        //name_string.concat(top_terms[i].Term);
                        name_string += top_terms[i].Term+" "
                    }
                    //console.log("este es el final string", name_string)
                    //name_topics_circles[topicID + d.topics] = d.topics //Here, we need to change the default topic name. 
                    name_topics_circles[topicID + d.topics] = name_string //Here, we need to change the default topic name. 

                    return (topicID + d.topics);
                })
        
    

        // Create the topic input & lambda slider forms. Inspired from:
        // http://bl.ocks.org/d3noob/10632804
        // http://bl.ocks.org/d3noob/10633704
        init_forms(topicID, lambdaID);

        // When the value of lambda changes, update the visualization
            
        d3.select("#"+lambdaID)
            .on("mouseup", function() {
                console.log("hice click en esti", "#"+lambdaID)
                //lambda_select = "#"+lambdaID
                
                // store the previous lambda value
                
                lambda.old = lambda.current;
                
                lambda.current = document.getElementById(lambdaID).value;
                vis_state.lambda = +this.value;
                // adjust the text on the range slider
                d3.select("#"+lambdaID).property("value", vis_state.lambda);
                d3.select("#"+lambdaID + "-value").text(vis_state.lambda);
                // transition the order of the bars
                var increased = lambda.old < vis_state.lambda;
                
                if (vis_state.topic > 0){
                    
                    reorder_bars_new(increased, "left");
                } 
                // store the current lambda value
                //state_save(true);
                document.getElementById(lambdaID).value = vis_state.lambda;
            });

        d3.select("#"+lambdaIDRightPanel)
            .on("mouseup", function() {
                console.log("hice click en esti", "#"+lambdaIDRightPanel)
                //lambda_select = "#"+lambdaID
                
                // store the previous lambda value
                
                lambda.old = lambda.current;
                
                lambda.current = document.getElementById(lambdaIDRightPanel).value;
                vis_state.lambda = +this.value;
                // adjust the text on the range slider
                d3.select("#"+lambdaIDRightPanel).property("value", vis_state.lambda);
                d3.select("#"+lambdaIDRightPanel + "-value").text(vis_state.lambda);
                // transition the order of the bars
                var increased = lambda.old < vis_state.lambda;
                
                if (vis_state.topic > 0){
                    
                    reorder_bars_new(increased, "right");
                } 
                // store the current lambda value
                //state_save(true);
                document.getElementById(lambdaIDRightPanel).value = vis_state.lambda;
            });


        function get_name_node_sankey(graph, threshold){
            graph.links.filter(function(el){
                if(el.value >=threshold){
                    if(el.target.node ==  undefined){
                        if(el.target<=min_target_node_value){
                            min_target_node_value=el.target
                            }
                        }
                    else{
                        if(el.target.node<=min_target_node_value){
                            min_target_node_value=el.target.node
                            }
                        }
                    }
                }
            );

            var nodes_filtered_set = new Set();

        
            graph.nodes.filter(function(d){
                if(!(nodes_filtered_set.has(d.node))){
                    
                    if(d.node >= min_target_node_value){
                        // pertenece al modelo de corpus 2
                        var topic_id_in_model = d.node-min_target_node_value
                        var real_topic_id = topic_order_2[topic_id_in_model]-1
                    
                        lamData = [];
                        for (var i = 0; i < jsonData_2['tinfo'].Term.length; i++) {
                            var obj = {};
                            for (var key in jsonData_2['tinfo']) {
                                obj[key] = jsonData_2['tinfo'][key][i];
                            }
                            lamData.push(obj);
                        }


                    }
                    else{
                        var topic_id_in_model = d.node                                                
                        lamData = [];
                        for (var i = 0; i < jsonData['tinfo'].Term.length; i++) {
                            var obj = {};
                            for (var key in jsonData['tinfo']) {
                                obj[key] = jsonData['tinfo'][key][i];
                            }
                            lamData.push(obj);
                        }
        
                    }

                    var dat2 = lamData.filter(function(e) {
                        if(d.node==-1){ 
                            return e.Category == "Default" //This are the most relevant terms from all the corpus. We are not using it!!!
                        }
                        else{
                            return e.Category == "Topic" + (d.node%min_target_node_value+1); // OJO! AQUI HAY UN +1, quizas hay que sacarlo y mejorar el codigo, esto esta medio mula
                        }
                        
                    });

        
                    // define relevance:
                    for (var i = 0; i < dat2.length; i++) {
                        dat2[i].relevance = lambda.current * dat2[i].logprob +
                            (1 - lambda.current) * dat2[i].loglift;
                    }
        
                    dat2.sort(fancysort("relevance"));
                
                    var top_terms = dat2.slice(0, number_top_keywords_name);
                    
                    var name_string = '';

                    for (var i=0; i < top_terms.length; i++){
                        name_string += top_terms[i].Term+" "
                    }
                    name_topics_sankey[topicID + d.node] = name_string
                    nodes_filtered_set.add(d.node);
                    return d;

                }
            });

            
        }   
        //Inspired by: https://bl.ocks.org/d3noob/013054e8d7807dff76247b81b0e29030
       function visualize_sankey(graph, threshold_min, threshold_max){

            var svgCentralSankeyDiv = d3.select("#CentralPanel").append("div")
            svgCentralSankeyDiv.attr("id", "svgCentralSankeyDiv")


            var margin = { top: 10, right: 10, bottom: 10, left: 10 } // ocupar estos margenes

            //get width, height according to client's window
            var bounds_svgCentralSankey = d3.selectAll('#svgCentralSankeyDiv').node().getBoundingClientRect();
            var user_width_sankey = bounds_svgCentralSankey.width - margin.left - margin.right;
            var user_height_sankey= bounds_svgCentralSankey.height - margin.top - margin.bottom;
            

            d3.selectAll('#svg_sankey').remove();
        
            //var min_target_node_value = Infinity;
            
            var nodes_filtered_set = new Set();

            
            var links_filtered =  graph.links.filter(function(el){

                if(threshold_min <= el.value.toFixed(2) && el.value.toFixed(2) <= threshold_max){
                    if(el.source.node ==  undefined){
                        nodes_filtered_set.add(el.source);
                        }
                    else{
                        nodes_filtered_set.add(el.source.node);
                        
                        }
                    if(el.target.node ==  undefined){
                        nodes_filtered_set.add(el.target);
                        if(el.target<=min_target_node_value){
                            min_target_node_value=el.target
                            }
                        }
                    else{
                        nodes_filtered_set.add(el.target.node);
                        if(el.target.node<=min_target_node_value){
                            min_target_node_value=el.target.node
                            }
                        }
                    return el.value
                    }
                }
            );
            
            
            var nodes_filtered = graph.nodes.filter(function(d){
                if(nodes_filtered_set.has(d.node)){
                    return d;
                }
            });

            var links_filtered =  graph.links.filter(function(el){
                return threshold_min <= el.value.toFixed(2) && el.value.toFixed(2) <= threshold_max;
                //return el.value >threshold;
                }
            );
            

            var units = "similarity";
            // set the dimensions and margins of the graph
            var margin = {top: 10, right: 10, bottom: 10, left: 10};
                //width = 3*mdswidth, //width = mdswidth - margin.left - margin.right,
                //height = 2*mdsheight - margin.top - margin.bottom;
                        // format variables
            
            var formatNumber = d3.format(",.2f"),    // two decimal places
                format = function(d) { return formatNumber(d) + " " + units; },
                color = d3.scaleOrdinal(d3.schemeAccent);
            


            var svg_sankey = d3.select("#svgCentralSankeyDiv").append("svg")// #CentralPanel
                .attr("width", "100%")
                .attr("height", "100%")
                .attr("id", "svg_sankey");//.attr("transform", "translate("+margin.left+","+ margin.top+")")
                
                /*.append("g")
                    .attr("transform", "translate(" + (termwidth+mdswidth+2*margin.left) + "," + (2*margin.top) + ")");*/

            
            var sankey = d3.sankey()
            .nodeWidth(36)
            .nodePadding(40)
            .size([user_width_sankey, user_height_sankey])
            //.size([mdswidth-margin.right, 2*mdsheight-margin.top]);

            var path = sankey.link();
            sankey
                .nodes(nodes_filtered)//.nodes(graph.nodes)
                .links(links_filtered)//.links(graph.links)
                .layout(32); //32
        
            // add in the links


            var link = svg_sankey.append("g").selectAll(".link")
                .data(links_filtered)//.data(graph.links)
            .enter().append("path")
                .filter(function(d){
                    return d.value;
                    //return d.value >= threshold;
                    //                    
                })
                .attr("class", "link")
                .attr("d", path)
                .style("stroke-width", function(d) { return Math.max(1, d.dy); })
                .sort(function(a, b) { return b.dy - a.dy; });

            
        // add the link titles
            link.append("title")
                .text(function(d) {
                    return d.source.name + " → " + 
                        d.target.name + "\n" + format(d.value); });
        
        // add in the nodes
            
            var node = svg_sankey.append("g").selectAll(".node")
                .data(nodes_filtered)//.data(graph.nodes)
                .enter().append("g")
                .attr("class", "node")
                .attr("transform", function(d) { 
                    return "translate(" + d.x + "," + d.y + ")"; })
                .on("click", function(d){
                    isSettingInitial = false
                    topic_on_sankey(d, min_target_node_value );
                    if(d.node>=min_target_node_value){
                        real_last_clicked_sankey_model_2 = d
                    }
                    else{
                        real_last_clicked_sankey_model_1 = d
                    }
                    
                })
                .on("mouseover", function(d) {
                    topic_on_sankey(d, min_target_node_value );

                })
                .on("mouseout", function(d) {


                    topic_on_sankey(real_last_clicked_sankey_model_1, min_target_node_value)
                    topic_on_sankey(real_last_clicked_sankey_model_2, min_target_node_value)

                   
                });
                

                
        
            // add the rectangles for the nodes
            node.append("rect")
                .attr("id", function(d){
                    return "node_"+d.node //que esta sea la id unica del nodo
                })
                .attr("height", function(d) { return d.dy; })
                .attr("width", sankey.nodeWidth())
                .style("fill", function(d) { 
                    if(d.node < min_target_node_value){
                        //return "blue";
                        //return "#1f77b4"; 
                        return "rgb(95,160,254)";
                        
                    }
                    else{
                        //return "red";
                        return "rgb(252,153,146)";
                        
                    }
                     
                })
                .style("stroke", function(d) { 
                    return d3.rgb(d.color).darker(2); })

                .append("title")
                    .text(function(d) { 
                                                
                        return d.name + "--\n" + format(d.value); })
                    
                .on("click", function(){
                    
                    alert("probando aqui", d.value);
                });
        
        // add in the title for the nodes
            node.append("text")
                .attr("x", -6)
                .attr("y", function(d) { return d.dy / 2; })
                .attr("dy", ".35em")
                .attr("text-anchor", "end")
                .attr("transform", null)
                .text(function(d){return name_topics_sankey[topicID + d.node] ;}) //.text(function(d) { return d.name; })
                .filter(function(d) { return d.x < user_width_sankey / 2; })
                .attr("x", 6 + sankey.nodeWidth())
                .attr("text-anchor", "start");
        
        // the function for moving the nodes
        
            /*
            function dragmove(d) {
                d3.select(this)
                    .attr("transform", 
                        "translate(" 
                            + d.x + "," 
                            + (d.y = Math.max(
                                0, Math.min(user_height_sankey - d.dy, d3.event.y))
                            ) + ")");
                sankey.relayout();
                link.attr("d", path);
                topic_on_sankey(real_last_clicked_sankey_model_1, min_target_node_value) //topic on on first topic of first model
                topic_on_sankey(real_last_clicked_sankey_model_2, min_target_node_value) //topic on first topic of second model
                }        
                
                */
            if(last_clicked_model_2!=-1){
                d3.select("#"+last_clicked_model_2).style("fill","rgb(237, 62, 50)")
            }
            if(last_clicked_model_1!=-1){
                d3.select("#"+last_clicked_model_1).style("fill","rgb(14, 91, 201)")
            }

            console.log("estoy en el setting initial", isSettingInitial)
            
            if(isSettingInitial){
                real_last_clicked_sankey_model_1 = nodes_filtered[0];
                real_last_clicked_sankey_model_2 = nodes_filtered[min_target_node_value];
                console.log("values", isSettingInitial, real_last_clicked_sankey_model_1, real_last_clicked_sankey_model_2, min_target_node_value);
                topic_on_sankey(real_last_clicked_sankey_model_1, min_target_node_value);
                topic_on_sankey(real_last_clicked_sankey_model_2, min_target_node_value);
            }
            

        }   

        function createMdsPlot(number, mdsData, lambda_lambda_topic_similarity){
            
            //if  previous mdsplot exists, remove it
            
            d3.selectAll('#svgMdsPlot').remove();





            //we need to append this to the central panel, not to the old svg
            //all draws of central panel must appear in this svg variable
            var svg = d3.select("#CentralPanel").append("svg")
                        .attr("width", "100%")
                        .attr("height", "95%")
                        .attr("id", "svgMdsPlot")
                        .style("background-color","lightblue")
             
            var margin = { top: 30, right: 30, bottom: 30, left: 30 } // ocupar estos margenes

            //get width, height according to client's window
            var bounds = d3.selectAll('#svgMdsPlot').node().getBoundingClientRect();
            //var user_width = bounds.width - margin.left - margin.right;
            //var user_height = bounds.height - margin.top - margin.bottom;
            var user_width = bounds.width; 
            var user_height = bounds.height;
            
            var mdsheight = user_height-margin.top-margin.bottom;
            var mdswidth = user_width-margin.left-margin.right;
            var mdsarea = mdsheight * mdswidth;





            // Create a group for the mds plot Bubbles visualization
            d3.selectAll('#'+leftPanelID).remove();

            var mdsplot = svg.append("g")
                .attr("id", leftPanelID) //now is central panel no leftpanel
                .attr("class", "points")
                .attr("transform", "translate("+margin.left+","+margin.top+")")
                

                //.attr("transform", "translate("+(mdswidth+margin.left+termwidth)+","+(2*margin.top +(mdsheight +margin.bottom  + 2 * rMax)*(number-1))+")");//.attr("transform", "translate(" + margin.left + "," + 2 * margin.top + ")");
                //should we need to translate this??

            mdsplot
                .append("rect")
                .attr("x", 0)
                .attr("y", 0)
                .attr("height", "100%")
                .attr("width", "100%")
                .attr("opacity", 0) //.style("fill", color1)
                .on("click", function() {
                });

            mdsplot.append("line") // draw x-axis
                .attr("x1", 0)
                .attr("x2", mdswidth)
                .attr("y1", mdsheight / 2)
                .attr("y2", mdsheight / 2)
                .attr("stroke", "gray")
                .attr("opacity", 0.3);
            mdsplot.append("text") // label x-axis
                .attr("x", 0)
                .attr("y", mdsheight/2 - 5)
                .text(data['plot.opts'].xlab)
                .attr("fill", "gray");

            mdsplot.append("line") // draw y-axis
                .attr("x1", mdswidth / 2)
                .attr("x2", mdswidth / 2)
                .attr("y1", 0)
                .attr("y2", mdsheight)
                .attr("stroke", "gray")
                .attr("opacity", 0.3);
            mdsplot.append("text") // label y-axis
                .attr("x", mdswidth/2 + 5)
                .attr("y", 7)
                .text(data['plot.opts'].ylab)
                .attr("fill", "gray");

            // new definitions based on fixing the sum of the areas of the default topic circles:
            
            var newSmall = Math.sqrt(0.02*mdsarea*circle_prop/Math.PI);
            var newMedium = Math.sqrt(0.05*mdsarea*circle_prop/Math.PI);
            var newLarge = Math.sqrt(0.10*mdsarea*circle_prop/Math.PI);
            var cx = 10 + newLarge,
                cx2 = cx + 1.5 * newLarge;

            // circle guide inspired from
            // http://www.nytimes.com/interactive/2012/02/13/us/politics/2013-budget-proposal-graphic.html?_r=0
            var circleGuide = function(rSize, size) {
                d3.select("#" + leftPanelID).append("circle")
                    .attr('class', "circleGuide" + size)
                    .attr('r', rSize)
                    .attr('cx', cx)
                    .attr('cy', 0.88*mdsheight + rSize)
                    .style('fill', 'none')
                    .style('stroke-dasharray', '2 2')
                    .style('stroke', '#999');
                d3.select("#" + leftPanelID).append("line")
                    .attr('class', "lineGuide" + size)
                    .attr("x1", cx)
                    .attr("x2", cx2)
                    .attr("y1", 0.88*mdsheight + 2 * rSize)
                    .attr("y2", 0.88*mdsheight + 2 * rSize)
                    .style("stroke", "gray")
                    .style("opacity", 0.3);
            };

            circleGuide(newSmall, "Small");
            circleGuide(newMedium, "Medium");
            circleGuide(newLarge, "Large");

            var defaultLabelSmall = "2%";
            var defaultLabelMedium = "5%";
            var defaultLabelLarge = "10%";


            d3.select("#" + leftPanelID).append("text")
                .attr("x", 10)
                .attr("y", 0.88*mdsheight-10)
                .attr('class', "circleGuideTitle")
                .style("text-anchor", "left")
                .style("fontWeight", "bold")
                .text("Marginal topic distribution");
            d3.select("#" + leftPanelID).append("text")
                .attr("x", cx2 + 10)
                .attr("y", 0.88*mdsheight + 2 * newSmall)
                .attr('class', "circleGuideLabelSmall")
                .style("text-anchor", "start")
                .text(defaultLabelSmall);
            d3.select("#" + leftPanelID).append("text")
                .attr("x", cx2 + 10)
                .attr("y", 0.88*mdsheight + 2 * newMedium)
                .attr('class', "circleGuideLabelMedium")
                .style("text-anchor", "start")
                .text(defaultLabelMedium);
            d3.select("#" + leftPanelID).append("text")
                .attr("x", cx2 + 10)
                .attr("y", 0.88*mdsheight + 2 * newLarge)
                .attr('class', "circleGuideLabelLarge")
                .style("text-anchor", "start")
                .text(defaultLabelLarge);
            

            // bind mdsData to the points in the left panel:
            
            var new_positions = new_circle_positions[lambda_lambda_topic_similarity]
            
            function getCol(matrix, col){
                var column = [];
                for(var i=0; i<matrix.length; i++){
                   column.push(matrix[i][col]);
                }
                return column; // return column data..
             }

            
            var points = mdsplot.selectAll("points")
                    .data(mdsData)
                    .enter();
            
            // create linear scaling to pixels (and add some padding on outer region of scatterplot)

            var xrange = d3.extent( getCol(new_positions, 0));
            /*
            var xrange = d3.extent(mdsData, function(d) {
                return d.x;
            }); //d3.extent returns min and max of an array
            */
            
            var xdiff = xrange[1] - xrange[0],
                xpad = 0.05;

            var yrange = d3.extent( getCol(new_positions, 1));
            /*
            var yrange = d3.extent(mdsData, function(d) {
                return d.y;
            });
            */
            var ydiff = yrange[1] - yrange[0],
                ypad = 0.05;
            //mdsheight=mdsheight/2 hay que revisar la escala, es como muy grande para este plano
            //mdswidth=mdswidth/2
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
            
            

            // draw circles
            points.append("circle")
                .attr("class", "dot")
                .style("opacity", 0.2)
                .style("fill", color1)
                .attr("r", function(d) {
                    //return (rScaleMargin(+d.Freq));
                    //return (Math.sqrt((d.Freq/100)*mdswidth*mdsheight*circle_prop/Math.PI));
                    return (Math.sqrt((mdsData[topic_order[d.topics-1]-1].Freq/100)*mdswidth*mdsheight*circle_prop/Math.PI)); //se hace esto porque el new_positions array no inclue 'Freq', en cambioe el MdsDATA YA LO OBTIENE
                    
                })
                .attr("cx", function(d) {
                    //return (xScale(+d.x));
                    return (xScale(+new_positions[topic_order[d.topics-1]-1][0])); //new position topic similarity metric proposed
                })
                .attr("cy", function(d) {
                    //return (yScale(+d.y));
                    return (yScale(+new_positions[topic_order[d.topics-1]-1][1]));
                })
                .attr("stroke", "black")
                .attr("id", function(d) {                    
                    return (topicID + d.topics);
                })
                .on("click", function(d) {
                    
                    // prevent click event defined on the div container from firing
                    // http://bl.ocks.org/jasondavies/3186840
                    d3.event.stopPropagation();
                    var old_topic = topicID + vis_state.topic;
                    if (vis_state.topic > 0 && old_topic != this.id) {
                        topic_off(document.getElementById(old_topic));
                    }
                    // make sure topic input box value and fragment reflects clicked selection
                    vis_state.topic = d.topics;
                    

                    splitting_topic= vis_state.topic
                    
                    document.getElementById("renameTopicId").value = name_topics_circles[topicID + d.topics]
                    $('#idTopic').html(topicID + d.topics);
                    //hacer merge de topicos
                    if(hacer_merge==false){
                        merging_topic_1= vis_state.topic
                    }                    
                    else{
                        merging_topic_2 = vis_state.topic
                    }
                    if(hacer_merge==true){
                        //preguntarle al usuario si quiere hacer este merge
                        $('.merging_topic_1').html(merging_topic_1);
                        $('.merging_topic_2').html(merging_topic_2);
                        $('#MergeModal_2').modal(); 
                    }

                    
                    topic_on(this);                
                })
                .on("mouseover", function(d) {
                    var old_topic = topicID + vis_state.topic;
                    if (vis_state.topic > 0 && old_topic != this.id) {
                        topic_off(document.getElementById(old_topic));
                    }
                    topic_on(this);
                })
                .on("mouseout", function(d) {
                    if (vis_state.topic != d.topics) topic_off(this);
                    if (vis_state.topic > 0) topic_on(document.getElementById(topicID + vis_state.topic));
                });

            // text to indicate topic
            points.append("text")
            .attr("class", "txt")
            .attr("x", function(d) {
                
                return (xScale(+new_positions[topic_order[d.topics-1]-1][0]));

            })
            .attr("y", function(d) {
                //return (yScale(+d.y) + 4);
                return (yScale(+new_positions[topic_order[d.topics-1]-1][1]));
            })
            .attr("stroke", "black")
            .attr("opacity", 1)
            .style("text-anchor", "middle")
            .style("font-size", "11px")
            .style("fontWeight", 100)
            .text(function(d) {
                return name_topics_circles[topicID + d.topics];
                
            });

                        
            svg.append("text")
                .text("Intertopic Distance Map (via multidimensional scaling)")
                .attr("x", mdswidth/2 + margin.left)
                .attr("y", 20)
                .attr("id","textMdsPlot")
                .style("font-size", "16px")
                .style("text-anchor", "middle");


        }
               
       if( type_vis === 1){

            createMdsPlot(1, mdsData, lambda_lambda_topic_similarity.current)
            

            createBarPlot("#BarPlotPanelDiv", dat3, barFreqsID,"bar-totals", "terms", "bubble-tool", "xaxis", R) //esto crea el bar plot por primera vez. 
            //dejar la tabla en una buena posicion
            d3.selectAll('#tableRelevantDocumentsClass_Model1').attr("transform", "translate("  +0 + "," +0+ ")")

            //hacer la configuracion inicial para cuando se quiera hacer el merge
            splitting_topic= vis_state.topic // es 1 by default
            
            document.getElementById("renameTopicId").value = name_topics_circles[topicID + vis_state.topic]
            $('#idTopic').html(topicID + vis_state.topic);
            topic_on(document.getElementById(topicID+vis_state.topic))
        
       }

       if(type_vis === 2){
        
        
           get_name_node_sankey(matrix_sankey[lambda_lambda_topic_similarity.current], vis_state.lambda_topic_similarity)
        
            // Add barplot into the left panel 
            createBarPlot("#BarPlotPanelDiv", dat3, barFreqsID,"bar-totals", "terms", "bubble-tool", "xaxis", number_terms_sankey) //esto crea el bar plot por primera vez. 

            // Add barplot into the right panel
            createBarPlot("#DocumentsPanel", dat3, barFreqsID_2,"bar-totals_2", "terms_2", "bubble-tool_2", "xaxis_2", number_terms_sankey) //hay que modificar la altura aqui en funcion del alto de las barras

            // Add documents into the left panel. 
           var RelevantDocumentsTableDiv = document.createElement("div");
           RelevantDocumentsTableDiv.setAttribute("id", "RelevantDocumentsTableDiv");
           RelevantDocumentsTableDiv.setAttribute("class", "RelevantDocumentsSankeyDiagram");
           document.getElementById("BarPlotPanelDiv").appendChild(RelevantDocumentsTableDiv) 
           const  div = document.getElementById('RelevantDocumentsTableDiv');
           div.insertAdjacentHTML('afterbegin', '<table  id="tableRelevantDocumentsClass_Model1" class="table table-hover"> <thead> <tr> <th class="text-center" data-field="topic_perc_contrib" scope="col">%</th> <th class="text-center" data-field="text" scope="col">Tweet</th> </tr> </thead> </table>');


           // Add documents into the right panel. 
           var RelevantDocumentsTableDiv_2 = document.createElement("div");
           RelevantDocumentsTableDiv_2.setAttribute("id", "RelevantDocumentsTableDiv_2");
           RelevantDocumentsTableDiv_2.setAttribute("class", "RelevantDocumentsSankeyDiagram");
           document.getElementById("DocumentsPanel").appendChild(RelevantDocumentsTableDiv_2) 
           const  div_2 = document.getElementById('RelevantDocumentsTableDiv_2');
           div_2.insertAdjacentHTML('afterbegin', '<table  id="tableRelevantDocumentsClass_Model2" class="table table-hover"> <thead> <tr> <th class="text-center" data-field="topic_perc_contrib" scope="col">%</th> <th class="text-center" data-field="text" scope="col">Tweet</th> </tr> </thead> </table>');

           //Añadir este barplot despues
           //createBarPlot(dat3, barFreqsID_2,"bar-totals_2", "terms_2", "bubble-tool_2", "xaxis_2", (8* margin.top + mdsheight), number_terms_sankey) //hay que modificar la altura aqui en funcion del alto de las barras
           visualize_sankey(matrix_sankey[lambda_lambda_topic_similarity.current], vis_state.min_value_filtering, vis_state.max_value_filtering)
           console.log("revisar estos values", isSettingInitial, real_last_clicked_sankey_model_1, real_last_clicked_sankey_model_2, min_target_node_value)


         


           /*
                       //It's the first time that this function is called, we are going to visualize the first topic of each model.
            if(isSettingInitial){
                console.log("estoy en el setting initial")
                real_last_clicked_sankey_model_1 = nodes_filtered[0]
                real_last_clicked_sankey_model_2 = nodes_filtered[min_target_node_value]
                console.log("values", isSettingInitial, real_last_clicked_sankey_model_1, real_last_clicked_sankey_model_2, min_target_node_value)
                topic_on_sankey(real_last_clicked_sankey_model_1, min_target_node_value) //topic on on first topic of first model
                topic_on_sankey(real_last_clicked_sankey_model_2, min_target_node_value) //topic on first topic of second model
                isSettingInitial = false
            }
            */

       }
       
       
        // establish layout and vars for bar chart
               




        function createBarPlot(to_select, dat3, barFreqsID_actual, bar_totals_actual, terms_actual,  bubble_tool, xaxis_class, number_terms){
            
            var height_bar = 20
            
            var svg = d3.select(to_select).append("svg") //BarPlotPanelDiv
            .attr("width", "100%")
            .attr("height", "50%");
            

            var bounds_barplot = svg.node().getBoundingClientRect();
            

            barheight = bounds_barplot.height - 1.5*termwidth
            barwidth = bounds_barplot.width - 1.5*termwidth
        

        
            var barDefault2 = dat3.filter(function(d) {
                return d.Category == "Default";
            });
            
            
            
            var y = d3.scaleBand()
                    .domain(barDefault2.map(function(d) {
                        return d.Term;
                    }))
                    .rangeRound([0, barheight])
                    .padding(0.15);
       
            var x = d3.scaleLinear()
                    .domain([1, d3.max(barDefault2, function(d) {
                        return d.Total;
                    })])
                    .range([0, barwidth])
                    .nice();
            var yAxis = d3.axisLeft(y);
            
            // Add a group for the bar chart
            var chart = svg.append("g")
                    .attr("transform", "translate("  +(termwidth) + "," +2*height_bar+ ")") //.attr("transform", "translate("  +(mdswidth + margin.left + termwidth) + "," +height_bar+ ")")
                    .attr("id", barFreqsID_actual)
                    .attr("class", "BarPlotClass");
            
            // bar chart legend/guide:
            /* I will delete this for now. We need to figure out a way to explain the information to the user
            mdsheight = 400
            */
            if(type_vis == 1){

                var legend_svg = d3.select(to_select).append("svg") //BarPlotPanelDiv
                .attr("width", "100%")
                .attr("id", "legend_svg")
                
                mdsheight = 0
                var barguide = {"width": 100, "height": 15};
                d3.select("#legend_svg").append("rect")
                    .attr("x", 0)
                    .attr("y", mdsheight + 10)
                    .attr("height", barguide.height)
                    .attr("width", barguide.width)
                    .style("fill", color1)
                    .attr("opacity", 0.4);
                d3.select("#legend_svg").append("text")
                    .attr("x", barguide.width + 5)
                    .attr("y", mdsheight + 10 + barguide.height/2)
                    .style("dominant-baseline", "middle")
                    .text("Overall term frequency");
                
                d3.select("#legend_svg").append("rect")
                    .attr("x", 0)
                    .attr("y", mdsheight + 10 + barguide.height + 5)
                    .attr("height", barguide.height)
                    .attr("width", barguide.width/2)
                    .style("fill", color2)
                    .attr("opacity", 0.8);
                d3.select("#legend_svg").append("text")
                    .attr("x", barguide.width/2 + 5)
                    .attr("y", mdsheight + 10 + (3/2)*barguide.height + 5)
                    .style("dominant-baseline", "middle")
                    .text("Estimated term frequency within the selected topic");
                
                
                
                d3.select("#legend_svg")
                    .append("a")
                    .attr("xlink:href", "http://vis.stanford.edu/files/2012-Termite-AVI.pdf")
                    .attr("target", "_blank")
                    .append("text")
                    .attr("x", 0)
                    .attr("y", mdsheight + 10 + (6/2)*barguide.height + 5)
                    .style("dominant-baseline", "middle")
                    .text("1. saliency(term w) = frequency(w) * [sum_t p(t | w) * log(p(t | w)/p(t))] for topics t; see Chuang et. al (2012)");
                d3.select("#legend_svg")
                    .append("a")
                    .attr("xlink:href", "http://nlp.stanford.edu/events/illvi2014/papers/sievert-illvi2014.pdf")
                    .attr("target", "_blank")
                    .append("text")
                    .attr("x", 0)
                    .attr("y", mdsheight + 10 + (8/2)*barguide.height + 5)
                    .style("dominant-baseline", "middle")
                    .text("2. relevance(term w | topic t) = \u03BB * p(w | t) + (1 - \u03BB) * p(w | t)/p(w); see Sievert & Shirley (2014)");
            }
            
            // Bind 'default' data to 'default' bar chart
            var basebars = chart.selectAll(to_select + " ."+bar_totals_actual)
                    .data(barDefault2)
                    .enter();
            
            // Draw the gray background bars defining the overall frequency of each word
            basebars
                .append("rect")
                .attr("class", bar_totals_actual)
                .attr("x", 0)
                .attr("y", function(d) {
                    return y(d.Term);
                })
                .attr("height", y.bandwidth())
                .attr("width", function(d) {
                    return x(d.Total);
                })
                .style("fill", color1)
                .attr("opacity", 0.4);
            
            // Add word labels to the side of each bar
            basebars
                .append("text")
                .attr("x", -5)
                .attr("class", terms_actual)
                .attr("y", function(d) {
                    return y(d.Term) + 12;
                })
                .attr("cursor", "pointer")
                .attr("id", function(d) {
                    return (termID + d.Term);
                })
                .style("text-anchor", "end") // right align text - use 'middle' for center alignment
                .text(function(d) {
                    return d.Term;
                })
                .on("mouseover", function() {
                    
                })
                .on("mouseout", function() {
                    vis_state.term = "";
                    
                });
            
            
            var title = chart.append("text")
                    .attr("x", 0) //mdswidth+margin.left+termwidth+(barwidth/2)
                    .attr("y", 0)
                    .attr("class", bubble_tool) //  set class so we can remove it when highlight_off is called
                    .style("text-anchor", "middle")
                    .style("font-size", "16px")
                    .text("Top Most Salient Terms");
            
            title.append("tspan")
                .attr("baseline-shift", "super")
                .attr("font-size", "12px")
                .text("(1)");
            
            // barchart axis adapted from http://bl.ocks.org/mbostock/1166403
            var xAxis = d3.axisTop().scale(x).tickSize(-barheight).ticks(6);
            
            
            
            chart.append("g")
                .attr("class", xaxis_class)
                .call(xAxis);
    
        }
        
        // dynamically create the topic and lambda input forms at the top of the page:
        function init_forms(topicID, lambdaID) {
            


            //div que contiene todo el panel izquierdo
            if(type_vis == 2){
                var svgRightPanel = d3.select("#DocumentsPanel").append("div")
                svgRightPanel.attr("id", "svgRightPanel")

                var topicDivRightPanel = document.createElement("div");
                topicDivRightPanel.setAttribute("id", "topic_name_and_buttons_div_right_panel")
                document.getElementById("svgRightPanel").appendChild(topicDivRightPanel) ////topicDiv.setAttribute("style", "width:100%; height:5%; background-color: red")

                var topic_title_right_panel= document.createElement("span"); 
                topic_title_right_panel.innerText = "Topic: ";
                topicDivRightPanel.appendChild(topic_title_right_panel); 

                var topic_name_selected_2 = document.createElement("span")
                topic_name_selected_2.innerText = ""
                topic_name_selected_2.setAttribute("id", "topic_name_selected_2")
                topicDivRightPanel.appendChild(topic_name_selected_2); 

                var merge_right_panel = document.createElement("button");
                merge_right_panel.setAttribute("id", topicMerge+"rightPanel");
                merge_right_panel.setAttribute("class", "btn btn-primary btnTopic")
                merge_right_panel.innerHTML = "Merge";
                topicDivRightPanel.appendChild(merge_right_panel);

                var split_rigth_panel = document.createElement("button");
                split_rigth_panel.setAttribute("id", topicSplit+"rightPanel");
                split_rigth_panel.setAttribute("class", "btn btn-primary btnTopic")
                split_rigth_panel.innerHTML = "Split";
                topicDivRightPanel.appendChild(split_rigth_panel);

                var edit2 = document.createElement("button");
                edit2.setAttribute("id", topicEdit2);
                edit2.setAttribute("class", "btn btn-primary btnTopic");
                edit2.innerHTML = "Rename";
                topicDivRightPanel.appendChild(edit2);
                d3.select("#"+topicEdit2)
                .on("click", function() {
                    $('#renameTopic2').modal(); 
                });

                
                //add relevance slider into the right panel. 
                var inputDivRightPanel = document.createElement("div");
                inputDivRightPanel.setAttribute("id", "BarPlotDivRightPanel");
                document.getElementById("DocumentsPanel").appendChild(inputDivRightPanel)  //document.getElementById(visID).appendChild(inputDiv); //creo que esto debiera estar unido al svg mejor

                //Div for relevance slider. 
                var lambdaDivRightPanel = document.createElement("div");
                lambdaDivRightPanel.setAttribute("id", "relevanceSliderDivRightPanel");
                lambdaDivRightPanel.setAttribute("class", "RowDiv");
                inputDivRightPanel.appendChild(lambdaDivRightPanel);

                var sliderDivRightPanel = document.createElement("div");
                sliderDivRightPanel.setAttribute("id", "RelevanceSliderContenedorRightPanel");
                sliderDivRightPanel.setAttribute("class", "ColumnDiv");
                lambdaDivRightPanel.appendChild(sliderDivRightPanel);

                var lambdaInputRightPanel = document.createElement("input");
                lambdaInputRightPanel.setAttribute("class", "SliderInput")
                lambdaInputRightPanel.type = "range";
                lambdaInputRightPanel.min = 0;
                lambdaInputRightPanel.max = 1;
                lambdaInputRightPanel.step = data['lambda.step'];
                lambdaInputRightPanel.value = vis_state.lambda;
                lambdaInputRightPanel.id = lambdaID+"RightPanel";
                lambdaInputRightPanel.setAttribute("list", "ticks"); 
                sliderDivRightPanel.appendChild(lambdaInputRightPanel);

                var lambdaLabelRightPanel = document.createElement("label");
                lambdaLabelRightPanel.setAttribute("id", lambdaLabelID+"RightPanel");
                lambdaLabelRightPanel.setAttribute("class", "ColumnDiv");
                lambdaLabelRightPanel.setAttribute("for", lambdaID+"RightPanel");
                lambdaLabelRightPanel.innerHTML = "Relevance score: &#955 = <span id='" + lambdaID+"RightPanel" + "-value'>" + vis_state.lambda + "</span>";
                lambdaDivRightPanel.appendChild(lambdaLabelRightPanel);

                // Create the svg to contain the slider scale:
                var scaleContainerRightPanel = d3.select("#" + "RelevanceSliderContenedorRightPanel").append("svg")
                        .attr("id", "scaleContainerRightPanel");

                var bounds_scaleContainer_right_panel = scaleContainerRightPanel.node().getBoundingClientRect();

                var sliderScalerRightPanel = d3.scaleLinear()
                        .domain([0, 1])
                        .range([7.5, bounds_scaleContainer_right_panel.width-11])  //Now it is responsive
                        .nice();



                var sliderAxisRightPanel = d3.axisBottom(sliderScalerRightPanel).tickSize(10).ticks(6);
                        
                // group to contain the elements of the slider axis:
                var sliderAxisGroupRightPanel = scaleContainerRightPanel.append("g")
                        .attr("class", "slideraxis")
                        .attr("margin-top", "-10px")
                        .call(sliderAxisRightPanel);




     
            }
            var svgLeftPanel = d3.select("#BarPlotPanel").append("div")
            svgLeftPanel.attr("id", BarPlotPanelDivId)
            
            
            var topicDiv = document.createElement("div");
            topicDiv.setAttribute("id", "topic_name_and_buttons_div")
            document.getElementById(BarPlotPanelDivId).appendChild(topicDiv) ////topicDiv.setAttribute("style", "width:100%; height:5%; background-color: red")

            
           var topic_title= document.createElement("span"); 
           topic_title.innerText = "Topic: ";
           topicDiv.appendChild(topic_title); 

            
           var topic_name_selected_1 = document.createElement("span")
           topic_name_selected_1.innerText = ""
           topic_name_selected_1.setAttribute("id", "topic_name_selected_1")
           topicDiv.appendChild(topic_name_selected_1); 
            
           var merge = document.createElement("button");
           merge.setAttribute("id", topicMerge);
           merge.setAttribute("class", "btn btn-primary btnTopic")
           merge.innerHTML = "Merge";
           topicDiv.appendChild(merge);

           d3.select("#"+topicMerge)
               .on("click", function() {
                   if(merging_topic_1!=-1){
                       console.log("el mergin value is ", merging_topic_1)
                       $('.merging_topic_1').html(merging_topic_1);
                       $('#MergeModal_1').modal(); 
                   }
                   else{
                       $('#MergeModal_0').modal(); 
                   }
                   
               });


           d3.select("#continue_merging") //el usuario desea continuar con el mergin
           .on("click", function() {
               hacer_merge = true
           });

           d3.select("#cancel_merging") //el usuario desea continuar con el mergin
           .on("click", function() {
               hacer_merge = false
               
           });

           d3.select("#cancel_merging_2") //el usuario desea continuar con el mergin
           .on("click", function() {
               hacer_merge = false
               merging_topic_1 = merging_topic_2
               merging_topic_2 = -1
               
           });


           var split = document.createElement("button");
           split.setAttribute("id", topicSplit);
           split.setAttribute("class", "btn btn-primary btnTopic")
           split.innerHTML = "Split";
           topicDiv.appendChild(split);

  
        
            var edit = document.createElement("button");
            edit.setAttribute("id", topicEdit);
            edit.setAttribute("class", "btn btn-primary btnTopic")
            edit.innerHTML = "Rename";
            topicDiv.appendChild(edit);

            
            d3.select("#"+topicEdit)
                .on("click", function() {
                    $('#renameTopic').modal(); 
                });



            
            
            if(type_vis == 1){
                d3.select("#rename_topic_button")
                .on("click", function(){
                    
                    //rename the topic
                    name_topics_circles[document.getElementById("idTopic").innerText] = document.getElementById("renameTopicId").value
                    $('#topic_name_selected_1').html(name_topics_circles[document.getElementById("idTopic").innerText]); 

                    //visualize the new name
                    createMdsPlot(1, mdsData, lambda_lambda_topic_similarity.current)


                    topic_on(document.getElementById(topicID+vis_state.topic))


                })
            }
            else{
                d3.select("#rename_topic_button")
                .on("click", function(){

                    //rename the topic
                    name_topics_sankey[document.getElementById("idTopic").innerText] = document.getElementById("renameTopicId").value
                    
                    //visualize the new name
                    visualize_sankey(matrix_sankey[lambda_lambda_topic_similarity.current], vis_state.min_value_filtering, vis_state.max_value_filtering)
                    $('#topic_name_selected_1').html(name_topics_sankey[document.getElementById("idTopic").innerText])                    


                  
                })
            }
            d3.select("#rename_topic_button2")
                .on("click", function(){
                    //cambiar el nombre del topico segun lo especifique el usuario
                    name_topics_sankey[document.getElementById("idTopic2").innerText] = document.getElementById("renameTopicId2").value
                    //console.log("ESTE ES EL NUEVO ARREGLO", name_topics_sankey)
                    visualize_sankey(matrix_sankey[lambda_lambda_topic_similarity.current], vis_state.min_value_filtering, vis_state.max_value_filtering)
                    $('#topic_name_selected_2').html(name_topics_sankey[document.getElementById("idTopic2").innerText])                    
                    //visualizar el nuevo nombre
                    
                })


            


            //colocar #apply_merging.  "aqui esta el antiguo codigo para el merge"

            d3.select("#"+topicSplit)
            .on("click",function(){
                if(splitting_topic!=-1){
                    var real_topic_id = topic_order[splitting_topic-1]-1//Ojo! los topicos fueron ordenados de mayor a menor frecuencia, por eso que el orden cambia
                    updateRelevantDocumentsSplitting(real_topic_id, relevantDocumentsDict);
                    console.log("se hara un split al topico", splitting_topic)
                    $('.splitting_topic_1').html(splitting_topic);
                    $('#SplitModal_1').modal(); //$("#myModal").show();
                }
            });
            
            
            /*
            d3.select("#"+topicSplit) //el usuario desea continuar con el mergin #"#"+topicSplit
            .on("click", function() {
                merging_topic_1 = 1
                merging_topic_2 =2
                console.log("mezclar", merging_topic_1,topic_order[merging_topic_1-1]-1,"con", merging_topic_2, topic_order[merging_topic_2-1]-1)

                fetch('/merge_topics', {

                    // Specify the method
                    method: 'POST',

                    // A JSON payload
                    body: JSON.stringify({
                        "merging_topic_1": topic_order[merging_topic_1-1]-1, //no estoy seguro que numero de topico pasarle
                        "merging_topic_2": topic_order[merging_topic_2-1]-1
                    })
                }).then(function (response) { // At this point, Flask has printed our JSON
                    response.json().then(function(data){
                      //return response.text();
                        console.log("DATA DEVUELTA", data)
                    })
                }).then(function (text) {

                    console.log('POST response: ');

                    // Should be 'OK' if everything was successful
                    console.log(response)//console.log(text);
                });
                
                //createMdsPlot(1, mdsData, lambda_lambda_topic_similarity.current)
                
            });
            */


            
            var inputDiv = document.createElement("div");
            inputDiv.setAttribute("id", "BarPlotDiv");
            document.getElementById(BarPlotPanelDivId).appendChild(inputDiv)  //document.getElementById(visID).appendChild(inputDiv); //creo que esto debiera estar unido al svg mejor

            //Div for relevance slider. 
            var lambdaDiv = document.createElement("div");
            lambdaDiv.setAttribute("id", "relevanceSliderDiv");
            lambdaDiv.setAttribute("class", "RowDiv");
            inputDiv.appendChild(lambdaDiv);

            var sliderDiv = document.createElement("div");
            sliderDiv.setAttribute("id", sliderDivID);
            sliderDiv.setAttribute("class", "ColumnDiv");
            lambdaDiv.appendChild(sliderDiv);

            var lambdaInput = document.createElement("input");
            lambdaInput.setAttribute("class", "SliderInput")
            lambdaInput.type = "range";
            lambdaInput.min = 0;
            lambdaInput.max = 1;
            lambdaInput.step = data['lambda.step'];
            lambdaInput.value = vis_state.lambda;
            lambdaInput.id = lambdaID;
            lambdaInput.setAttribute("list", "ticks"); 
            sliderDiv.appendChild(lambdaInput);

            var lambdaLabel = document.createElement("label");
            lambdaLabel.setAttribute("id", lambdaLabelID);
            lambdaLabel.setAttribute("class", "ColumnDiv");
            lambdaLabel.setAttribute("for", lambdaID);
            lambdaLabel.innerHTML = "Relevance score: &#955 = <span id='" + lambdaID + "-value'>" + vis_state.lambda + "</span>";
            lambdaDiv.appendChild(lambdaLabel);

            // Create the svg to contain the slider scale:
            var scaleContainer = d3.select("#" + sliderDivID).append("svg")
                    .attr("id", "scaleContainer");

            var bounds_scaleContainer = scaleContainer.node().getBoundingClientRect();

            var sliderScale = d3.scaleLinear()
                    .domain([0, 1])
                    .range([7.5, bounds_scaleContainer.width-11])  //Now it is responsive
                    .nice();



            var sliderAxis = d3.axisBottom(sliderScale).tickSize(10).ticks(6);
                    
            // group to contain the elements of the slider axis:
            var sliderAxisGroup = scaleContainer.append("g")
                    .attr("class", "slideraxis")
                    .attr("margin-top", "-10px")
                    .call(sliderAxis);



            //Topic similarity slider (change the lambda of vector keywords and vector documents for topic similarity metric proposed)

            var svgCentralPanel = d3.select("#CentralPanel").append("div")
            svgCentralPanel.attr("id", "TopicSimilarityMetricPanel")



            ////

            var sliderDivLambdaTopicSimilarity = document.createElement("div");
            sliderDivLambdaTopicSimilarity.setAttribute("id", sliderDivIDLambdaTopicSimilarity);
            sliderDivLambdaTopicSimilarity.setAttribute("class", "RowDiv");
            document.getElementById("TopicSimilarityMetricPanel").appendChild(sliderDivLambdaTopicSimilarity)  //document.getElementById(visID).appendChild(inputDiv); //creo que esto debiera estar unido al svg mejor


            if(type_vis==2){


                
                /* This section is to allow users to filtering paths on sankey diagram*/

                //This funciton allow to the slider use the min-max value of the sankey diagram
                var min_similarity_score = Infinity
                var max_similarity_score = -Infinity
                matrix_sankey[lambda_lambda_topic_similarity.current].links.filter(function(el){
                    if(el.value < min_similarity_score){
                        min_similarity_score = el.value
                    }
                    if(el.value > max_similarity_score){
                        max_similarity_score = el.value
                    }
                });
                //round value min/max similarity score

                min_similarity_score =   Math.round(  min_similarity_score* 100) / 100
                max_similarity_score = Math.round(  max_similarity_score* 100) / 100
               

                var svgCentralPanelFiltering = d3.select("#CentralPanel").append("div")
                svgCentralPanelFiltering.attr("id", "TopicSimilarityMetricPanelFiltering")

                var sliderDivFiltering = document.createElement("div");
                sliderDivFiltering.setAttribute("id", "sliderDivFiltering");
                sliderDivFiltering.setAttribute("class", "RowDiv");
                document.getElementById("TopicSimilarityMetricPanelFiltering").appendChild(sliderDivFiltering)  

                var sliderDivInputFilteringTopicSimilarity = document.createElement("div");
                sliderDivInputFilteringTopicSimilarity.setAttribute("id", "sliderDivInputFilteringTopicSimilarity");
                sliderDivInputFilteringTopicSimilarity.setAttribute("class", "ColumnDiv");
                sliderDivFiltering.appendChild(sliderDivInputFilteringTopicSimilarity); 

                /* Add multi range slider*/
                var lambdaInputTopicSimilarity = document.createElement("div");
                lambdaInputTopicSimilarity.setAttribute("id", "lamdaInputTopicSimilarity");
                sliderDivInputFilteringTopicSimilarity.appendChild(lambdaInputTopicSimilarity);

                
                //var slider = document.getElementById('sliderDivInputFilteringTopicSimilarity');
                
                var slider = document.getElementById('lamdaInputTopicSimilarity');
                noUiSlider.create(slider, {
                    start: [(min_similarity_score+max_similarity_score)/2.0, max_similarity_score],
                    connect: true,
                    range: {
                        'min': min_similarity_score,
                        'max': max_similarity_score
                    }
                });
                //read values from slider slider-value-lower
                

                var lambdaLabelTopicSimilarity = document.createElement("label");
                lambdaLabelTopicSimilarity.setAttribute("id", "LabelFilteringTopicSimilarity");
                lambdaLabelTopicSimilarity.setAttribute("class", "ColumnDiv");
                lambdaLabelTopicSimilarity.setAttribute("for", "lambdaInputTopicSimilarityFiltering");
                lambdaLabelTopicSimilarity.innerHTML = "Filtering = [<span id='slider-value-lower'></span> - <span id='slider-value-upper'>]";
                sliderDivFiltering.appendChild(lambdaLabelTopicSimilarity);

                
                slider.noUiSlider.on('update', function (values, handle) {
                    
                    document.getElementById("LabelFilteringTopicSimilarity").innerHTML = "Filtering = [<span id='slider-value-lower'>"+values[0]+"</span>, <span id='slider-value-upper'>"+values[1]+"</span>]";
                    vis_state.max_value_filtering = values[1],
                    vis_state.min_value_filtering = values[0],
                    visualize_sankey(matrix_sankey[lambda_lambda_topic_similarity.current], vis_state.min_value_filtering, vis_state.max_value_filtering)


                });



                
                var scaleContainerTopicSimilarityFiltering = d3.select("#" + "sliderDivInputFilteringTopicSimilarity").append("svg")
                .attr("id", "scaleContainerTopicSimilarityFiltering");

                var bounds_scaleContainer_filtering = scaleContainerTopicSimilarityFiltering.node().getBoundingClientRect();
                
                var sliderScaleTopicSimilarityFiltering = d3.scaleLinear()
                        .domain([min_similarity_score, max_similarity_score])
                        .range([0+8, bounds_scaleContainer_filtering.width-8]);

                // adapted from http://bl.ocks.org/mbostock/1166403
                var sliderAxisTopicSimilarityFiltering = d3.axisBottom(sliderScaleTopicSimilarityFiltering).tickSize(10).ticks(10);
                        
                // group to contain the elements of the slider axis:
                var sliderAxisGroupFiltering = scaleContainerTopicSimilarityFiltering.append("g")
                        .attr("class", "slideraxis") //.attr("margin-top", "-30px")
                        .call(sliderAxisTopicSimilarityFiltering);
                

            }


            var sliderDivInputOmegaTopicSimilarity = document.createElement("div");
            sliderDivInputOmegaTopicSimilarity.setAttribute("id", sliderDivID+"OmegaTopicSimilarity");
            sliderDivInputOmegaTopicSimilarity.setAttribute("class", "ColumnDiv");
            sliderDivLambdaTopicSimilarity.appendChild(sliderDivInputOmegaTopicSimilarity);

            var lambdaInputLambdaTopicSimilarity = document.createElement("input");
            lambdaInputLambdaTopicSimilarity.type = "range";
            lambdaInputLambdaTopicSimilarity.min = 0.0
            lambdaInputLambdaTopicSimilarity.max = 1.0;
            lambdaInputLambdaTopicSimilarity.step = data['lambda.step'];
            lambdaInputLambdaTopicSimilarity.value = vis_state.lambda_lambda_topic_similarity; //
            lambdaInputLambdaTopicSimilarity.id = "lambdaInputLambdaTopicSimilarity";
            lambdaInputLambdaTopicSimilarity.setAttribute("list", "ticks"); // to enable automatic ticks (with no labels, see below)
            sliderDivInputOmegaTopicSimilarity.appendChild(lambdaInputLambdaTopicSimilarity);

            var lambdaLabelLambdaTopicSimilarity = document.createElement("label");
            lambdaLabelLambdaTopicSimilarity.setAttribute("id", "LambdaLabelLambdaTopicSimilarity");
            lambdaLabelLambdaTopicSimilarity.setAttribute("class", "ColumnDiv");
            lambdaLabelLambdaTopicSimilarity.setAttribute("for", "lambdaInputLambdaTopicSimilarity");
            lambdaLabelLambdaTopicSimilarity.innerHTML = "Omega score: &#937  = <span id='" + "lambdaInputLambdaTopicSimilarity" + "-value'>" + vis_state.lambda_lambda_topic_similarity + "</span>";
            sliderDivLambdaTopicSimilarity.appendChild(lambdaLabelLambdaTopicSimilarity);


            // Create the svg to contain the slider scale:
            var scaleContainerOmegaTopicSimilarity = d3.select("#" + sliderDivID+"OmegaTopicSimilarity").append("svg")
            .attr("id", "scaleContainerOmegaTopicSimilarity");

            var bounds_scaleContainer_omegatopicsimilarity = scaleContainerOmegaTopicSimilarity.node().getBoundingClientRect();

            var sliderScaleOmegaTopicSimilarity = d3.scaleLinear()
                    .domain([0, 1])
                    .range([7.5, bounds_scaleContainer_omegatopicsimilarity.width-7.5])  //Now it is responsive
                    .nice();



            var sliderAxisOmegaTopicSimilarity = d3.axisBottom(sliderScaleOmegaTopicSimilarity).tickSize(10).ticks(6);
                    
            // group to contain the elements of the slider axis:
            var sliderAxisGroup = scaleContainerOmegaTopicSimilarity.append("g")
                    .attr("class", "slideraxis")
                    .attr("margin-top", "-10px")
                    .call(sliderAxisOmegaTopicSimilarity);
    


            d3.select("#"+"lambdaInputLambdaTopicSimilarity")
            .on("mouseup", function() {
                lambda_lambda_topic_similarity.old = lambda_lambda_topic_similarity.current;
                lambda_lambda_topic_similarity.current = document.getElementById("lambdaInputLambdaTopicSimilarity").value;
                

                vis_state.lambda_lambda_topic_similarity =lambda_lambda_topic_similarity.current
            
                document.getElementById("lambdaInputLambdaTopicSimilarity" + "-value").innerHTML = " <span id='" + "lambdaInputLambdaTopicSimilarity" + "-value'>" + vis_state.lambda_lambda_topic_similarity + "</span>";
                document.getElementById("lambdaInputLambdaTopicSimilarity").value = vis_state.lambda_lambda_topic_similarity;


                
                if( lambda_lambda_topic_similarity.current == 0){
                    lambda_lambda_topic_similarity.current = Number(0).toFixed(1) //we need to do this, because javascript converts 0.0 to 0 by default. 
                }
                if ( lambda_lambda_topic_similarity.current == 1){
                    
                    lambda_lambda_topic_similarity.current = Number(1).toFixed(1)
                    
                }

                if(type_vis == 2){
                    visualize_sankey(matrix_sankey[lambda_lambda_topic_similarity.current], vis_state.min_value_filtering, vis_state.max_value_filtering)
                }
                if(type_vis == 1){

                    createMdsPlot(1, mdsData, lambda_lambda_topic_similarity.current)
                }
            });

            d3.select("#lambdaInputTopicSimilarityFiltering") //Filtering paths of sankey diagram
            .on("mouseup", function() {
                
                // store the previous lambda value
                lambda_topic_similarity.old = lambda_topic_similarity.current;
                
                lambda_topic_similarity.current = document.getElementById("lambdaInputTopicSimilarityFiltering").value;
                
                
                vis_state.lambda_topic_similarity =lambda_topic_similarity.current

                
                
                document.getElementById("lambdaInputTopicSimilarityFiltering-value").innerHTML = " <span id='lambdaInputTopicSimilarityFiltering-value'>" + Math.round( vis_state.lambda_topic_similarity * 100) / 100 + "</span>";

                document.getElementById("lambdaInputTopicSimilarityFiltering").value = vis_state.lambda_topic_similarity;
                
                
                visualize_sankey(matrix_sankey[lambda_lambda_topic_similarity.current], vis_state.min_value_filtering, vis_state.max_value_filtering)
                
            });






        }

        // function to re-order the bars (gray and red), and terms:

        function reorder_bars_helper(to_select, increase, topic_id_in_model, barFreqsID_actual, bar_totals_actual, terms_actual, overlay, xaxis_class){
            console.log("ojo, estos son los parametros que recibe reorder_bars_helper", increase, topic_id_in_model, barFreqsID_actual, bar_totals_actual, terms_actual, overlay, xaxis_class)
            
            var dat2 = lamData.filter(function(d) {
                
                return d.Category == "Topic" + topic_id_in_model;
            });
            
            
            // define relevance:
            for (var i = 0; i < dat2.length; i++) {
                dat2[i].relevance = vis_state.lambda * dat2[i].logprob +
                    (1 - vis_state.lambda) * dat2[i].loglift;
            }
            

            // sort by relevance:
            dat2.sort(fancysort("relevance"));

            

            // truncate to the top R tokens:
            var dat3 = dat2.slice(0, R);
            
            var y = d3.scaleBand()
                    .domain(dat3.map(function(d) {
                        return d.Term;
                    }))
                    .rangeRound([0, barheight])
                    .padding(0.15);
                    //.rangeRoundBands([0, barheight], 0.15);
            var x = d3.scaleLinear()
                    .domain([1, d3.max(dat3, function(d) {
                        return d.Total;
                    })])
                    .range([0, barwidth])
                    .nice();

            // Change Total Frequency bars
            var graybars = d3.select("#" + barFreqsID_actual)
                    .selectAll(to_select + " ."+bar_totals_actual) //.bar-totals
                    .data(dat3, function(d) {
                        return d.Term;
                    });

            // Change word labels
            var labels = d3.select("#" + barFreqsID_actual)
                    .selectAll(to_select + " ."+terms_actual)
                    .data(dat3, function(d) {
                        return d.Term;
                    });

            // Create red bars (drawn over the gray ones) to signify the frequency under the selected topic
            var redbars = d3.select("#" + barFreqsID_actual)
                    .selectAll(to_select + " ."+overlay)
                    .data(dat3, function(d) {
                        return d.Term;
                    });

            // adapted from http://bl.ocks.org/mbostock/1166403

            var xAxis = d3.axisTop(x).tickSize(-barheight).ticks(6);
            
            // New axis definition:
            var newaxis = d3.selectAll(to_select + " ."+xaxis_class);

            // define the new elements to enter:
            var graybarsEnter = graybars.enter().append("rect")
                    .attr("class", bar_totals_actual)
                    .attr("x", 0)
                    .attr("y", function(d) {
                        return y(d.Term) + barheight + margin.bottom + 2 * rMax;
                    })
                    .attr("height", y.bandwidth())
                    .style("fill", color1)
                    .attr("opacity", 0.4);

            var labelsEnter = labels.enter()
                    .append("text")
                    .attr("x", -5)
                    .attr("class", terms_actual)
                    .attr("y", function(d) {
                        return y(d.Term) + 12 + barheight + margin.bottom + 2 * rMax;
                    })
                    .attr("cursor", "pointer")
                    .style("text-anchor", "end")
                    .attr("id", function(d) {
                        return (termID + d.Term);
                    })
                    .text(function(d) {
                        return d.Term;
                    })
                    .on("mouseover", function() {
                        //term_hover(this); esto lo desactive
                    })
            
                    .on("mouseout", function() {
                        vis_state.term = "";
                        term_off(this);
                        //state_save(true);
                    });

            var redbarsEnter = redbars.enter().append("rect")
                    .attr("class", overlay)
                    .attr("x", 0)
                    .attr("y", function(d) {
                        return y(d.Term) + barheight + margin.bottom + 2 * rMax;
                    })
                    .attr("height", y.bandwidth())
                    .style("fill", color2)
                    .attr("opacity", 0.8);


            if (increase) {
                graybarsEnter
                    .attr("width", function(d) {
                        return x(d.Total);
                    })
                    .transition().duration(duration)
                    .delay(duration)
                    .attr("y", function(d) {
                        return y(d.Term);
                    });
                labelsEnter
                    .transition().duration(duration)
                    .delay(duration)
                    .attr("y", function(d) {
                        return y(d.Term) + 12;
                    });
                redbarsEnter
                    .attr("width", function(d) {
                        return x(d.Freq);
                    })
                    .transition().duration(duration)
                    .delay(duration)
                    .attr("y", function(d) {
                        return y(d.Term);
                    });

                graybars.transition().duration(duration)
                    .attr("width", function(d) {
                        return x(d.Total);
                    })
                    .transition().duration(duration)
                    .attr("y", function(d) {
                        return y(d.Term);
                    });
                labels.transition().duration(duration)
                    .delay(duration)
                    .attr("y", function(d) {
                        return y(d.Term) + 12;
                    });
                redbars.transition().duration(duration)
                    .attr("width", function(d) {
                        return x(d.Freq);
                    })
                    .transition().duration(duration)
                    .attr("y", function(d) {
                        return y(d.Term);
                    });

                // Transition exiting rectangles to the bottom of the barchart:
                graybars.exit()
                    .transition().duration(duration)
                    .attr("width", function(d) {
                        return x(d.Total);
                    })
                    .transition().duration(duration)
                    .attr("y", function(d, i) {
                        return barheight + margin.bottom + 6 + i * 18;
                    })
                    .remove();
                labels.exit()
                    .transition().duration(duration)
                    .delay(duration)
                    .attr("y", function(d, i) {
                        return barheight + margin.bottom + 18 + i * 18;
                    })
                    .remove();
                redbars.exit()
                    .transition().duration(duration)
                    .attr("width", function(d) {
                        return x(d.Freq);
                    })
                    .transition().duration(duration)
                    .attr("y", function(d, i) {
                        return barheight + margin.bottom + 6 + i * 18;
                    })
                    .remove();
                // https://github.com/mbostock/d3/wiki/Transitions#wiki-d3_ease
                newaxis.transition().duration(duration)
                    .call(xAxis)
                    .transition().duration(duration);
            } else {
                graybarsEnter
                    .attr("width", 100) // FIXME by looking up old width of these bars
                    .transition().duration(duration)
                    .attr("y", function(d) {
                        return y(d.Term);
                    })
                    .transition().duration(duration)
                    .attr("width", function(d) {
                        return x(d.Total);
                    });
                labelsEnter
                    .transition().duration(duration)
                    .attr("y", function(d) {
                        return y(d.Term) + 12;
                    });
                redbarsEnter
                    .attr("width", 50) // FIXME by looking up old width of these bars
                    .transition().duration(duration)
                    .attr("y", function(d) {
                        return y(d.Term);
                    })
                    .transition().duration(duration)
                    .attr("width", function(d) {
                        return x(d.Freq);
                    });

                graybars.transition().duration(duration)
                    .attr("y", function(d) {
                        return y(d.Term);
                    })
                    .transition().duration(duration)
                    .attr("width", function(d) {
                        return x(d.Total);
                    });
                labels.transition().duration(duration)
                    .attr("y", function(d) {
                        return y(d.Term) + 12;
                    });
                redbars.transition().duration(duration)
                    .attr("y", function(d) {
                        return y(d.Term);
                    })
                    .transition().duration(duration)
                    .attr("width", function(d) {
                        return x(d.Freq);
                    });

                // Transition exiting rectangles to the bottom of the barchart:
                graybars.exit()
                    .transition().duration(duration)
                    .attr("y", function(d, i) {
                        return barheight + margin.bottom + 6 + i * 18 + 2 * rMax;
                    })
                    .remove();
                labels.exit()
                    .transition().duration(duration)
                    .attr("y", function(d, i) {
                        return barheight + margin.bottom + 18 + i * 18 + 2 * rMax;
                    })
                    .remove();
                redbars.exit()
                    .transition().duration(duration)
                    .attr("y", function(d, i) {
                        return barheight + margin.bottom + 6 + i * 18 + 2 * rMax;
                    })
                    .remove();

                // https://github.com/mbostock/d3/wiki/Transitions#wiki-d3_ease
                newaxis.transition().duration(duration)
                    .transition().duration(duration)
                    .call(xAxis);
            }
        }

        function reorder_bars_new(increase, side) {
            if(type_vis == 1){
                // grab the bar-chart data for this topic only:
                var topic_id_in_model = vis_state.topic
                reorder_bars_helper("#barplot_1", increase, topic_id_in_model, barFreqsID,'bar-totals','terms','overlay', 'xaxis')
            }
            else{
                //type_vis == 2
                //hay que determinar si le hace click al slider de la izquierda o al de la derecha
                if(side == "left"){
                    reorder_bars_helper("#barplot_1", increase, topic_id_model_1+1, barFreqsID,'bar-totals','terms','overlay', 'xaxis')
                }
                else{
                    //right
                    reorder_bars_helper("#barplot_2", increase, topic_id_model_2+1, barFreqsID_2,'bar-totals_2','terms_2','overlay_2', 'xaxis_2')

                }
                

            }
            

            

        }




        // function to update bar chart when a topic is selected
        // the circle argument should be the appropriate circle element
        function topic_on_sankey(box, min_target_node_value ){
            
            if(box.node>=min_target_node_value){
                //pertenece al modelo de corpus 2
                to_select = "#DocumentsPanel"
                var topic_id_in_model = box.node-min_target_node_value
                var real_topic_id = topic_order_2[topic_id_in_model]-1
                
                
                updateRelevantDocuments(real_topic_id, relevantDocumentsDict_2,2);
                
                var Freq = jsonData_2.mdsDat.Freq[box.node-min_target_node_value]    

                lamData = [];
                for (var i = 0; i < jsonData_2['tinfo'].Term.length; i++) {
                    var obj = {};
                    for (var key in jsonData_2['tinfo']) {
                        obj[key] = jsonData_2['tinfo'][key][i];
                    }
                    lamData.push(obj);
                }

                var barFreqsID_actual = barFreqsID_2
                var bar_totals_actual = "bar-totals_2"
                var terms_actual = "terms_2"
                var bubble_tool = 'bubble-tool_2'
                var overlay = 'overlay_2'
                var xaxis_class = "xaxis_2"

                topic_id_model_2 = topic_id_in_model //esta info es util para la funcion reorder_bars
                
                //colorear el item seleccionado
                if(last_clicked_model_2!=-1){
                    d3.select("#"+last_clicked_model_2).style("fill","rgb(252,153,146)")
                }

                
                last_clicked_model_2 = "node_"+box.node
                d3.select("#"+last_clicked_model_2).style("fill","rgb(237, 62, 50)")
                document.getElementById("renameTopicId2").value = name_topics_sankey[topicID + box.node] 
                $('#idTopic2').html(topicID + box.node); 
                $('#topic_name_selected_2').html(name_topics_sankey[topicID + box.node] ); 
            }
            else{ // el topico seleccionado eprtenece al modelo del corpus 1


                //show topic namename_topics_sankey
                //$('#topic_name_selected_1').html(name_topics_circles[topicID + d.topics]); 
                


                to_select =  "#BarPlotPanelDiv"
                var topic_id_in_model = box.node
                var real_topic_id = topic_order[topic_id_in_model]-1
                
                updateRelevantDocuments(real_topic_id, relevantDocumentsDict, 1);
                
                var Freq = jsonData.mdsDat.Freq[box.node]   

                lamData = [];
                for (var i = 0; i < jsonData['tinfo'].Term.length; i++) {
                    var obj = {};
                    for (var key in jsonData['tinfo']) {
                        obj[key] = jsonData['tinfo'][key][i];
                    }
                    lamData.push(obj);
                }

                var barFreqsID_actual = barFreqsID
                var bar_totals_actual = "bar-totals"
                var terms_actual = "terms"
                var bubble_tool = 'bubble-tool'
                var overlay = 'overlay'
                var xaxis_class = "xaxis"

                topic_id_model_1 = topic_id_in_model //esta info es util para la funcion reorder_bars

                //colorear el item seleccionado
                if(last_clicked_model_1!=-1){
                    d3.select("#"+last_clicked_model_1).style("fill","rgb(95,160,254)")
                }

                last_clicked_model_1 = "node_"+box.node
                d3.select("#"+last_clicked_model_1).style("fill","rgb(14, 91, 201)")
                //cual es el d al que le estoy haciendo click??


                
                
                document.getElementById("renameTopicId").value = name_topics_sankey[topicID + box.node] 
                $('#idTopic').html(topicID + box.node);
                $('#topic_name_selected_1').html(name_topics_sankey[topicID + box.node]); 
                
            }

            vis_state.topic = box.node
            

            Freq = Math.round(Freq * 10) / 10  


            var text = d3.select(to_select + " ."+bubble_tool);
            text.remove();

            /* Quite el titulo, quizas esto sea importante en el futuro. 
            d3.select("#" + barFreqsID_actual)
                .append("text")
                .attr("x", mdswidth+margin.left+termwidth+(barwidth/2))
                .attr("y", -30)
                .attr("class", bubble_tool) //  set class so we can remove it when highlight_off is called
                .style("text-anchor", "middle")
                .style("font-size", "16px")
                .text("Top-" + number_terms_sankey + " Most Relevant Terms for Topic " + topic_id_in_model+ " (" + Freq + "% of tokens)");
                //Freq jsonData
            
            */
            // grab the bar-chart data for this topic only:
            
            var dat2 = lamData.filter(function(d) {
                if(box.node==-1){ //haccer que esto ocurra
                    return d.Category == "Default" //creo que estos son los terminos mas relevantes de todo el corpus
                }
                else{
                    return d.Category == "Topic" + (box.node%min_target_node_value+1); // OJO! AQUI HAY UN +1, quizas hay que sacarlo y mejorar el codigo, esto esta medio mula
                }
                
            });
            

            // define relevance:
            for (var i = 0; i < dat2.length; i++) {
                dat2[i].relevance = lambda.current * dat2[i].logprob +
                    (1 - lambda.current) * dat2[i].loglift;
            }

            dat2.sort(fancysort("relevance"));
            // truncate to the top R tokens:
            var dat3 = dat2.slice(0, number_terms_sankey);

            //AddBackgroundColorToText(dat3)

            // scale the bars to the top R terms:
            var y = d3.scaleBand()
                    .domain(dat3.map(function(d) {
                        return d.Term;
                    }))
                    .rangeRound([0, barheight])
                    .padding(0.15);
                    //.rangeRoundBands([0, barheight], 0.15);
            var x = d3.scaleLinear()
                    .domain([1, d3.max(dat3, function(d) {
                        return d.Total;
                    })])
                    .range([0, barwidth])
                    .nice();

            // remove the red bars if there are any:
            d3.selectAll(to_select + " ."+overlay).remove();

            // Change Total Frequency bars
            d3.selectAll(to_select + " ."+bar_totals_actual)
                .data(dat3)
                .attr("x", 0)
                .attr("y", function(d) {
                    return y(d.Term);
                })
                .attr("height", y.bandwidth())
                .attr("width", function(d) {
                    return x(d.Total);
                })
                .style("fill", color1)
                .attr("opacity", 0.4);

            // Change word labels
            d3.selectAll(to_select + " ."+terms_actual)
                .data(dat3)
                .attr("x", -5)
                .attr("y", function(d) {
                    return y(d.Term) + 12;
                })
                .attr("id", function(d) {
                    return (termID + d.Term);
                })
                .style("text-anchor", "end") // right align text - use 'middle' for center alignment
                .text(function(d) {
                    return d.Term;
                });

            // Create red bars (drawn over the gray ones) to signify the frequency under the selected topic
            d3.select("#" + barFreqsID_actual).selectAll(to_select + " ."+overlay)
                .data(dat3)
                .enter()
                .append("rect")
                .attr("class", overlay)
                .attr("x", 0)
                .attr("y", function(d) {
                    return y(d.Term);
                })
                .attr("height", y.bandwidth())
                .attr("width", function(d) {
                    return x(d.Freq);
                })
                .style("fill", color2)
                .attr("opacity", 0.8);

            // adapted from http://bl.ocks.org/mbostock/1166403

            var xAxis = d3.axisTop(x).tickSize(-barheight).ticks(6);

            // redraw x-axis
            d3.selectAll(to_select + " ."+xaxis_class)
            //.attr("class", "xaxis")
                .call(xAxis);


        }
        function topic_on(circle) {
            to_select = "#BarPlotPanelDiv"
            if (circle == null) return null;
            
            
            // grab data bound to this element
            var d = circle.__data__;

            // update name in visualization
            $('#topic_name_selected_1').html(name_topics_circles[topicID + d.topics]); 


            var Freq = Math.round(d.Freq * 10) / 10,
                topics = d.topics;

            // change opacity and fill of the selected circle
            circle.style.opacity = highlight_opacity;
            circle.style.fill = color2;

            // Remove 'old' bar chart title
            var text = d3.select(to_select + " .bubble-tool");
            text.remove();

            // append text with info relevant to topic of interest
            console.log("que hay aqui", d3.select("#" + barFreqsID))
            
            var bounds_barplot = d3.select("#BarPlotPanelDiv").node().getBoundingClientRect();
            console.log("obtuve el ancho o no", bounds_barplot)

            //barheight = bounds_barplot.height - 1.5*termwidth
            //barwidth = bounds_barplot.width - 1.5*termwidth

            d3.select("#" + barFreqsID)
                .append("text")
                .attr("x",(bounds_barplot.width)/2 - termwidth) //mdswidth+margin.left+termwidth+(barwidth/2) .attr("transform", "translate("  +(termwidth) + "," +2*height_bar+ ")") /
                .attr("y", -20)
                .attr("class", "bubble-tool") //  set class so we can remove it when highlight_off is called
                .style("text-anchor", "middle")
                .style("font-size", "16px")
                .text("Top Most Relevant Terms for Topic  (" + Freq + "% of tokens)");
                //.text("Top Most Relevant Terms for Topic " + topics + " (" + Freq + "% of tokens)");
            



            // grab the bar-chart data for this topic only:
            var dat2 = lamData.filter(function(d) {
                return d.Category == "Topic" + topics;
            });

            // define relevance:
            for (var i = 0; i < dat2.length; i++) {
                dat2[i].relevance = lambda.current * dat2[i].logprob +
                    (1 - lambda.current) * dat2[i].loglift;
            }

            // sort by relevance:
            dat2.sort(fancysort("relevance"));
            
            // truncate to the top R tokens:
            var dat3 = dat2.slice(0, R);
            
            
            //Show most relevant documents
            var real_topic_id = topic_order[d.topics-1]-1//Ojo! los topicos fueron ordenados de mayor a menor frecuencia, por eso que el orden cambia
            updateRelevantDocuments(real_topic_id, relevantDocumentsDict, 1);
            
            var y = d3.scaleBand()
                    .domain(dat3.map(function(d) {
                        return d.Term;
                    }))
                    .rangeRound([0, barheight])
                    .padding(0.15);
                    //.rangeRoundBands([0, barheight], 0.15);
            var x = d3.scaleLinear()
                    .domain([1, d3.max(dat3, function(d) {
                        return d.Total;
                    })])
                    .range([0, barwidth])
                    .nice();

            // remove the red bars if there are any:
            d3.selectAll(to_select + " .overlay").remove();

            // Change Total Frequency bars
            d3.selectAll(to_select + " .bar-totals")
                .data(dat3)
                .attr("x", 0)
                .attr("y", function(d) {
                    return y(d.Term);
                })
                .attr("height", y.bandwidth())
                .attr("width", function(d) {
                    return x(d.Total);
                })
                .style("fill", color1)
                .attr("opacity", 0.4);

            // Change word labels
            d3.selectAll(to_select + " .terms")
                .data(dat3)
                .attr("x", -5)
                .attr("y", function(d) {
                    return y(d.Term) + 12;
                })
                .attr("id", function(d) {
                    return (termID + d.Term);
                })
                .style("text-anchor", "end") // right align text - use 'middle' for center alignment
                .text(function(d) {
                    return d.Term;
                });

            // Create red bars (drawn over the gray ones) to signify the frequency under the selected topic
            d3.select("#" + barFreqsID).selectAll(to_select + " .overlay")
                .data(dat3)
                .enter()
                .append("rect")
                .attr("class", "overlay")
                .attr("x", 0)
                .attr("y", function(d) {
                    return y(d.Term);
                })
                .attr("height", y.bandwidth())
                .attr("width", function(d) {
                    return x(d.Freq);
                })
                .style("fill", color2)
                .attr("opacity", 0.8);

            // adapted from http://bl.ocks.org/mbostock/1166403

            var xAxis = d3.axisTop(x).tickSize(-barheight).ticks(6);

            // redraw x-axis
            d3.selectAll(to_select + " .xaxis")
            //.attr("class", "xaxis")
                .call(xAxis);
        }



        function topic_off(circle) {
            to_select = "#BarPlotPanelDiv"

            if (circle == null) return circle;
            // go back to original opacity/fill
            circle.style.opacity = base_opacity;
            circle.style.fill = color1;

            var title = d3.selectAll(to_select + " .bubble-tool")
                    .text("Top-" + R + " Most Salient Terms");
            title.append("tspan")
                .attr("baseline-shift", "super")
                .attr("font-size", 12)
                .text(1);

            // remove the red bars
            d3.selectAll(to_select + " .overlay").remove();

            // go back to 'default' bar chart
            var dat2 = lamData.filter(function(d) {
                return d.Category == "Default";
            });

            var y = d3.scaleBand()
                    .domain(dat2.map(function(d) {
                        return d.Term;
                    }))
                    .rangeRound([0, barheight])
                    .padding(0.15);
                    //.rangeRoundBands([0, barheight], 0.15);
            var x = d3.scaleLinear()
                    .domain([1, d3.max(dat2, function(d) {
                        return d.Total;
                    })])
                    .range([0, barwidth])
                    .nice();

            // Change Total Frequency bars
            d3.selectAll(to_select + " .bar-totals")
                .data(dat2)
                .attr("x", 0)
                .attr("y", function(d) {
                    return y(d.Term);
                })
                .attr("height", y.bandwidth())
                .attr("width", function(d) {
                    return x(d.Total);
                })
                .style("fill", color1)
                .attr("opacity", 0.4);

            //Change word labels
            d3.selectAll(to_select + " .terms")
                .data(dat2)
                .attr("x", -5)
                .attr("y", function(d) {
                    return y(d.Term) + 12;
                })
                .style("text-anchor", "end") // right align text - use 'middle' for center alignment
                .text(function(d) {
                    return d.Term;
                });

            // adapted from http://bl.ocks.org/mbostock/1166403

           var xAxis = d3.axisTop(x).tickSize(-barheight).ticks(6);

            // redraw x-axis
            d3.selectAll(to_select + " .xaxis")
                .attr("class", "xaxis")
                .call(xAxis);
        }

       

       

        
    
        
        var ctx_list = document.querySelectorAll(".the-svg");
            for (var i = 0; i < ctx_list.length; i++) {
                
                var textElm = ctx_list[i].getElementById("the-text");
                var SVGRect = textElm.getBBox();
                
                var rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                rect.setAttribute("x", SVGRect.x);
                rect.setAttribute("y", SVGRect.y);
                rect.setAttribute("width", SVGRect.width);
                rect.setAttribute("height", SVGRect.height);
                rect.setAttribute("fill", "yellow");
                ctx_list[i].insertBefore(rect,textElm);
                

            }
        


            //https://stackoverflow.com/questions/44336431/how-to-add-a-column-with-buttons-to-a-bootstrap-table-populated-by-data-from-mys/44343632
            $('.tableRelevantDocumentsClass_Split').on('click-row.bs.table', function (e, row, $element) {
                var row_num = $element.index() + 1;
                
                
              });

        function getIdSelectionsFromTable() {
            var $table = $('.tableRelevantDocumentsClass_Split')
            
            return $.map($table.bootstrapTable('getSelections'), function (row) {
                return row.id
            })
        }

        var checkedRows = [];

        $('.tableRelevantDocumentsClass_Split').on('check.bs.table', function (e, row) {
            
        checkedRows.push({topic_perc_contrib: row.topic_perc_contrib, text: row.text,uncategorized: row.uncategorized, subtopic1: row.subtopic1, subtopic2: row.subtopic2 }); // id: row.id ¿como obtener la id de la row? uwu //checkedRows.push({id: row.id, name: row.name, forks: row.forks});
        console.log(checkedRows);
        });

        $('.tableRelevantDocumentsClass_Split').on('uncheck.bs.table', function (e, row) {
        $.each(checkedRows, function(index, value) {
            if (value.id === row.id) {
            checkedRows.splice(index,1);
            }
        });
        console.log(checkedRows);
        });

        $("#add_cart").click(function() {
        $("#output").empty();
        $.each(checkedRows, function(index, value) {
            $('#output').append($('<li></li>').text(value.text+"---"+value.topic_perc_contrib+"---"+value.uncategorized+"---"+value.subtopic1+"---"+value.subtopic2));
        });
        });

        function updateRelevantDocumentsSplitting(topic_id, relevantDocumentsDict){
            $('.tableRelevantDocumentsClass_Split').bootstrapTable("destroy");
                $('.tableRelevantDocumentsClass_Split').bootstrapTable({
                    toggle:true,
                    pagination: true,
                    search: true,
                    sorting: true,
                    //showRefresh: true, Hacer que esto funcione! ver :  https://examples.bootstrap-table.com/#view-source
                    //showExport:true,
                    //showColumns: true,
                    columns:[
                        {
                            field: 'topic_perc_contrib',
                            title: 'Contribution',
                            sortable:'true'
                        },{
                            field: 'text',
                            title: 'Text',
                            sortable:'true'
                        },{
                            field: 'uncategorized',
                            title:'Uncategorized',
                            checkbox: true,
                        },
                        {
                            field: 'subtopic1',
                            title:'Sub topic 1',
                            radio: true,
                        },
                        {
                            field: 'subtopic2',
                            title:'Sub topic 2',
                            radio: true,
                        }
                    ],
                    data: relevantDocumentsDict[topic_id]
                });
                //add dinamically row to a boostrapTable
                //$('.tableRelevantDocumentsClass_Split tbody tr').append('<td><input type="radio" id="uncategorized" ></td>');
                //$('.tableRelevantDocumentsClass_Split tbody tr').append('<td><input type="radio" id="subtopic1"></td>');
                //$('.tableRelevantDocumentsClass_Split tbody tr').append('<td><input type="radio" id="subtopic2"></td>');
                //$('.tableRelevantDocumentsClass_Split tbody tr').append('<td><input type="radio" id="uncategorized" name="group1"></td>');
                //$('.tableRelevantDocumentsClass_Split tbody tr').append('<td><input type="radio" id="subtopic1" name="group2"></td>');

                


        }
        function updateRelevantDocuments(topic_id, relevantDocumentsDict, model){
            if(model == 1){
                $('#tableRelevantDocumentsClass_Model1').bootstrapTable("destroy");
                $('#tableRelevantDocumentsClass_Model1').bootstrapTable({
                    data: relevantDocumentsDict[topic_id].slice(0,R)
                });
            }
            else{//model == 2
                $('#tableRelevantDocumentsClass_Model2').bootstrapTable("destroy");
                $('#tableRelevantDocumentsClass_Model2').bootstrapTable({
                    data: relevantDocumentsDict[topic_id].slice(0,R)
                });
            }
            
        
        }
        function get_RGB_by_relevance(c1_r,c1_g,c1_b, c2_r, c2_g, c2_b, r_min, r_max, r_actual){
            var final_color_r = c1_r+((r_actual-r_min)/(r_max-r_min))*(c2_r-c1_r)
            var final_color_g = c1_g+((r_actual-r_min)/(r_max-r_min))*(c2_g-c1_g)
            var final_color_b = c1_b+((r_actual-r_min)/(r_max-r_min))*(c2_b-c1_b)
            
            return [final_color_r,final_color_g,final_color_b]
        }
        


    }
    
    if (typeof data_or_file_name === 'string'){
        
        d3.json(data_or_file_name, function(error, data) {visualize(data);});
    }

        
    else{
        
        visualize(data_or_file_name);
        
    }
        


};

