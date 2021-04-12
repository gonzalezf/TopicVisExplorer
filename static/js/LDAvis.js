/* Original code taken from https://github.com/cpsievert/LDAvis */
/* Copyright 2013, AT&T Intellectual Property */
/* MIT Licence */

'use strict';
var global_terms_1;
var global_lamData;
var merged_topic_to_delete = [];
var name_merged_topic_to_delete = [];
var old_topic_model_states = []; //here we are going to save previous topic models. This should be a array of dictionaries
var current_relevant_documents_topic_splitting;
var global_topic_splitting_data;
var list_terms_for_topic_splitting = [];
var slider_topic_splitting_values = {};
var testing_var; 
var testing_mdsData;
var is_human_in_the_loop;
var scenario_2_is_baseline_metric;
if(type_vis== 2){
    if( Object.keys(matrix_sankey).length == 1){
        scenario_2_is_baseline_metric = true;
    
    }
    else{
        scenario_2_is_baseline_metric = false;
    }
}


var LDAvis = function(to_select, data_or_file_name) {

    // This section sets up the logic for event handling
    
    var vis_state = {
            lambda: 0.6,
            min_value_filtering:-1.0,
            max_value_filtering: 1.0,
            lambda_lambda_topic_similarity:0.8, //que tanta info tiene vector top keywords y que tanta info tiene vector top relevant documents
            lambda_topic_similarity:-1.0, //este filtra las lineas (el ancho que de similitud). If this value is very low, it is going to show all the paths. 
            topic: 1,
            term: ""
        };


    //for the user study. The omega value will be random
    if(type_vis==2){
        vis_state.lambda_lambda_topic_similarity = Math.random().toFixed(2) // Omega random , chosen randomly for the user study        

    }
    // Set up a few 'global' variables to hold the data:
    var K, // number of topics
        mdsData, // (x,y) locations and topic proportions
        //mdsData3, // topic proportions for all terms in the viz
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
        color1_1 = "#BE7CF0", //violeta
        color1_2 = "#632A9E", //morado
        

        color2_1 = "#6BF0A7", //"red", //"#6BF0A7", //verde claro
        color2_2 = "#00A385"; //"blue"; //"00A385"; //"13A383"; //verde oscuro
                

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
    highlight_opacity = 0.5;

    // lambda selection names are specific to *this* vis
    
    var lambda_select = to_select + "-lambda";

    // get rid of the # in the to_select (useful) for setting ID values
    var visID = to_select.replace("#", "");
    var topicID = visID + "-topic";
    var lambdaID = visID + "-lambda";
    var lambdaIDRightPanel =  lambdaID+"RightPanel"; 



    var termID = visID + "-term";

    var topicReverse = topicID+"-reverse";    

    var topicEdit = topicID+"-edit";
    var topicEdit2 = topicID+"-edit_2";
    var topicSplit = topicID+"-split";
    var topicMerge = topicID+"-merge";

    

    var leftPanelID = visID + "-leftpanel";
    var barFreqsID = "barplot_1";
    var barFreqsID_2 = "barplot_2";

    var barFreqsIDTopicSplitting = "barplot_1_TopicSplitting";



    
    
    var sliderDivID = "RelevanceSliderContenedor";
    var lambdaLabelID = "RelevanceSliderLabel";

    var min_target_node_value = Infinity;

    var number_terms_sankey = 20
    

    //esto se ocupa en la comparación de un corpus
    var topic_id_model_1 = -1
    var topic_id_model_2 = -1

    /////////////////////////
    ////topic mergin
    var merging_topic_1 = -1
    

    var splitting_topic = -1

    

    var last_clicked_model_1 = -1
    var last_clicked_model_2 = -1


    //rename topic variables
    
    var name_topics_circles = {}
    var name_topics_sankey = {}

    var isSettingInitial = true

    var number_top_keywords_name = 3

    
    var real_last_clicked_sankey_model_1
    var real_last_clicked_sankey_model_2

    var BarPlotPanelDivId = 'BarPlotPanelDiv'


    

    var sliderDivIDLambdaTopicSimilarity = "sliderDivLambdaTopicSimilarity"
    //to_select = BarPlotPanelDivId
    
    //Get relevant documents from ajax
    if(type_vis === 1){
        var relevantDocumentsDict;    
        $.ajax({
            url: "/SingleCorpus_documents",
            dataType: 'json',
            async: false,
            success: function(data) {        
                relevantDocumentsDict = data            
            }
        });        
    }

    if(type_vis === 2){
     
        var relevantDocumentsDict;
        var relevantDocumentsDict_2;
    
        $.ajax({
            url: "/MultiCorpora_documents_1",
            dataType: 'json',
            async: false,
            success: function(data) {        
                relevantDocumentsDict = data
                
            }
        });
    
        $.ajax({
            url: "/MultiCorpora_documents_2",
            dataType: 'json',
            async: false,
            success: function(data) {        
                relevantDocumentsDict_2 = data            
            }
        });
        
    }
    
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

    function updateTopicNamesCircles(data){
        
        // set the number of topics to global variable K:
        ////console.log("este data yo recibi", data)
        //console.log('estoy en la funcion update topic names circles')
        K = data['mdsDat'].x.length;

        // R is the number of top relevant (or salient) words whose bars we display
        var R = Math.min(data['R'], 20);

        // a (K x 5) matrix with columns x, y, topics, Freq, cluster (where x and y are locations for left panel)
        //console.log('Before MDS ', mdsData);

        mdsData = [];
        for (var i = 0; i < K; i++) {
            var obj = {};
            for (var key in data['mdsDat']) {
                obj[key] = data['mdsDat'][key][i];
            }
            mdsData.push(obj);
        }
        
        //console.log('Step 1: mds data updated', mdsData);


        //console.log('step 3,  lamdata BEFORE', lamData);
        var length_tinfo =   Object.keys(data['tinfo']['Term']).length;

      
        //console.log('este es el largo', length_tinfo);
        lamData = [];
        for (var i = 0; i <  length_tinfo ; i++) { // data['tinfo'].Term.length
            var obj = {};
            for (var key in data['tinfo']) {
                obj[key] = data['tinfo'][key][i];
            }

            if(obj['Freq']==0){
                obj['loglift'] = -Infinity;
                obj['logprob'] = -Infinity;
            }
            lamData.push(obj);
        }



        //console.log('step 3, updated lamdata', lamData);

        var dat3 = lamData.slice(0, R);
        //console.log('step 4, updated dat3', dat3);


    


        //console.log(data);
        //console.log('estos datos a mirar , se debieron actualizar ojala lamdata', lamData,'r',R,'k',K);

        //assign name to array

        
        d3.select("#name_topics")
                    .data(mdsData)
                    .enter()
                    .each(
                    function(d) {
                        var dat2 = lamData.filter(function(e) {
                            return e.Category == "Topic"+d.topics;s
                        });
                        
    
                        // define relevance:
                        for (var i = 0; i < dat2.length; i++) {
                            dat2[i].relevance = lambda.current * dat2[i].logprob +
                                (1 - lambda.current) * dat2[i].loglift;
    
                            if(isNaN(dat2[i].relevance)){
                                dat2[i].relevance  = -Infinity;
                            }
                        }
            
                        // sort by relevance:
                        dat2.sort(fancysort("relevance"));
                        
    
                        // truncate to the top R tokens:
                        var top_terms = dat2.slice(0, number_top_keywords_name);
                        //console.log('cuales son los nombres de esto', top_terms, 'number top keywords', number_top_keywords_name, 'dat2', dat2);
                        
                        var name_string = '';
    
                        for (var i=0; i < top_terms.length; i++){
                        
                        
                            name_string += top_terms[i].Term+" "
                        }
                        
                        name_topics_circles[topicID + d.topics] = name_string 
    
                        return (topicID + d.topics);
                    });    
    }

    
  

    function visualize(data) {
        console.log('esto es data dentro de la funcion visualize', data);
        // set the number of topics to global variable K:
        ////console.log("este data yo recibi", data)
        is_human_in_the_loop = data['human_in_the_loop'];
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
        /*
        mdsData3 = [];
        for (var i = 0; i < data['token.table'].Term.length; i++) {
            var obj = {};
            for (var key in data['token.table']) {
                obj[key] = data['token.table'][key][i];
            }
            mdsData3.push(obj);
        }
        */

        
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

        //assign name to array
        d3.select("#name_topics")
                    .data(mdsData)
                    .enter()
                    .each(
                    function(d) {
                        var dat2 = lamData.filter(function(e) {
                            return e.Category == "Topic"+d.topics;s
                        });
                        
    
                        // define relevance:
                        for (var i = 0; i < dat2.length; i++) {
                            dat2[i].relevance = lambda.current * dat2[i].logprob +
                                (1 - lambda.current) * dat2[i].loglift;
    
                            if(isNaN(dat2[i].relevance)){
                                dat2[i].relevance  = -Infinity;
                            }
                        }
            
                        // sort by relevance:
                        dat2.sort(fancysort("relevance"));
                        
    
                        // truncate to the top R tokens:
                        var top_terms = dat2.slice(0, number_top_keywords_name);
                        
                        var name_string = '';
    
                        for (var i=0; i < top_terms.length; i++){
                        
                        
                            name_string += top_terms[i].Term+" "
                        }
                        
                        name_topics_circles[topicID + d.topics] = name_string 
    
                        return (topicID + d.topics);
                    });

        
        
                
        
        

        // Create the topic input & lambda slider forms. Inspired from:
        // http://bl.ocks.org/d3noob/10632804
        // http://bl.ocks.org/d3noob/10633704
        init_forms(topicID, lambdaID);

        // When the value of lambda changes, update the visualization
            
        d3.select("#"+lambdaID)
            .on("mouseup", function() {

                
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
                ////////////console.log("hice click en esti", "#"+lambdaIDRightPanel)
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
                if(el.value >=threshold){ //HAY QUE CAMBIA RESTO, HAY DOS THRESHOLD AHORA!
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
                        //var real_topic_id = topic_order_2[topic_id_in_model]-1
                    
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

                        if(isNaN(dat2[i].relevance)){
                            dat2[i].relevance  = -Infinity;
                        }
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
           var node_padding = 25
            //////////console.log("este es el graph que recibo", graph)
            d3.selectAll('#svgCentralSankeyDiv').remove();
            d3.selectAll('#divider_central_panel_sankey').remove();
            
            var svgCentralSankeyDiv = d3.select("#CentralPanel").append("div")
            svgCentralSankeyDiv.attr("id", "svgCentralSankeyDiv")

            var divider_central_panel_sankey = document.createElement("hr");
            divider_central_panel_sankey.setAttribute("class", "rounded");
            divider_central_panel_sankey.setAttribute("id", "divider_central_panel_sankey");
            document.getElementById("svgCentralSankeyDiv").appendChild(divider_central_panel_sankey) 


            var margin = { top: 10, right: 10, bottom: 10, left: 10 } // ocupar estos margenes

            //get width, height according to client's window
            var bounds_svgCentralSankey = d3.selectAll('#svgCentralSankeyDiv').node().getBoundingClientRect();
            var user_width_sankey = bounds_svgCentralSankey.width - margin.left - margin.right;
            var user_height_sankey= bounds_svgCentralSankey.height - margin.top - margin.bottom;

            
            

            d3.selectAll('#svg_sankey').remove();
        
            
            var nodes_filtered_set = new Set();

            //get min_target_node_value
            graph.links.filter(function(el){

                
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
            );





            //////console.log("este es el graph, ",graph)
            var links_filtered =  graph.links.filter(function(el){
                return ((threshold_min <= el.value.toFixed(2) && el.value.toFixed(2) <= threshold_max));
                }
            );

            //add a link dummy para que siempre dibuje algo
            
            if( links_filtered.length == 0){
                
            }



            var margin = {top: 10, right: 10, bottom: 10, left: 10};
            
            var formatNumber = d3.format(",.2f"),    // two decimal places
                format = function(d) { 
                    if(scenario_2_is_baseline_metric == true){
                        return "distance: "+formatNumber(d);

                    }else{
                        return "similarity: "+formatNumber(d);

                    }
                
                },
                color = d3.scaleOrdinal(d3.schemeAccent);
            


            var svg_sankey = d3.select("#svgCentralSankeyDiv").append("svg")// #CentralPanel
                .attr("width", "100%")
                .attr("height", "100%")
                .attr("id", "svg_sankey");
                

            
            //I deleted the filtered of nodes. Sankey diagram shows all the nodes (even if these nodes don't have any other similarities. I could add a different color even!. Thus 
            //we could detect original topics. Not only the topics that are similar)
            var nodes_filtered = graph.nodes
            var sankey = d3.sankey()
            .nodeWidth(36)
            .nodePadding(node_padding)
            .size([user_width_sankey, user_height_sankey])
            .nodes(nodes_filtered) //it receives all the nodes
            .min_target_node_value(min_target_node_value)
            .links(links_filtered) //only the links between certain similarity scores appears
            .jsonDataArray([jsonData,jsonData_2])
            .layout(1); //32


            var path = sankey.link();

            var link = svg_sankey.append("g").selectAll(".link")
                .data(links_filtered)
                .enter().append("path")
                .filter(function(d){
                    return d.value;
                })
                .attr("class", "link") //
                .attr("d", path)
                .style("stroke-width", function(d) {     
                    return Math.max(1, d.dy)
                
                })
                .sort(function(a, b) { return b.dy - a.dy; }); // el dy de aqui tambien hay que modificarlo

            
    
            link.append("title")
                .text(function(d) {
                    return name_topics_sankey[topicID + d.source.node] + " → " + 
                    name_topics_sankey[topicID + d.target.node] + "\n" + format(d.value);});
                    
        
            // add in the nodes

            var node = svg_sankey.append("g").selectAll(".node")
                .data(nodes_filtered)//.data(graph.nodes)
                .enter().append("g")
                .attr("class", "node")
                .attr("transform", function(d) { 
                    return "translate(" + d.x + "," + d.y + ")"; }) // el d.y de aqui tambien hay que modificarlo
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
        
            // add the rectangles for the nodes
            node.append("rect")
                .attr("id", function(d){
                    return "node_"+d.node //que esta sea la id unica del nodo
                })
                .attr("height", function(d){
                    if(d.node>=min_target_node_value){ //model 2
                        
                        var Freq = jsonData_2.mdsDat.Freq[d.node-min_target_node_value]    
                        Freq = Math.round(Freq * 10) / 10  
                        
                        

                  
                    }
                    else{
                        var Freq = jsonData.mdsDat.Freq[d.node]                       
                        Freq = Math.round(Freq * 10) / 10  
                    }
                    
                    //return  Freq/100*(user_height_sankey-(min_target_node_value*1.5*node_padding));
                    return  d.dy; 
                    
                }
                ) 
                .attr("width", sankey.nodeWidth())
                .style("fill", function(d) { 
                    if(d.node < min_target_node_value){

                        return color1_1;
                        
                    }
                    else{
                        return color2_1;
                        
                    }
                     
                })
                .style("stroke", function(d) { 
                    return d3.rgb(d.color).darker(2); })
                .style("opacity", 0.6)
                .append("title")
                    .text(function(d) { 
                        return name_topics_sankey[topicID + d.node] ;}) 
                .on("click", function(){
                    
                });
        
        // add in the title for the nodes
            node.append("text")
                .attr("x", -6)
                .attr("y", function(d) { return d.dy / 2; })
                .attr("dy", ".35em")
                .attr("width", function(d) {
                    return 0.25*d3.selectAll('#svg_sankey').node().getBoundingClientRect().width
                    
                })
                .attr("class", "txt")
                .attr("font-weight", "bold")
                .attr("text-anchor", "end")
                .attr("transform", null)
                .text(function(d){
                    if(d.node>=min_target_node_value){ //model 2
                        
                        var Freq = jsonData_2.mdsDat.Freq[d.node-min_target_node_value]    
                        var freq_current_topic = Math.round(Freq * 10) / 10  
                        
                        

                  
                    }
                    else{
                        var Freq = jsonData.mdsDat.Freq[d.node]                       
                        var freq_current_topic = Math.round(Freq * 10) / 10  
                    }



                    return "("+freq_current_topic+"%) "+ name_topics_sankey[topicID + d.node] ;}
                    //return name_topics_sankey[topicID + d.node] ;}                                                
                ) //.text(function(d) { return d.name; })
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
                d3.select("#"+last_clicked_model_2).style("fill",color2_1)
            }
            if(last_clicked_model_1!=-1){
                d3.select("#"+last_clicked_model_1).style("fill",color1_1)
            }

            
            
            if(isSettingInitial){
                real_last_clicked_sankey_model_1 = nodes_filtered[0];
                real_last_clicked_sankey_model_2 = nodes_filtered[min_target_node_value];
                
                topic_on_sankey(real_last_clicked_sankey_model_1, min_target_node_value);
                topic_on_sankey(real_last_clicked_sankey_model_2, min_target_node_value);
            }
            
            d3.selectAll('.txt').call(dotme);

        }

        function dotme(text) {
            
            text.each(function() {
                var text = d3.select(this);
                var words = text.text().split(/\s+/);
                
                var ellipsis = text.text('').append('tspan').attr('class', 'elip').text('...');
                
                var width = parseFloat(text.attr('width')) - ellipsis.node().getComputedTextLength();
                var numWords = words.length;
                
                var tspan = text.insert('tspan', ':first-child').text(words.join(' '));
                
                
                while (tspan.node().getComputedTextLength() > width && words.length) {
                    words.pop();
                    tspan.text(words.join(' '));
                }
                
                if (words.length === numWords) {
                    ellipsis.remove();
                }
            });
        }
    

        
        function get_topics_sorted_by_distance(mdsData, lambda_lambda_topic_similarity_current, vis_state_topic){
            //revisar el topic mergin 1 que recibe!!!
            
            var new_positions = new_circle_positions[lambda_lambda_topic_similarity_current]
            //save the index, it is important to mantaint it after sorting
            var new_positions_dict = {};
                for(var i=0; i<new_positions.length; i++){
                    new_positions_dict[i+1] = new_positions[i]
                }
    
              // Create items array
            var items = Object.keys(new_positions_dict).map(function(key) {
                return [key, new_positions_dict[key]];
            });
            
            // Sort the array based on the second element. Using distance
            const distance = (coor1, coor2) => {
                const x = coor2[0] - coor1[0];
                const y = coor2[1] - coor1[1];
                return Math.sqrt((x*x) + (y*y));
            };
            
            items.sort(function(first, second) {
                return distance(new_positions_dict[vis_state_topic], first[1]) - distance(new_positions_dict[vis_state_topic], second[1]);            
            });
            //this is the final result

            var new_topic_names_sorted = []
            for(var i = 0; i<items.length; i++){
                new_topic_names_sorted.push(name_topics_circles[topicID + items[i][0]])
            }

            return new_topic_names_sorted
        }

        function findWithAttr(array, attr, value) {
            for(var i = 0; i < array.length; i += 1) {
                if(array[i][attr] === value) {
                    return i;
                }
            }
            return -1;
        }

        Array.prototype.sum = function (prop) {
            var total = 0
            for ( var i = 0, _len = this.length; i < _len; i++ ) {
                total += this[i][prop]
            }
            return total
        }
        
        //https://flaviocopes.com/how-to-clone-javascript-object/
        //https://lodash.com/docs/4.17.15#cloneDeep
        function save_state_data(){
            //before merging/ splitting, save the current state (in case we want to reverse these changes)

            var current_state_dict = {};

            

            current_state_dict.relevantDocumentsDict = _.cloneDeep(relevantDocumentsDict);
            
            current_state_dict.lamData = _.cloneDeep(lamData);
            current_state_dict.mdsData = _.cloneDeep(mdsData);
            current_state_dict.new_circle_positions = _.cloneDeep(new_circle_positions);
            current_state_dict.name_topics_circles = _.cloneDeep(name_topics_circles);
            current_state_dict.current_topic_id = _.cloneDeep(vis_state.topic);
            //radio input infromation for topic splitting
            current_state_dict.slider_topic_splitting_values = _.cloneDeep(slider_topic_splitting_values);

            old_topic_model_states.push(current_state_dict);

            //console.log("en el merge/splitting acabo de guardar este estado", current_state_dict);
            //console.log("en la pila tengo esto",old_topic_model_states);
            if(old_topic_model_states.length>0){
                document.getElementById(topicReverse).disabled = false;

            }
            else{
                document.getElementById(topicReverse).disabled = true;

            }
        }
        
        function splitting_topics_document_based_scenario_1(){
            $("#loadMe").modal();

            var postDataTopicSplitting = {
                new_document_seeds: slider_topic_splitting_values[splitting_topic],
                old_circle_positions: new_circle_positions,
                topic_id: vis_state.topic,
                current_number_of_topics: Object.values(new_circle_positions['0.0']).length,
                //mdsData: mdsData, 
                //lamData: lamData                
            };
            console.log('este es el numero de topicos actual que envio', postDataTopicSplitting);

            //4.- Create new new_position circle arrray
            //console.log('Se mando estos datos en este arreglo', postDataTopicSplitting);
            var new_dict_topic_splitting; 
            $.ajax({
                type: 'POST',
                url: '/Topic_Splitting_Document_Based',
                async: false,
                data: JSON.stringify(postDataTopicSplitting),
                success: function(data) {
                                
                    new_dict_topic_splitting = data                    
                },
                error: function(XMLHttpRequest, textStatus, errorThrown) { 
                    alert("Status: " + textStatus); alert("Error: " + errorThrown); 
                }, 
                contentType: "application/json"             
            });


            global_topic_splitting_data = new_dict_topic_splitting;
            new_circle_positions = JSON.parse(new_dict_topic_splitting['new_circle_positions']); 
           
            //1. Update relevantDocumentsDict
            console.log('estos eran los documentos antes', relevantDocumentsDict);
            relevantDocumentsDict = JSON.parse(new_dict_topic_splitting['relevantDocumentsDict_fromPython'].replace(/\bNaN\b/g, "null"));
            console.log('estos eran los documentos despues', relevantDocumentsDict);

            //update lambdata with the new informsation
            console.log('ojo este es el mds data antes de actualizar en topic splitting,', mdsData)
            updateTopicNamesCircles(new_dict_topic_splitting['PreparedDataObtained_fromPython']);
            console.log('ojo este es el mds data despues de actualizar en topic splitting,', mdsData)

            //see_most_relevant_keywords(12)

            createMdsPlot(1, mdsData, lambda_lambda_topic_similarity.current); //update central panel

            topic_on(document.getElementById(topicID+vis_state.topic));
            slider_topic_splitting_values[splitting_topic] = {};
            $("#loadMe").modal('hide');

                                
        }

      

        function merging_topics_scenario_1(topic_name_1, topic_name_2){
            console.log(' aqui estoy en el mergin');
            $("#loadMe").modal();

    
            //get index topic from name    
            var current_index = 0;
            for (var [key, value] of Object.entries(name_topics_circles)) {
                //console.log("topic_name_1", topic_name_1.trim());
                //console.log("value ", value.trim());
                if(value.trim() == topic_name_1.trim()){
                
                    var index_topic_name_1 = current_index;
                }
                if(value.trim() == topic_name_2.trim()){
                    var index_topic_name_2 = current_index;
                }
                current_index+=1;
            }
            
            //1.- Join relevant documents

            for (var row in relevantDocumentsDict)
            {             

                var new_prob_documents = relevantDocumentsDict[row][index_topic_name_1]+relevantDocumentsDict[row][index_topic_name_2];
                relevantDocumentsDict[row][index_topic_name_1] = new_prob_documents;
                relevantDocumentsDict[row][index_topic_name_2] = new_prob_documents;
            }
            
            
            // 2.- Join top keywords
            var terms_topic_1 = lamData.filter(function(d) {
                return d.Category == "Topic" + (index_topic_name_1+1); //we have to add '1' to index_topic_name, because prepareddata starts from 1 instead of 0
            });
            var terms_topic_2 = lamData.filter(function(d) {
                return d.Category == "Topic" + (index_topic_name_2+1);
            });
            

            
            var total_sum_frequency_corpus = terms_topic_1.sum("Total");
            var contador = 0;
            for(var i = 0; i < terms_topic_1.length; i += 1) {            //we have a 'matrix'. There is the same information for all the terms.                                                                                 
                var row_topic_1 = terms_topic_1[i];
                var row_topic_2 = terms_topic_2.find( row => row.Term ===  terms_topic_1[i].Term);

                var new_probability_term = Math.exp(row_topic_1.logprob)+Math.exp(row_topic_2.logprob);
                var new_logprob = Math.log(new_probability_term);                                    
                var new_loglift = Math.log(new_probability_term/(row_topic_1.Total/total_sum_frequency_corpus));                    
                var new_frequency_term = row_topic_1.Freq+row_topic_2.Freq;     



                row_topic_1.logprob = new_logprob;
                row_topic_2.logprob = new_logprob;

                
                row_topic_1.loglift = new_loglift;
                row_topic_2.loglift = new_loglift;
                
                row_topic_1.Freq = new_frequency_term;
                row_topic_2.Freq = new_frequency_term;


                var new_relevance = vis_state.lambda * row_topic_1.logprob +(1 - vis_state.lambda) * row_topic_1.loglift;
                //console.log("en APPLY MERGING TOPIC TENGO ESTOS VALORES", vis_state.lambda, lambda.current ); retorna los ismos valores.


                if(isNaN(new_relevance)){
                    new_relevance = -Infinity;
                }
                

                row_topic_1.relevance = new_relevance;
                row_topic_2.relevance = new_relevance;

           
                
                if(row_topic_1.relevance != row_topic_2.relevance){
                    console.log("puta nacho, era esta weaaaa ME LA QUIERO CORTAR", row_topic_1, row_topic_2)
                }
                contador+=1;
                

            }      
                        

            terms_topic_1.sort(fancysort("relevance"));
            terms_topic_2.sort(fancysort("relevance"));

 
            

            //3.- Update frequency of mdsData

            var new_frequency =  mdsData[index_topic_name_1].Freq+mdsData[index_topic_name_2].Freq;

            
            mdsData[index_topic_name_1].Freq =new_frequency;
            mdsData[index_topic_name_2].Freq = new_frequency;


            //4.- Pass to python, the new relevant documents and the new Lambdata
            //Python shoudl recalculate the new topic similarity metric and the new positions!!
            
            var postData = {
                relevantDocumentsDict_new: relevantDocumentsDict,
                lamData_new: lamData,
                omega_value: vis_state.lambda_lambda_topic_similarity,
                old_circle_positions: new_circle_positions,
                index_topic_name_1: index_topic_name_1,
                index_topic_name_2: index_topic_name_2,
                
            };

            //4.- Create new new_position circle arrray

            $.ajax({
                type: 'POST',
                url: '/get_new_topic_vector',
                async: false,
                data: JSON.stringify(postData),                
                success: function(data) {
                                
                    new_circle_positions = data
                },
                contentType: "application/json",
                dataType: 'json'

             });


            //5.- get new topic name
            //console.log("AQUIII QUEREMOS BANEAR UNA ID!!!!")

            
            var new_merged_topic_name = name_topics_circles[topicID + (index_topic_name_1+1)].trim()+' - '+ name_topics_circles[topicID + (index_topic_name_2+1)].trim();
            name_topics_circles[topicID + (index_topic_name_1+1)] = new_merged_topic_name;
            name_topics_circles[topicID + (index_topic_name_2+1)] = new_merged_topic_name+"-delete";
            merged_topic_to_delete.push(index_topic_name_2+1);
            name_merged_topic_to_delete.push(new_merged_topic_name+"-delete");
            
            

            d3.selectAll('#svgMdsPlot').remove();
            d3.selectAll('#divider_central_panel').remove();

            document.getElementById("renameTopicId").value = name_topics_circles[topicID + vis_state.topic];
            $('#idTopic').html(topicID + vis_state.topic);



            createMdsPlot(1, mdsData, lambda_lambda_topic_similarity.current); //update central panel
            topic_on(document.getElementById(topicID+vis_state.topic));         
            $("#loadMe").modal('hide');
            console.log(' fin del merging, debi haberloc errado');


        }



        function createMdsPlot(number, mdsData, lambda_lambda_topic_similarity){

            
            
            testing_mdsData = mdsData;

            //if  previous mdsplot exists, remove it
            d3.selectAll('#svgMdsPlot').remove();
            d3.selectAll('#divider_central_panel').remove();

            //we need to append this to the central panel, not to the old svg
            //all draws of central panel must appear in this svg variable

            var divider_central_panel = document.createElement("hr");
            divider_central_panel.setAttribute("class", "rounded");
            divider_central_panel.setAttribute("id", "divider_central_panel");
            document.getElementById("CentralPanel").appendChild(divider_central_panel) 
            

            var svg = d3.select("#CentralPanel").append("svg")
                        .attr("width", "100%")
                        .attr("height", "85%")
                        .attr("id", "svgMdsPlot")
                        


            var margin = { top: 90, right: 90, bottom: 90, left: 90 } // ocupar estos margenes

            //get width, height according to client's window
            var bounds = d3.selectAll('#svgMdsPlot').node().getBoundingClientRect();
            
            var user_width = bounds.width; 
            var user_height = bounds.height;
            
            var mdsheight = (user_height-margin.top-margin.bottom);
            var mdswidth = (user_width-margin.left-margin.right);
            var mdsarea = mdsheight * mdswidth;

            // Create a group for the mds plot Bubbles visualization
            d3.selectAll('#'+leftPanelID).remove();

            var mdsplot = svg.append("g")
                .attr("id", leftPanelID) //now is central panel no leftpanel
                .attr("class", "points")
                .attr("transform", "translate("+margin.left+","+margin.top+")")                                



            mdsplot
                .append("rect")
                .attr("x", 0)
                .attr("y", 0)
                .attr("height", "100%")
                .attr("width", "100%")
                .attr("opacity", 0) //.style("fill", color1_1)
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
            //console.log('en el createmdsplot tenemos esto', mdsData)
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
            
            
            var xdiff = xrange[1] - xrange[0],
                xpad = 0.05;

            var yrange = d3.extent( getCol(new_positions, 1));
            
            var ydiff = yrange[1] - yrange[0],
                ypad = 0.05;
            

            if (xdiff > ydiff) {
                var xScale = d3.scaleLinear()
                        .range([0, mdswidth*0.95])
                        .domain([xrange[0] - xpad * xdiff, xrange[1] + xpad * xdiff]);

                var yScale = d3.scaleLinear()
                        .range([mdsheight*0.95, 0])
                        .domain([yrange[0] - 0.5*(xdiff - ydiff) - ypad*xdiff, yrange[1] + 0.5*(xdiff - ydiff) + ypad*xdiff]);
            } else {


                var xScale = d3.scaleLinear()
                        .range([0, mdswidth*0.95])
                        .domain([xrange[0] - 0.5*(ydiff - xdiff) - xpad*ydiff, xrange[1] + 0.5*(ydiff - xdiff) + xpad*ydiff]);
                var yScale = d3.scaleLinear()
                        .range([mdsheight*0.95, 0])
                        .domain([yrange[0] - ypad * ydiff, yrange[1] + ypad * ydiff]);
            }


            // draw circles
            
            points.append("circle")
                .attr("class", "dot")
                .style("opacity",0.2)
                .style("fill", color1_1)
                .attr("r", function(d) {
                    
                    return (Math.sqrt((mdsData[d.topics-1].Freq/100)*mdswidth*mdsheight*circle_prop/Math.PI)); //se hace esto porque el new_positions array no inclue 'Freq', en cambioe el MdsDATA YA LO OBTIENE
                    
                })
                .attr("cx", function(d) {
                    //console.log('este es el id', d.topics-1);
                    //console.log('estas son las posiciones', new_positions);
                    testing_var = new_positions;
                    return (xScale(+new_positions[d.topics-1][0])); 


                })
                .attr("cy", function(d) {
                    //return (yScale(+d.y));
                    return (yScale(+new_positions[d.topics-1][1]));
                })
                .attr("stroke", "black")
                .attr("id", function(d) {        
                    //console.log("estas son las idssss de los topicooos", d.topics)            
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
                    
                    
                    topic_on(this);                
                })
                .append("title")
                    .text(function(d) { 
                        //console.log("este es el nombre del topico, ", name_topics_circles[topicID + d.topics] )
                        return name_topics_circles[topicID + d.topics] ;});

            // text to indicate topic
            

        points.append("text")
        .attr("class", "txt")
        .attr("width", function(d) {
            
            return (2*Math.sqrt((mdsData[d.topics-1].Freq/100)*mdswidth*mdsheight*circle_prop/Math.PI))
        })
        .attr("x", function(d) {
            
            return (xScale(new_positions[d.topics-1][0]));

        })
        .attr("y", function(d) {
            
            return (yScale(new_positions[d.topics-1][1]));
        })
        .attr("id", function(d) {        
            return ("text-"+topicID + d.topics);
        })
        .attr("stroke", "black")
        .style("stroke-opacity", .2)
        .attr("opacity", 1)
        .style("text-anchor", "middle")
        .style("font-size", "11px")                //.style("fontWeight", 50)
        .text(function(d) {
            var freq_current_topic = Math.round(mdsData[d.topics-1].Freq* 10) / 10;
            
            return "("+freq_current_topic+"%) "+name_topics_circles[topicID + d.topics];
            
        });



     

        //overflow-text in svg
       
        d3.selectAll('.txt').call(dotme);
        
        
        
        //remove topic merged
        for(var i = 0; i<merged_topic_to_delete.length; i++){
            var d_topics_current = merged_topic_to_delete[i];
            d3.selectAll('#text-'+topicID + d_topics_current).remove();
            d3.selectAll("#circles_center-"+topicID + d_topics_current).remove();            
            d3.selectAll('#'+topicID + d_topics_current).remove();
            //console.log("topico borradoooo")

        }
        arrangeCircles();        
        //arrangeLabels();

        }
               
        

        /* This function evaluate an overlap between the circles . If there is a overlap, the circles are moved*/
        function arrangeCircles() {
            var move = 1;
            var iterations = 0;
            while(move>0 && iterations < 5000) {
              move = 0;
              
              iterations+=1;              
              d3.selectAll(".dot")
                 .each(function() {
              
                   var that = this,
                       a = this.getBoundingClientRect();
              
                       
                   d3.selectAll(".dot")
                      .each(function() {
                        if(this != that) {
                          var b = this.getBoundingClientRect();
                          
                          
                          var x_1 = a.left + (a.width * 0.5);
                          var y_1 = a.top + (a.height * 0.5);

                          var x_2 = b.left + (b.width * 0.5);
                          var y_2 = b.top + (b.height * 0.5);
                          
                          
                          var distances_to_center = Math.pow(((Math.pow((x_2-x_1),2)) +(Math.pow((y_2-y_1),2))),0.5);
                          var r1 = a.width*0.5;
                          var r2 = b.width*0.5;

                          
                          if(r1>0 && r2>0 && r1+r2 >= distances_to_center){
                          

                            var dx = (Math.max(0, a.right - b.left) +
                                     Math.min(0, a.left - b.right)) * 0.005,
                                dy = (Math.max(0, a.bottom - b.top) +
                                     Math.min(0, a.top - b.bottom)) * 0.005,
                          
                                tt = [d3.select(this).attr("cx"), d3.select(this).attr("cy")],
                          
                                to = [d3.select(that).attr("cx"), d3.select(that).attr("cy")];
                          
                            move += Math.abs(dx) + Math.abs(dy);

                            var text_this = d3.selectAll("#text-"+d3.select(this).attr("id"));
                            var text_that = d3.selectAll("#text-"+d3.select(that).attr("id"));
                          
                            
                            
                            to.translate = [ parseFloat(to[0]) + parseFloat(dx), parseFloat(to[1]) + parseFloat(dy) ];
                            tt.translate = [ parseFloat(tt[0]) - parseFloat(dx), parseFloat(tt[1]) - parseFloat(dy) ];
                            

                            
                            //move circles
                            d3.select(this).attr("cx", tt.translate[0]);
                            d3.select(this).attr("cy", tt.translate[1]);
                            d3.select(that).attr("cx", to.translate[0]);
                            d3.select(that).attr("cy", to.translate[1]);

                            //move labels
                            text_this.attr("x", tt.translate[0]);
                            text_this.attr("y", tt.translate[1]);
                            text_that.attr("x", to.translate[0]);
                            text_that.attr("y", to.translate[1]);



                            a = this.getBoundingClientRect();
                          }                          
                        }
                      });
                 });
            }
        }


        //http://bl.ocks.org/larskotthoff/11406992
        /* This function is not useful when arrangeCircles() is on. Given that with arrangeCircle there will not appear an overlap*/
        /*Arrange labels detect colission between labels, if there is a colission, the labels will be moved*/ 
        function arrangeLabels() {
            var move = 1;
            var iterations = 0;
            while(move>0 && iterations < 50) {
              move = 0;
              
              iterations+=1;              
              d3.selectAll(".txt")
                 .each(function() {
                     
                   var that = this,
                       a = this.getBoundingClientRect();
                   d3.selectAll(".txt")
                      .each(function() {
                        if(this != that) {
                          var b = this.getBoundingClientRect();
                          if((Math.abs(a.left - b.left) * 2 < (a.width + b.width)) &&
                             (Math.abs(a.top - b.top) * 2 < (a.height + b.height))) {
                            
                            //console.log("We found an overlap",iterations, this, that);
                            var dx = (Math.max(0, a.right - b.left) +
                                     Math.min(0, a.left - b.right)) * 0.01,
                                dy = (Math.max(0, a.bottom - b.top) +
                                     Math.min(0, a.top - b.bottom)) * 0.02,
                                
                                tt = [d3.select(this).attr("x"), d3.select(this).attr("y")],
                                
                                to = [d3.select(that).attr("x"), d3.select(that).attr("y")];
                                
                            move += Math.abs(dx) + Math.abs(dy);
                                                                                                                
                            to.translate = [ parseFloat(to[0]) + parseFloat(dx), parseFloat(to[1]) + parseFloat(dy) ];
                            tt.translate = [ parseFloat(tt[0]) - parseFloat(dx), parseFloat(tt[1]) - parseFloat(dy) ];
                            

                            d3.select(this).attr("x", tt.translate[0]);
                            d3.select(this).attr("y", tt.translate[1]);
                            d3.select(that).attr("x", to.translate[0]);
                            d3.select(that).attr("y", to.translate[1]);

                            a = this.getBoundingClientRect();
                          }
                        }
                      });
                 });
            }
        }
          
        
       if( type_vis === 1){
           
 



            createMdsPlot(1, mdsData, lambda_lambda_topic_similarity.current)        
            createBarPlot("#BarPlotPanelDiv", dat3, barFreqsID,"bar-totals", "terms", "bubble-tool", "xaxis", R) //esto crea el bar plot por primera vez. 
            d3.selectAll('#tableRelevantDocumentsClass_Model1').attr("transform", "translate("  +0 + "," +0+ ")")

            
            splitting_topic= vis_state.topic // es 1 by default
            
            document.getElementById("renameTopicId").value = name_topics_circles[topicID + vis_state.topic]
            $('#idTopic').html(topicID + vis_state.topic);
            topic_on(document.getElementById(topicID+vis_state.topic))
        
       }

       if(type_vis === 2){
        
  
            get_name_node_sankey(matrix_sankey[lambda_lambda_topic_similarity.current], vis_state.lambda_topic_similarity)
           
            // Add barplot into the left panel 
            createBarPlot("#BarPlotDiv_zero", dat3, barFreqsID,"bar-totals", "terms", "bubble-tool", "xaxis", number_terms_sankey) //esto crea el bar plot por primera vez.             
            // Add barplot into the right panel
            createBarPlot("#DocumentsPanel", dat3, barFreqsID_2,"bar-totals_2", "terms_2", "bubble-tool_2", "xaxis_2", number_terms_sankey) //hay que modificar la altura aqui en funcion del alto de las barras

            // Add documents into the left panel. 
           var RelevantDocumentsTableDiv = document.createElement("div");
           RelevantDocumentsTableDiv.setAttribute("id", "RelevantDocumentsTableDiv");
           RelevantDocumentsTableDiv.setAttribute("class", "RelevantDocumentsSankeyDiagram mt-4");
           document.getElementById("BarPlotPanelDiv").appendChild(RelevantDocumentsTableDiv) 
           const  div = document.getElementById('RelevantDocumentsTableDiv');
           div.insertAdjacentHTML('afterbegin', '<table  id="tableRelevantDocumentsClass_Model1" class="table table-hover"> <thead> <tr> <th class="text-center" data-field="topic_perc_contrib" scope="col">%</th> <th class="text-center" data-field="text" scope="col">Tweet</th> </tr> </thead> </table>');


           // Add documents into the right panel. 
           var RelevantDocumentsTableDiv_2 = document.createElement("div");
           RelevantDocumentsTableDiv_2.setAttribute("id", "RelevantDocumentsTableDiv_2");
           RelevantDocumentsTableDiv_2.setAttribute("class", "RelevantDocumentsSankeyDiagram mt-4");
           document.getElementById("DocumentsPanel").appendChild(RelevantDocumentsTableDiv_2) 
           const  div_2 = document.getElementById('RelevantDocumentsTableDiv_2');
           div_2.insertAdjacentHTML('afterbegin', '<table  id="tableRelevantDocumentsClass_Model2" class="table table-hover"> <thead> <tr> <th class="text-center" data-field="topic_perc_contrib" scope="col">%</th> <th class="text-center" data-field="text" scope="col">Tweet</th> </tr> </thead> </table>');

           visualize_sankey(matrix_sankey[lambda_lambda_topic_similarity.current], vis_state.min_value_filtering, vis_state.max_value_filtering)
       }
       

        $('#CentralPanelTopicSplittingRow').on('post-body.bs.table', function (e) {
            //highlight relevant keywords. it is not ready. but it is not urgent
            /*
            var trs = $('#CentralPanelTopicSplittingRow').find('tbody tr').children();

            var book = $('#DocumentsPanel_TopicSplitting');
            var original_book = _.cloneDeep(book);
            //console.log('a veeer, estos son los trs', trs);
            for (var i = 0; i < trs.length; i++) {
                $(trs[i]).mouseover(function(e) {
                    var current_row_topic_splitting_modal = $(e.currentTarget).closest('table').find('th').eq($(e.currentTarget).index()).data();
                    var index = $(this).closest('tr').index();
                    var current_term = list_terms_for_topic_splitting[index].Term;
                    
                    console.log(list_terms_for_topic_splitting[index].Term);

                    // probemos volver bold estas palabras
                    console.log('this is  the book', book);
                    var lookFor = current_term;
                    //book.html(book.html().replace(lookFor, '<strong>'+ lookFor +'</strong>'));
                    book.html(book.html().replace(lookFor, String(lookFor).bold().bold()));
                });
                $(trs[i]).mouseout(function(e) {
                    console.log('doing mouse up');
                    book = _.cloneDeep(original_book);

                });                     
            };*/            
        });







       
       function createBarPlotTopicSplitting(to_select, dat3, barFreqsID_actual, bar_totals_actual, terms_actual,  splitting, xaxis_class, number_terms){


        
        var termwidth_splitting = 90;
        d3.selectAll("#svg_keywords_topic_splitting").remove();

            
        var svg_topicsplitting = d3.select("#KeywordsPanel_TopicSplitting").append("svg") //BarPlotPanelDiv
        .attr("width", "100%")
        .attr('id',"svg_keywords_topic_splitting")
        .attr("class", "graph-svg-component")
        .attr("height", "100%");
        

        
        var topicDivRightPanel = document.createElement("div");
        topicDivRightPanel.setAttribute("id", "topic_splitting_slider_row")
        topicDivRightPanel.setAttribute("class", "RowDiv")
        document.getElementById("svg_keywords_topic_splitting").appendChild(topicDivRightPanel) 
        

        //Lets draw the term frequency barplot
        //for the first demo, the size of the barplot panel in the topic splitting modal is equal to the size of the barplot panel in tghe scenario 1
        var bounds_barplot_splitting = d3.select("#BarPlotPanelDiv").node().getBoundingClientRect();

       

        var barheight_splitting = barheight  //bounds_barplot_splitting.height - 0.5*termwidth_splitting
        var barwidth_splitting = barwidth   //bounds_barplot_splitting.width - 1.5*termwidth_splitting
    



    
        var barDefault2_splitting = dat3.filter(function(d) {
            return d.Category == "Default";
        });
        
        barDefault2_splitting = barDefault2_splitting.slice(0, number_terms)
       


        
        var y_splitting = d3.scaleBand()
                .domain(barDefault2_splitting.map(function(d) {
                    return d.Term;
                }))
                .rangeRound([0, barheight_splitting])
                .padding(0.15);

        var x_splitting = d3.scaleLinear()
                .domain([1, d3.max(barDefault2_splitting, function(d) {
                    return d.Total;
                })])
                .range([0, barwidth_splitting])
                .nice();
        var yAxis_splitting = d3.axisLeft(y_splitting);

        // Add a group for the bar chart
        var chart_splitting = svg_topicsplitting.append("g")
                .attr("transform", "translate("  +(termwidth_splitting) + "," +50+ ")") //.attr("transform", "translate("  +(mdswidth + margin.left + termwidth) + "," +height_bar+ ")")
                .attr("id", barFreqsID_actual);

        // Bind 'default' data to 'default' bar chart
        var basebars_splitting = chart_splitting.selectAll(to_select + " ."+bar_totals_actual)
                .data(barDefault2_splitting)
                .enter();

        // Draw the gray background bars defining the overall frequency of each word
        basebars_splitting
            .append("rect")
            .attr("class", bar_totals_actual)
            .attr("x", 0)
            .attr("y", function(d) {
                return y_splitting(d.Term);
            })
            .attr("height", y_splitting.bandwidth())
            .attr("width", function(d) {
                return x_splitting(d.Total);
            })
            .style("fill", color1_1)//color2_2
            .attr("opacity", 0.4);

        // Add word labels to the side of each bar
        basebars_splitting
            .append("text")
            .attr("x", -5)
            .attr("class", terms_actual)
            .attr("y", function(d) {
                return y_splitting(d.Term) + 12;
            })
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



        // barchart axis adapted from http://bl.ocks.org/mbostock/1166403
        var xAxis_splitting = d3.axisTop().scale(x_splitting).tickSize(-barheight_splitting).ticks(6);



        chart_splitting.append("g")
            .attr("class", xaxis_class)
            .call(xAxis_splitting);
        


        //Add bar of term frequency estimated for the selected topic




        var topic_id_in_model = vis_state.topic
        var increase = false

        show_bars_withouth_transitions("#svg_keywords_topic_splitting", increase, topic_id_in_model, barFreqsID_actual, bar_totals_actual,terms_actual,'overlay', xaxis_class)



        }

        function createBarPlot(to_select, dat3, barFreqsID_actual, bar_totals_actual, terms_actual,  splitting, xaxis_class, number_terms){

            
            var svg = d3.select(to_select).append("svg") //BarPlotPanelDiv
            .attr("width", "100%")
            .attr("height", "32%");
            

            var bounds_barplot = svg.node().getBoundingClientRect();
            

            barheight = bounds_barplot.height - 0.5*termwidth
            barwidth = bounds_barplot.width - 1.5*termwidth
        
            
        
            var barDefault2 = dat3.filter(function(d) {
                return d.Category == "Default";
            });
            
            barDefault2 = barDefault2.slice(0, R)
            
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
                    .attr("transform", "translate("  +(termwidth) + "," +50+ ")") //.attr("transform", "translate("  +(mdswidth + margin.left + termwidth) + "," +height_bar+ ")")
                    .attr("id", barFreqsID_actual)
                    .attr("class", "BarPlotClass");
            
            if(type_vis == 1 && splitting!=1){

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
                    .style("fill", color1_1)
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
                    .style("fill", color2_1)
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
                .style("fill", color2_2)
                .attr("opacity", 0.4);
            
            // Add word labels to the side of each bar
            basebars
                .append("text")
                .attr("x", -5)
                .attr("class", terms_actual)
                .attr("y", function(d) {
                    return y(d.Term) + 12;
                })
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
                var svgRightPanel = d3.select("#DocumentsPanel").append("div");
                svgRightPanel.attr("id", "svgRightPanel");

                var topicDivRightPanel = document.createElement("div");
                topicDivRightPanel.setAttribute("id", "topic_name_and_buttons_div_right_panel")
                topicDivRightPanel.setAttribute("class", "RowDiv")
                document.getElementById("svgRightPanel").appendChild(topicDivRightPanel) 

                
                var topicNameRightPanel = document.createElement("div");
                topicNameRightPanel.setAttribute("id", "topic_name_div_right_panel")
                topicNameRightPanel.setAttribute("class", "ColumnDiv")
                topicDivRightPanel.appendChild(topicNameRightPanel) 

                var topicButtonsRightPanel = document.createElement("div");
                topicButtonsRightPanel.setAttribute("id", "topic_buttons_div_right_panel")
                topicButtonsRightPanel.setAttribute("class", "ColumnDiv")
                topicDivRightPanel.appendChild(topicButtonsRightPanel) 

                var topic_title_right_panel= document.createElement("span"); 
                topic_title_right_panel.innerText = "Topic: ";
                topicNameRightPanel.appendChild(topic_title_right_panel); 

                var topic_name_selected_2 = document.createElement("span");
                topic_name_selected_2.innerText = ""
                topic_name_selected_2.setAttribute("id", "topic_name_selected_2")
                topicNameRightPanel.appendChild(topic_name_selected_2); 

                var merge_right_panel = document.createElement("button");
                merge_right_panel.setAttribute("id", topicMerge+"rightPanel");
                merge_right_panel.setAttribute("class", "btn btn-primary btnTopic");
                merge_right_panel.setAttribute("disabled", true);
                merge_right_panel.innerHTML = "Merge";
                topicButtonsRightPanel.appendChild(merge_right_panel);

                var split_rigth_panel = document.createElement("button");
                split_rigth_panel.setAttribute("id", topicSplit+"rightPanel");
                split_rigth_panel.setAttribute("class", "btn btn-primary btnTopic");
                split_rigth_panel.setAttribute("disabled", true);
                split_rigth_panel.innerHTML = "Split";
                topicButtonsRightPanel.appendChild(split_rigth_panel);

                var edit2 = document.createElement("button");
                edit2.setAttribute("id", topicEdit2);
                edit2.setAttribute("class", "btn btn-primary btnTopic");
                edit2.innerHTML = "Rename";
                topicButtonsRightPanel.appendChild(edit2);
                d3.select("#"+topicEdit2)
                .on("click", function() {
                    $('#renameTopic2').modal(); 
                    
                    
                });
                
                //add relevance slider into the right panel. 
                var inputDivRightPanel_zero = document.createElement("div");
                inputDivRightPanel_zero.setAttribute("id", "BarPlotDivRightPanel_zero");
                document.getElementById("DocumentsPanel").appendChild(inputDivRightPanel_zero)  //document.getElementById(visID).appendChild(inputDiv); //creo que esto debiera estar unido al svg mejor

                var divider_topic_name_right = document.createElement("hr");
                divider_topic_name_right.setAttribute("class", "rounded");
                document.getElementById("BarPlotDivRightPanel_zero").appendChild(divider_topic_name_right) 

                var inputDivRightPanel = document.createElement("div");
                inputDivRightPanel.setAttribute("id", "BarPlotDivRightPanel");
                document.getElementById("BarPlotDivRightPanel_zero").appendChild(inputDivRightPanel)

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

            d3.selectAll('#'+BarPlotPanelDivId).remove();

            var svgLeftPanel = d3.select("#BarPlotPanel").append("div")
            svgLeftPanel.attr("id", BarPlotPanelDivId)
            //svgLeftPanel.attr("class", "border_box my-1")
            
            var topicDiv = document.createElement("div");
            topicDiv.setAttribute("id", "topic_name_and_buttons_div")
            topicDiv.setAttribute("class", "RowDiv ") //border_box my-1
            
            document.getElementById(BarPlotPanelDivId).appendChild(topicDiv) ////topicDiv.setAttribute("style", "width:100%; height:5%; background-color: red")

        
            var topicNameDiv = document.createElement("div");
            topicNameDiv.setAttribute("id", "topic_name_div")
            topicNameDiv.setAttribute("class", "ColumnDiv")
            topicDiv.appendChild(topicNameDiv) ////topicDiv.setAttribute("style", "width:100%; height:5%; background-color: red")


            var topicButtonsDiv = document.createElement("div");
            topicButtonsDiv.setAttribute("id", "topic_buttons_div")
            topicButtonsDiv.setAttribute("class", "ColumnDiv")
            topicDiv.appendChild(topicButtonsDiv) ////topicDiv.setAttribute("style", "width:100%; height:5%; background-color: red")
            
            var reverse = document.createElement("button");
            reverse.setAttribute("id", topicReverse);

                    
            reverse.setAttribute("class", "btn btn-primary btnTopic");
            reverse.innerHTML = "Undo";
            //reverse.setAttribute("disabled", true);

            var help = document.createElement("button");
            help.setAttribute("id", 'help_button');

                    
            help.setAttribute("class", "btn btn-info btnTopic");
            help.innerHTML = "<i class='fas fa-1x fa-info-circle'></i>";

            var save_data_user_study_button = document.createElement("button");
            save_data_user_study_button.setAttribute("id", 'save_data_user_study_button');

                    
            save_data_user_study_button.setAttribute("class", "btn btn-info btnTopic");
            save_data_user_study_button.innerHTML = "<i class='fas fa-1x fa-file-export'></i>";


            topicButtonsDiv.appendChild(save_data_user_study_button);
            topicButtonsDiv.appendChild(help);
            topicButtonsDiv.appendChild(reverse);
            
            d3.select("#"+topicReverse)
                .on("click", function() {
                    console.log(' este es el largo que tengo en esto', old_topic_model_states.length)
                    $('#ReverseModel').modal(); 
                });
            
            //quizas guardar un json en vez de un pickle
            d3.select('#save_data_user_study_button')
                .on('click', function(){
                    if(type_vis == 1){
                        var user_study_data = {
                            topic_id: vis_state.topic,
                            mdsDat: mdsData,
                            name_topics_circles: name_topics_circles,
                            relevantDocumentsDict_new: relevantDocumentsDict,
                            lamData_new: lamData,
                            omega_value: vis_state.lambda_lambda_topic_similarity,
                            circle_positions: new_circle_positions,   
                            relevance_value: vis_state.lambda     
                        };
                    }else{ // scenario 2                            //lambda_lambda_topic_similarity.current

                        var user_study_data = {
                            topic_id: vis_state.topic,
                            mdsDat: mdsData,
                            name_topics_sankey: name_topics_sankey,
                            relevantDocumentsDict_new: relevantDocumentsDict,
                            lamData_new: lamData,
                            omega_value: vis_state.lambda_lambda_topic_similarity,
                            relevance_value: vis_state.lambda,
                            min_filtering:  vis_state.min_value_filtering, 
                            max_filtering: vis_state.max_value_filtering
                        };
                    }


                    console.log('User study data from Javascript', user_study_data);
        
                    var result; 
                    $.ajax({
                        type: 'POST',
                        url: '/export_user_study_data',
                        async: false,
                        data: JSON.stringify(user_study_data),
                        success: function(data) {
                                        
                            result = data;
                            console.log('esto fue lo q recibi after exporting data with python', result);  
                            $('#export_results_user_study_successfully').modal(); 

                                              
                        },
                        error: function(XMLHttpRequest, textStatus, errorThrown) { 
                            alert("Status: " + textStatus); alert("Error: " + errorThrown); 
                        }, 
                        contentType: "application/json"             
                    });
        
                
                });


            d3.select("#help_button")
                .on("click", function() {
                    if(type_vis==1){
                        if(is_human_in_the_loop == true){ // users can use topic splitting/ topic merging
                            introJs().setOptions({
                                steps: [{
                                  intro: 'Hello! This tutorial will guide you in the usage of this topic modeling visualization tool.'
                                },
                                {
                                  title: 'Global view of topics',
                                  element: document.querySelector('#CentralPanel'),
                                  intro: "The central panel presents a global view of the topics and aims to answer questions <b style='color: #1f77b4;'> How prevalent each topic is?</b>, and <b style='color: #1f77b4;'>How do topics relate to each other? </b>"
                                },
                                {
                                  element: document.querySelector('#svgMdsPlot'),
                                  title: 'How prevalent each topic is?', 
                                  intro: "Each topic is represented as a circle. The area of the circle  indicates how frequent it is regarding its marginal topic distribution"
                                },
                                {
                                    element: document.querySelector('#svgMdsPlot'),
                                    title: 'How do topics relate to each other? ', 
                                    intro: "Similar topics appear closer, while distinct topics appear more distant between each other"
                                },
                                {
                                  element: document.querySelector('#TopicSimilarityMetricPanel'),
                                  title: 'Inter-topic comparison', 
                                  intro: "This slider allows adjusting the similarity between topics. A higher omega score implies higher importance to the most relevant keywords, but a lower significance to the most relevant documents in the topic similarity calculation"
                                },
                                {
                                    element: document.querySelector('#DocumentsPanel_first_scenario'),
                                    title: 'What is the meaning of each topic?', 
                                    intro: "In order to identify the meaning of each topic. This panel provides the most relevant documents associated with the currently selected topic"
                                },
                                {
                                  element: document.querySelector('#barplot_1'),
                                  title: 'Most relevant keywords', 
                                  intro: "Here you can see the  most relevant keywords associated with the currently selected topic."
                                },
                                {
                                    element: document.querySelector('#relevanceSliderDiv'),
                                    title: 'Most relevant keywords', 
                                    intro: "This slider allows adjusting the order of the most relevant keywords. A higher value assigns higher importance to the term's frequency but less priority to its uniqueness."
                                },
                                {
                                    element: document.querySelector('#topic_buttons_div'),
                                    title: 'Rename-Split-Merge topics', 
                                    intro: "Buttons from this panel allow to edit topics: rename, joint two topics, split a topic into two subtopics"
                                },
                                {
                                    element: document.querySelector('#help_button'),
                                    title: 'Ask for help!', 
                                    intro: "Remember that you can always start the interactive tutorial here!"
                                }
    
                              ]
                              }).start();
                        }
                        else{ // users cant use topic splitting and topic mergign
                            introJs().setOptions({
                                steps: [{
                                  intro: 'Hello! This tutorial will guide you in the usage of this topic modeling visualization tool.'
                                },
                                {
                                  title: 'Global view of topics',
                                  element: document.querySelector('#CentralPanel'),
                                  intro: "The central panel presents a global view of the topics and aims to answer questions <b style='color: #1f77b4;'> How prevalent each topic is?</b>, and <b style='color: #1f77b4;'>How do topics relate to each other? </b>"
                                },
                                {
                                  element: document.querySelector('#svgMdsPlot'),
                                  title: 'How prevalent each topic is?', 
                                  intro: "Each topic is represented as a circle. The area of the circle  indicates how frequent it is regarding its marginal topic distribution"
                                },
                                {
                                    element: document.querySelector('#svgMdsPlot'),
                                    title: 'How do topics relate to each other? ', 
                                    intro: "Similar topics appear closer, while distinct topics appear more distant between each other"
                                },
                                {
                                  element: document.querySelector('#TopicSimilarityMetricPanel'),
                                  title: 'Inter-topic comparison', 
                                  intro: "This slider allows adjusting the similarity between topics. A higher omega score implies higher importance to the most relevant keywords, but a lower significance to the most relevant documents in the topic similarity calculation"
                                },
                                {
                                    element: document.querySelector('#DocumentsPanel_first_scenario'),
                                    title: 'What is the meaning of each topic?', 
                                    intro: "In order to identify the meaning of each topic. This panel provides the most relevant documents associated with the currently selected topic"
                                },
                                {
                                  element: document.querySelector('#barplot_1'),
                                  title: 'Most relevant keywords', 
                                  intro: "Here you can see the  most relevant keywords associated with the currently selected topic."
                                },
                                {
                                    element: document.querySelector('#relevanceSliderDiv'),
                                    title: 'Most relevant keywords', 
                                    intro: "This slider allows adjusting the order of the most relevant keywords. A higher value assigns higher importance to the term's frequency but less priority to its uniqueness."
                                },
                                {
                                    element: document.querySelector('#LDAvisContainer-topic-edit'),
                                    title: 'Rename topics', 
                                    intro: "You can use this button to rename a topic"
                                },
                                {
                                    element: document.querySelector('#help_button'),
                                    title: 'Ask for help!', 
                                    intro: "Remember that you can always start the interactive tutorial here!"
                                }
    
                              ]
                              }).start();
                        }
                        
                    }
                    else{ // scenario 2
                        if(scenario_2_is_baseline_metric == false){
                            introJs().setOptions({
                                steps: [
                                {
                                  intro: 'Hello! This tutorial will guide you in the usage of this topic modeling visualization tool.'
                                },
                                {
                                  title: 'Global view of topics',
                                  element: document.querySelector('#CentralPanel'),
                                  intro: "The central panel presents a global view of the topics and aims to answer <b style='color: #1f77b4;'>How topics relate to each other? </b>"
                                },
                                {
                                  element: document.querySelector('#svg_sankey'),
                                  title: 'How topics relate to each other?', 
                                  intro: "Each topic is represented as a box. Its color indicates to which dataset the topic belongs. "
                                },
                                {
                                    element: document.querySelector('#svg_sankey'),
                                    title: 'How  topics relate to each other? ', 
                                    intro: "The link between topics indicates their similarity. A higher similarity is represented with a wider link."
                                },
                                {
                                    element: document.querySelector('#TopicSimilarityMetricPanelFiltering'),
                                    title: 'Filtering links', 
                                    intro: "You can modify this slider to visualize only links between topics with a similarity score between a range of values."
                                  },
                                  {
                                    element: document.querySelector('#RelevantDocumentsTableDiv'), //document.querySelectorAll('.bootstrap-table')[0],
                                    title: 'What is the meaning of each topic?', 
                                    intro: "In order to identify the meaning of each topic. This panel provides the most relevant documents associated with the currently selected topic"
                                },                                
                                {
                                  element: document.querySelector('#TopicSimilarityMetricPanel'),
                                  title: 'Inter-topic comparison', 
                                  intro: "This slider allows adjusting the similarity between topics. A higher omega score implies higher importance to the most relevant keywords, but a lower significance to the most relevant documents in the topic similarity calculation."
                                },
                                {
                                  element: document.querySelector('#BarPlotDiv_zero'),
                                  title: 'Most relevant keywords', 
                                  intro: "Here you can see the most relevant keywords associated with the currently selected topic."
                                },
                                {
                                    element: document.querySelector('#relevanceSliderDiv'),
                                    title: 'Most relevant keywords', 
                                    intro: "This slider allows adjusting the order of the most relevant keywords. A higher value assigns higher importance to the term's frequency but less priority to its uniqueness."
                                },
                                {
                                    element: document.querySelector('#LDAvisContainer-topic-edit'),
                                    title: 'Rename topics', 
                                    intro: "You can use this button to rename a topic"
                                },
                                {
                                    element: document.querySelector('#help_button'),
                                    title: 'Ask for help!', 
                                    intro: "Finally, remember that you can always start the interactive tutorial here!"
                                }                                                                        
    
                              ]
                              }).start();
                        }
                        else{ // scenario 2, metric baseline. 
                            introJs().setOptions({
                                steps: [{
                                  intro: 'Hello! This tutorial will guide you in the usage of this topic modeling visualization tool.'
                                },
                                {
                                  title: 'Global view of topics',
                                  element: document.querySelector('#CentralPanel'),
                                  intro: "The central panel presents a global view of the topics and aims to answer <b style='color: #1f77b4;'>How topics relate to each other? </b>"
                                },
                                {
                                  element: document.querySelector('#svg_sankey'),
                                  title: 'How topics relate to each other?', 
                                  intro: "Each topic is represented as a box. Its color indicates to which dataset the topic belongs. "
                                },
                                {
                                    element: document.querySelector('#svg_sankey'),
                                    title: 'How  topics relate to each other? ', 
                                    intro: "The link between topics indicates the similarity between topics. Topics that are more similar have lower distance scores. A higher similarity is represented with a narrower link."
                                },
                                {
                                    element: document.querySelector('#TopicSimilarityMetricPanelFiltering'),
                                    title: 'Filtering links', 
                                    intro: "You can modify this slider to visualize only links between topics with a distance/similarity  score between a range of values."
                                  },                            
                                  {
                                    element: document.querySelector('#RelevantDocumentsTableDiv'), //document.querySelectorAll('.bootstrap-table')[0],
                                    title: 'What is the meaning of each topic?', 
                                    intro: "In order to identify the meaning of each topic. This panel provides the most relevant documents associated with the currently selected topic"
                                },    
                                {
                                  element: document.querySelector('#BarPlotDiv_zero'),
                                  title: 'Most relevant keywords', 
                                  intro: "Here you can see the most relevant keywords associated with the currently selected topic."
                                },
                                {
                                    element: document.querySelector('#relevanceSliderDiv'),
                                    title: 'Most relevant keywords', 
                                    intro: "This slider allows adjusting the order of the most relevant keywords. A higher value assigns higher importance to the term's frequency but less priority to its uniqueness."
                                },
                                {
                                    element: document.querySelector('#LDAvisContainer-topic-edit'),
                                    title: 'Rename topics', 
                                    intro: "You can use this button to rename a topic"
                                },
                                {
                                    element: document.querySelector('#help_button'),
                                    title: 'Ask for help!', 
                                    intro: "Finally, remember that you can always start the interactive tutorial here!"
                                }                                                                        
                              ]
                              }).start();
                        }
                       
                    }
                });
    

            d3.select("#apply_reverse_topic_model") //el usuario desea continuar con el mergin
                .on("click", function() {
                    //console.log("que bacan, voy a revertir los cambios!!!");
                    //console.log("PRE reverse esto es lo q queda en la pila", old_topic_model_states);

                    var last_state_dict = old_topic_model_states.pop();
                    //console.log("este es mi last state dict", last_state_dict)

                    relevantDocumentsDict = last_state_dict.relevantDocumentsDict;
                    lamData = last_state_dict.lamData;
                    mdsData = last_state_dict.mdsData;
                    new_circle_positions = last_state_dict.new_circle_positions;
                    name_topics_circles = last_state_dict.name_topics_circles;
                    vis_state.topic = last_state_dict.current_topic_id;
                    slider_topic_splitting_values = last_state_dict.slider_topic_splitting_values;



                    //quitar del arreglo de topicos a no mostrar. En un split hay que crear la condicion para saber de que arreglo sacar el ultimo topico baneado
                    merged_topic_to_delete.pop();
                    name_merged_topic_to_delete.pop();


                    d3.selectAll('#svgMdsPlot').remove();
                    d3.selectAll('#divider_central_panel').remove();
        
                    document.getElementById("renameTopicId").value = name_topics_circles[topicID + vis_state.topic]
                    $('#idTopic').html(topicID + vis_state.topic);
        
        
        
                    createMdsPlot(1, mdsData, lambda_lambda_topic_similarity.current); //update central panel
                    topic_on(document.getElementById(topicID+vis_state.topic));
        
                    
                    console.log("debiese haberse actualizado todo");
                    console.log("post reverse esto es lo q queda en la pila", old_topic_model_states);
                    $.ajax({
                        type: 'POST',
                        url: '/undo_merge_splitting',
                        async: false,
                        success: function(data) {
                                        
                            console.log('esto fue lo recibido en el undoooo', data)
                        },
        
                     });
                     console.log('a esta altura tendria q haber realizado el undo merge splitting. etse es el mds data', mdsData)

                    /*

                    if(old_topic_model_states.length!=0){
                        reverse.setAttribute("disabled", false);
                        d3.select("#"+topicReverse).setAttribute("disabled", false);
                        console.log("esto fue lo q seleccione aqui", d3.select("#"+topicReverse));
                        console.log("este reverse es undefined seguri", reverse);
                        

                    }
                    else{
                        reverse.setAttribute("disabled", true);
                        d3.select("#"+topicReverse).setAttribute("disabled", true);
                        console.log("esto fue lo q seleccione aqui", d3.select("#"+topicReverse));
                        console.log("este reverse es undefined seguri", reverse);
                    }
                    console.log("este es el length",old_topic_model_states.length);
                    */
                   if(old_topic_model_states.length>0){
                    document.getElementById(topicReverse).disabled = false;
    
                    }
                    else{
                        document.getElementById(topicReverse).disabled = true;
        
                    }

            });
    
            
           var topic_title= document.createElement("span"); 
           topic_title.innerText = "Topic: ";
           topicNameDiv.appendChild(topic_title); 

            
           var topic_name_selected_1 = document.createElement("span")
           topic_name_selected_1.innerText = ""
           topic_name_selected_1.setAttribute("id", "topic_name_selected_1")
           topicNameDiv.appendChild(topic_name_selected_1); 
            
           var merge = document.createElement("button");
           merge.setAttribute("id", topicMerge);
           merge.setAttribute("class", "btn btn-primary btnTopic"); //merge.setAttribute("disabled", true);
           merge.innerHTML = "Merge";
           topicButtonsDiv.appendChild(merge);

        

           d3.select("#apply_topic_merging") //el usuario desea continuar con el mergin
                .on("click", function() {
                    //hacer_merge = true
                    
                    var merging_final_topic_1 = document.getElementById("merging_topic_1_name").innerText;
                    var merging_final_topic_2 =  $("#selectTopicMerge" ).val()
                    save_state_data()

                    merging_topics_scenario_1(merging_final_topic_1, merging_final_topic_2);
                    console.log("antes reverse", document.getElementById(topicReverse));
                    //document.getElementById(topicReverse).attr('disabled', null);
                    
                    console.log("despues es el reverse", document.getElementById(topicReverse));

                });
       
           d3.select("#"+topicMerge)
               .on("click", function() {
                   if(merging_topic_1!=-1){  
                       $('.merging_topic_1').html(merging_topic_1); //this is one topic wish I would like to merge
                       //populate el dropdown, topics should be sorted according to the distance to the current topic
                       $('#selectTopicMerge').empty();
                       var topics_name_sorted_by_distance = get_topics_sorted_by_distance(mdsData, lambda_lambda_topic_similarity.current, merging_topic_1)
                       $.each(topics_name_sorted_by_distance, function(i, p) {
                           //add the array with the topics sorted according to the distance to the current topic
                           if(i!=0 && ( !(name_merged_topic_to_delete.includes(topics_name_sorted_by_distance[i])))){ //el primer elemento no se ocupa, ya que es el mismo topico con el q se quiere unir. ESTO NO OCURRE ASI EN EL SCENARIO 2. Ojo, tambien chequeamos que ese elemento no haya que borrarse
                            $('#selectTopicMerge').append($('<option></option>').val(topics_name_sorted_by_distance[i]).html(topics_name_sorted_by_distance[i]));
                           }
                           else{
                               ////console.log("no agregamos este", topics_name_sorted_by_distance[i])
                           }                           
                       });
                       $('#MergeModal_new_design').modal();                        
                   }
                   else{ //you need to select a topic first
                       $('#MergeModal_0').modal(); 
                   }
                   
               });

           var split = document.createElement("button");
           split.setAttribute("id", topicSplit);
           split.setAttribute("class", "btn btn-primary btnTopic");           
           split.innerHTML = "Split";
           topicButtonsDiv.appendChild(split);
           //split.setAttribute("disabled", true);

  
        
            var edit = document.createElement("button");
            edit.setAttribute("id", topicEdit);
            edit.setAttribute("class", "btn btn-primary btnTopic");
            edit.innerHTML = "Rename";
            topicButtonsDiv.appendChild(edit);

            
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
                    
                    visualize_sankey(matrix_sankey[lambda_lambda_topic_similarity.current], vis_state.min_value_filtering, vis_state.max_value_filtering)
                    $('#topic_name_selected_2').html(name_topics_sankey[document.getElementById("idTopic2").innerText])                    
                    //visualizar el nuevo nombre
                    
                })

            //colocar #apply_merging.  "aqui esta el antiguo codigo para el merge"

            d3.select("#"+topicSplit)
            .on("click",function(){
                
                $('#topic_to_split_name').html(name_topics_circles[topicID + vis_state.topic]);                    
                $('#SplitTopicModal').modal();

                updateRelevantDocumentsTopicSplitting(splitting_topic-1, relevantDocumentsDict, 1);                
                //createBarPlotTopicSplitting("#KeywordsPanel_TopicSplitting", dat3, barFreqsIDTopicSplitting,"bar-totals_TopicSplitting", "TopicSplitting", 1, "xaxis-TopicSplitting", 20); //hay que modificar la altura aqui en funcion del alto de las barras
            });

            $("#apply_topic_splitting").click(function() {
                if(typeof slider_topic_splitting_values[splitting_topic] != "undefined"){
                    if((typeof slider_topic_splitting_values[splitting_topic]['TopicA'] == "undefined") || (typeof slider_topic_splitting_values[splitting_topic]['TopicB'] == "undefined")){

                        $('#error_splitting').modal()

                    }
                    else{
                        console.log('yay. we are going to do topic splitting')
                        //console.log(' Documents en a', slider_topic_splitting_values[splitting_topic]['TopicA'])
                        //console.log(' Documents en b', slider_topic_splitting_values[splitting_topic]['TopicB'])

                        //save_state_data()
                        //splitting_topics_document_based_scenario_1()
                    }                
                }
                else{
                    $('#error_splitting').modal()
                }
            });


    
            var inputDiv_zero = document.createElement("div");
            inputDiv_zero.setAttribute("id", "BarPlotDiv_zero"); //inputDiv_zero.setAttribute("class", "border_box my-1");
            document.getElementById(BarPlotPanelDivId).appendChild(inputDiv_zero)  //document.getElementById(visID).appendChild(inputDiv); //creo que esto debiera estar unido al svg mejor
            
            var divider_topic_name_left = document.createElement("hr");
            divider_topic_name_left.setAttribute("class", "rounded");
            document.getElementById("BarPlotDiv_zero").appendChild(divider_topic_name_left) 

            var inputDiv = document.createElement("div");
            inputDiv.setAttribute("id", "BarPlotDiv");
            document.getElementById("BarPlotDiv_zero").appendChild(inputDiv)  //document.getElementById(visID).appendChild(inputDiv); //creo que esto debiera estar unido al svg mejor

            //Div for relevance slider. 
            var lambdaDiv = document.createElement("div");
            lambdaDiv.setAttribute("id", "relevanceSliderDiv");
            lambdaDiv.setAttribute("class", "RowDiv ");
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
    
            var sliderDivLambdaTopicSimilarity = document.createElement("div");
            sliderDivLambdaTopicSimilarity.setAttribute("id", sliderDivIDLambdaTopicSimilarity);
            sliderDivLambdaTopicSimilarity.setAttribute("class", "RowDiv");
            document.getElementById("TopicSimilarityMetricPanel").appendChild(sliderDivLambdaTopicSimilarity)  //document.getElementById(visID).appendChild(inputDiv); //creo que esto debiera estar unido al svg mejor


            if(type_vis==2){


                
                /* This section is to allow users to filtering paths on sankey diagram*/

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
                var range_slider = noUiSlider.create(slider, {
                    start: [(max_similarity_score)*0.65, max_similarity_score],
                    //start: [-0.5, 0.17],
                    //start: [(min_similarity_score+max_similarity_score)/2.0, max_similarity_score],
                    connect: true,
                    range: {
                        'min': min_similarity_score,
                        'max': max_similarity_score
                    }
                });
                //disable right handle of the slider                    
                //read values from slider slider-value-lower
                
                var lambdaLabelTopicSimilarity = document.createElement("label");
                lambdaLabelTopicSimilarity.setAttribute("id", "LabelFilteringTopicSimilarity");
                lambdaLabelTopicSimilarity.setAttribute("class", "ColumnDiv");
                lambdaLabelTopicSimilarity.setAttribute("for", "lambdaInputTopicSimilarityFiltering");
                lambdaLabelTopicSimilarity.innerHTML = "Filtering = [<span id='slider-value-lower'></span> - <span id='slider-value-upper'>]";
                sliderDivFiltering.appendChild(lambdaLabelTopicSimilarity);

                var origins = slider.getElementsByClassName('noUi-origin');
                

                slider.noUiSlider.on('update', function (values, handle) {
                    
                    //por ahora, values[1] siempre sera el maximo score, vamos a desabilitar ese handle a mano
                    
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
                        .range([0+8, bounds_scaleContainer_filtering.width-12]);

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
                    .range([7.5, bounds_scaleContainer_omegatopicsimilarity.width-12])  //Now it is responsive
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
                    topic_on(document.getElementById(topicID+vis_state.topic))
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
            ////////////console.log("ojo, estos son los parametros que recibe reorder_bars_helper", increase, topic_id_in_model, barFreqsID_actual, bar_totals_actual, terms_actual, overlay, xaxis_class)
            
            var dat2 = lamData.filter(function(d) {
                
                return d.Category == "Topic" + topic_id_in_model;
            });
            
            
            // define relevance:
            for (var i = 0; i < dat2.length; i++) {
                dat2[i].relevance = vis_state.lambda * dat2[i].logprob +
                    (1 - vis_state.lambda) * dat2[i].loglift;
            
                if(isNaN(dat2[i].relevance)){
                    dat2[i].relevance  = -Infinity;
                }
            }
            

            // sort by relevance:
            dat2.sort(fancysort("relevance"));
            
            
            var dat3 = dat2.slice(0, R);
            
            var y = d3.scaleBand()
                    .domain(dat3.map(function(d) {
                        return d.Term;
                    }))
                    .rangeRound([0, barheight])
                    .padding(0.15);
            
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
                    .style("fill", color1_1)
                    .attr("opacity", 0.4);

            var labelsEnter = labels.enter()
                    .append("text")
                    .attr("x", -5)
                    .attr("class", terms_actual)
                    .attr("y", function(d) {
                        return y(d.Term) + 12 + barheight + margin.bottom + 2 * rMax;
                    })
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
                    .style("fill", color2_1)
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

        function show_bars_withouth_transitions(to_select, increase, topic_id_in_model, barFreqsID_actual, bar_totals_actual, terms_actual, overlay, xaxis_class){
            ////////////console.log("ojo, estos son los parametros que recibe reorder_bars_helper", increase, topic_id_in_model, barFreqsID_actual, bar_totals_actual, terms_actual, overlay, xaxis_class)
            
            var dat2 = lamData.filter(function(d) {
                
                return d.Category == "Topic" + topic_id_in_model;
            });
            
            
            // define relevance:
            for (var i = 0; i < dat2.length; i++) {
                dat2[i].relevance = vis_state.lambda * dat2[i].logprob +
                    (1 - vis_state.lambda) * dat2[i].loglift;
            
                if(isNaN(dat2[i].relevance)){
                    dat2[i].relevance  = -Infinity;
                }
            }
            

            // sort by relevance:
            dat2.sort(fancysort("relevance"));
            
            
            var dat3 = dat2.slice(0, R);
            list_terms_for_topic_splitting = dat3;

            var y = d3.scaleBand()
                    .domain(dat3.map(function(d) {
                        return d.Term;
                    }))
                    .rangeRound([0, barheight])
                    .padding(0.15);
            
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
                    .style("fill", color1_1)
                    .attr("opacity", 0.4);

            var labelsEnter = labels.enter()
                    .append("text")
                    .attr("x", -5)
                    .attr("class", terms_actual)
                    .attr("y", function(d) {
                        return y(d.Term) + 12 + barheight + margin.bottom + 2 * rMax;
                    })
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
                    .style("fill", color2_1)
                    .attr("opacity", 0.8);
            var old_duration = duration;
            duration = 0;
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

                duration = old_duration;
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
                                
                updateRelevantDocuments(topic_id_in_model, relevantDocumentsDict_2,2);
                
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
                    d3.select("#"+last_clicked_model_2).style("fill",color2_1)
                }

                
                last_clicked_model_2 = "node_"+box.node
                d3.select("#"+last_clicked_model_2).style("fill",color2_2) //color2_2
                //d3.select("#"+last_clicked_model_2).style("opacity", 1.0)
                document.getElementById("renameTopicId2").value = name_topics_sankey[topicID + box.node] 
                $('#idTopic2').html(topicID + box.node); 
                $('#topic_name_selected_2').html(name_topics_sankey[topicID + box.node] ); 

                
                

            }
            else{ // el topico seleccionado eprtenece al modelo del corpus 1

        
                to_select =  "#BarPlotPanelDiv"
                var topic_id_in_model = box.node

                
                updateRelevantDocuments(topic_id_in_model, relevantDocumentsDict, 1);
                
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
                    d3.select("#"+last_clicked_model_1).style("fill",color1_1)
                }

                last_clicked_model_1 = "node_"+box.node
                d3.select("#"+last_clicked_model_1).style("fill",color1_2)
                //cual es el d al que le estoy haciendo click??


                
                
                document.getElementById("renameTopicId").value = name_topics_sankey[topicID + box.node] 
                $('#idTopic').html(topicID + box.node);
                $('#topic_name_selected_1').html(name_topics_sankey[topicID + box.node]); 
                
            }

            vis_state.topic = box.node
            

            Freq = Math.round(Freq * 10) / 10  


            var text = d3.select(to_select + " ."+bubble_tool);
            text.remove();

            
            
            
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

                if(isNaN(dat2[i].relevance)){
                    dat2[i].relevance  = -Infinity;
                }
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
                .style("fill", color1_1)
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
                .style("fill", color2_1)
                .attr("opacity", 0.8);

            // adapted from http://bl.ocks.org/mbostock/1166403

            var xAxis = d3.axisTop(x).tickSize(-barheight).ticks(6);

            // redraw x-axis
            d3.selectAll(to_select + " ."+xaxis_class)
            //.attr("class", "xaxis")
                .call(xAxis);

            
            if(!(d3.select("#" + barFreqsID_actual).empty())){
            
                var bounds_barplot = d3.select("#" + barFreqsID_actual).node().getBoundingClientRect();
                d3.select("#" + barFreqsID_actual)
                .append("text")
                .attr("x", (bounds_barplot.width - termwidth)/2) 
                .attr("y", -20)
                .attr("class", bubble_tool) //  set class so we can remove it when highlight_off is called
                .style("text-anchor", "middle")
                .style("font-size", "16px")
                .text("Top Most Relevant Terms for Topic  (" + Freq + "% of tokens)"); //.text("Top-" + number_terms_sankey + " Most Relevant Terms for Topic " + topic_id_in_model+ " (" + Freq + "% of tokens)");
                
            }

                    


        }
        function topic_on(circle) {
            
            to_select = "#BarPlotPanelDiv"
            if (circle == null) return null;
                        
            // grab data bound to this element
            var d = circle.__data__;
            mdswidth+margin.left+termwidth+(barwidth/2)
            // update name in visualization
            $('#topic_name_selected_1').html(name_topics_circles[topicID + d.topics]); 


            var Freq = Math.round(d.Freq * 10) / 10,
                topics = d.topics;
            // change opacity and fill of the selected circle
            circle.style.opacity = highlight_opacity;
            circle.style.fill = color1_2;

            // Remove 'old' bar chart title
            var text = d3.select(to_select + " .bubble-tool");
            text.remove();

            // MERGING topic 1 data
            merging_topic_1 = d.topics //la id
            $('#merging_topic_1').html(merging_topic_1)
            $('#merging_topic_1_name').html(name_topics_circles[topicID + d.topics])
            
            var bounds_barplot = d3.select("#" + barFreqsID).node().getBoundingClientRect();
            


            d3.select("#" + barFreqsID)
                .append("text")
                .attr("x",(bounds_barplot.width - termwidth)/2) 
                .attr("y", -20)
                .attr("class", "bubble-tool") //  set class so we can remove it when highlight_off is called
                .style("text-anchor", "middle")
                .style("font-size", "16px")
                .text("Top Most Relevant Terms for Topic  (" + Freq + "% of tokens)");
                
                        
            // grab the bar-chart data for this topic only:            
            var dat2 = lamData.filter(function(d) {
                return d.Category == "Topic" + topics;
            });
            
                        
            // define relevance:
            var new_relevance;
            for (var i = 0; i < dat2.length; i++) {

                new_relevance = lambda.current * dat2[i].logprob +(1 - lambda.current) * dat2[i].loglift;
                if(isNaN(new_relevance)){
                    new_relevance = -Infinity;
                }

                dat2[i].relevance = new_relevance;
            }
            
            
            // sort by relevance:
            dat2.sort(fancysort("relevance"));        
            var dat3 = dat2.slice(0, R);

            //Show most relevant documents                    
            updateRelevantDocuments(d.topics-1, relevantDocumentsDict, 1);
            
            var y = d3.scaleBand()
                    .domain(dat3.map(function(d) {
                        return d.Term;
                    }))
                    .rangeRound([0, barheight])
                    .padding(0.15);                    
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
                .style("fill", color1_1)
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
                .style("fill", color2_1)
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
            circle.style.fill = color1_1;

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
                .style("fill", color1_1)
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
        



        function to_percentage(number){
            var result =  (number*100).toFixed(1);
            if(result>100){
                console.log('que weaaa este es el number', number, 'y este es el result', result);
            }
            return (number*100).toFixed(1) + '%';

        }


        function s2ab(s) { 
            var buf = new ArrayBuffer(s.length); //convert s to arrayBuffer
            var view = new Uint8Array(buf);  //create uint8array as viewer
            for (var i=0; i<s.length; i++) view[i] = s.charCodeAt(i) & 0xFF; //convert to octet
            return buf;    
        }

        
        //fab menu to download data
        $(function() {
            $('.btn-group-fab').on('click', '.btn', function() {
              $('.btn-group-fab').toggleClass('active');
            });
            $('has-tooltip').tooltip();
          });
        //https://docs.sheetjs.com/        
        function s2ab(s) {
            var buf = new ArrayBuffer(s.length);
            var view = new Uint8Array(buf);
            for (var i=0; i<s.length; i++) view[i] = s.charCodeAt(i) & 0xFF;
            return buf;
          }
          
        d3.select("#export_to_csv") 
        .on("click", function() {
            //create worksheet for single corpus data
            if(type_vis == 1){
                
                var wb = XLSX.utils.book_new();

                wb.Props = {
                        Title: "Topic Modeling - Single Corpus"                        
                    };

                //create a worksheet - most relevant documents topic model 1                        
                wb.SheetNames.push("Documents");
                var documents_1 = XLSX.utils.json_to_sheet(relevantDocumentsDict);            
                wb.Sheets["Documents"] = documents_1;

                //export the top keywords for each topic, add lambda, loflift values, etc.
                wb.SheetNames.push("Top keywords");
                var documents_1 = XLSX.utils.json_to_sheet(dat3);            
                wb.Sheets["Top keywords"] = documents_1;

                var topic_similarity_matrix_excel;    
                //console.log("se ejecuta esto y xk no el ajax")
                $.ajax({
                    url: "/get_topic_similarity_matrix_single_corpus",
                    dataType: 'json',
                    async: false,
                    method: "GET",
                    data: {"value":String(lambda_lambda_topic_similarity.current)},
                    success: function(matrix) {        
                        topic_similarity_matrix_excel = matrix;  
                    }
                });        
                
                //add topic similarity matrix
                wb.SheetNames.push("Topic similarities");
                var documents_1 = XLSX.utils.aoa_to_sheet(topic_similarity_matrix_excel);            
                wb.Sheets["Topic similarities"] = documents_1;
                            
            }
            //create worksheet for multicorpus
            if(type_vis === 2){
                //create workbook
                var wb = XLSX.utils.book_new();
                ////console.log("que hay en merge lassmbData", lamData, dat3,jsonData_2)   
                wb.Props = {
                        Title: "Topic Modeling - Multi Corpora"
                    };

                //create a worksheet - most relevant documents topic model 1                        
                wb.SheetNames.push("Documents 1");
                var documents_1 = XLSX.utils.json_to_sheet(relevantDocumentsDict);
                wb.Sheets["Documents 1"] = documents_1;
                
                //create a worksheet - most relevant documents topic model 2                      
                wb.SheetNames.push("Documents 2");
                var documents_2 = XLSX.utils.json_to_sheet(relevantDocumentsDict_2);
                wb.Sheets["Documents 2"] = documents_2;

                //export the top keywords for each topic, add lambda, loflift values, etc.
                wb.SheetNames.push("Top keywords");
                var documents_1 = XLSX.utils.json_to_sheet(lamData);            
                wb.Sheets["Top keywords"] = documents_1;

                
                /*var topic_similarity_matrix_excel;    
                //console.log("se ejecuta esto y xk no el ajax")
                $.ajax({
                    url: "/get_topic_similarity_matrix_single_corpus",
                    dataType: 'json',
                    async: false,
                    method: "GET",
                    data: {"value":String(lambda_lambda_topic_similarity.current)},
                    success: function(matrix) {        
                        topic_similarity_matrix_excel = matrix;  
                    }
                });        
                
                //add topic similarity matrix
                wb.SheetNames.push("Topic similarities");
                var documents_1 = XLSX.utils.aoa_to_sheet(topic_similarity_matrix_excel);            
                wb.Sheets["Topic similarities"] = documents_1;*/


            }
            
            //exporting to download
            var wbout = XLSX.write(wb, {bookType:'xlsx',  type: 'binary'});
            saveAs(new Blob([s2ab(wbout)],{type:"application/octet-stream"}), 'Topic Modeling data.xlsx');
            
                            

            

        });


        function get_name_text_column_on_relevant_documents(relevantDocumentsDict){
            //get the name of the columns
            var name_columns = Object.keys(relevantDocumentsDict[0])
            var column_text_name = ''
            name_columns.forEach(
                element => {
                    if(typeof relevantDocumentsDict[0][element] == "string"){                                            
                        column_text_name = element
                        
                    }
                })
            return column_text_name                                      
        }


        //https://www.jqueryscript.net/form/shift-select-multiple-checkboxes.html

        function generateColumns(param) {
            return  [{
                field: 'id',
                title: 'ID',
                visible: false,
                align: 'center',
                valign: 'middle'
            }];            
        }

        /*
        function see_most_relevant_keywords(topic_id){
            var dat2 = lamData.filter(function(e) {
                return e.Category == "Topic"+topic_id;
            });
            

            // define relevance:
            for (var i = 0; i < dat2.length; i++) {
                dat2[i].relevance = lambda.current * dat2[i].logprob +
                    (1 - lambda.current) * dat2[i].loglift;

                if(isNaN(dat2[i].relevance)){
                    dat2[i].relevance  = -Infinity;
                }
            }

            // sort by relevance:
            dat2.sort(fancysort("relevance"));
            console.log('estos son los terminos ordenadoooos para topic id' , topic_id, dat2.slice(0,30));
                        
        }
        */

        function arrayRemove(arr, value) { 
            return arr.filter(function(ele){ 
                return ele != value; 
            });
        }

            //slider topic splitting
        $('#tableRelevantDocumentsClass_TopicSplitting').on('post-body.bs.table', function (e) {
            /*This add a slider too all the table*/
            //$(".checkradios").checkradios();
           //console.log('se ejecuto la funcion post body bs');

            $('.radio_button_topic_splitting').click(function () {
                if ($(this).is(':checked')) {
                        //update the values in the dictionary                
                        if(slider_topic_splitting_values[splitting_topic] == undefined ){
                            slider_topic_splitting_values[splitting_topic] = {};
                            
                            
                        }
                        //The element is removed from other places


                        //console.log('que hay en esta fila', this);
                        var current_id_radio_button = this.id;
                        var current_topic = current_id_radio_button.split("_")[0];
                        var current_index = current_id_radio_button.split("_")[1];
                        var current_class = current_id_radio_button.split("_")[2];

                        var current_row = current_relevant_documents_topic_splitting[current_index];


                        if(typeof slider_topic_splitting_values[splitting_topic]['TopicA'] != "undefined"){
                            slider_topic_splitting_values[splitting_topic]['TopicA'] = arrayRemove(slider_topic_splitting_values[splitting_topic]['TopicA'], current_row);
                        }
                        if(typeof slider_topic_splitting_values[splitting_topic]['TopicB'] != "undefined"){
                            slider_topic_splitting_values[splitting_topic]['TopicB'] = arrayRemove(slider_topic_splitting_values[splitting_topic]['TopicB'], current_row)
                        }


                        if(slider_topic_splitting_values[splitting_topic][current_class] == undefined){
                            slider_topic_splitting_values[splitting_topic][current_class] = []
                        }

                        slider_topic_splitting_values[splitting_topic][current_class].push(current_row);
                        //console.log('asi va estoo', slider_topic_splitting_values);




                    }

            });
            
            if(slider_topic_splitting_values[splitting_topic] !== undefined ){
                var array_current_relevant_documents_topic_splitting = Object.values(current_relevant_documents_topic_splitting);
                for (const [key, value] of Object.entries(slider_topic_splitting_values[splitting_topic] )) {
                    for (var i = 0; i < slider_topic_splitting_values[splitting_topic][key].length; i++) {
                        var index = array_current_relevant_documents_topic_splitting.findIndex( s => s == slider_topic_splitting_values[splitting_topic][key][i] );
                        if(document.getElementById(String(splitting_topic+'_'+index+'_'+key))!= undefined){
                            document.getElementById(String(splitting_topic+'_'+index+'_'+key)).checked =true;

    
                        } 

                    }
                }               
            console.log('asi va estoo aqui', slider_topic_splitting_values);

            }            
        });
        //Show how the relevant keywords are being used in the most relevant documents. 
        //Maybe, also, we should increase the bold of the keyword in the left panel too. 



        function updateRelevantDocumentsTopicSplitting(topic_id, relevantDocumentsDict, model){
            
            var column_text_name = get_name_text_column_on_relevant_documents(relevantDocumentsDict)
            //sorted regarding to its contribution
            relevantDocumentsDict.sort(function(row_1, row_2){
                return row_2[String(topic_id)]-row_1[String(topic_id)];
            });

            current_relevant_documents_topic_splitting = relevantDocumentsDict; // the documents are sorted according to the contribution to the specific topic 

            if(model == 1){
                $('#tableRelevantDocumentsClass_TopicSplitting').bootstrapTable("destroy");
                $('#tableRelevantDocumentsClass_TopicSplitting').bootstrapTable({
                    toggle:true,
                    //height:420,
                    pagination: true,
                    //showRefresh: true,
                    search: true,
                    sorting: true,
                    uniqueId: true,
                    //pageList: [10, 25, 50, 100],
                    pageList: [10],
                    checkboxHeader: false,           
                    multipleSelectRow: true,         
                    //showRefresh: true, Hacer que esto funcione! ver :  https://examples.bootstrap-table.com/#view-source
                    //showExport:true,
                    //showColumns: true,
                    columns:[
                        {
                            field: String(topic_id),
                            formatter:to_percentage,
                            title: '%',
                            sortable:'true'
                        },{
                            field: column_text_name,
                            escape:"true",
                            title: 'Document',
                            sortable:'true'
                        },
                        {
                            field: 'Term',
                            title: 'New subtopic A',
                            align: 'center',
                            valign: 'middle',
                            clickToSelect: false,
                            formatter : function(value,row,index) {       
                                //console.log('este es un value', value, row, index);             
                             return '<input type="radio" name="radio_'+splitting_topic+'_'+index+'" id="'+splitting_topic+'_'+index+'_TopicA" class="radio_button_topic_splitting" />';
                             }                      
                          },
                          {
                             field: 'Term',
                             title: 'New subtopic B',
                             align: 'center',
                             valign: 'middle',
                             clickToSelect: false,
                             formatter : function(value,row,index) {                                              
                              return '<input type="radio"  name="radio_'+splitting_topic+'_'+index+'" id="'+splitting_topic+'_'+index+'_TopicB" class="radio_button_topic_splitting" />';
     
                              }                      
                           },
                           {
                             field: 'Term',
                             title: 'Neither',
                             align: 'center',
                             valign: 'middle',
                             clickToSelect: false,
                             formatter : function(value,row,index) {                            
                         
                              return '<input type="radio" name="radio_'+splitting_topic+'_'+index+'"  id="'+splitting_topic+'_'+index+'_TopicNone" class="radio_button_topic_splitting" checked/>'; 
                              }                      
                           }                               
                      
                        
                    ],
                    data: relevantDocumentsDict // We dont need to show to the user a huge number of documents
                });
            }

            

            $(".search-input").attr("placeholder", "Search on documents").val("").focus().blur();
           
        }

        


        function updateRelevantDocuments(topic_id, relevantDocumentsDict, model){
            
            var column_text_name = get_name_text_column_on_relevant_documents(relevantDocumentsDict)
            //sorted regarding to its contribution
            relevantDocumentsDict.sort(function(row_1, row_2){
                return row_2[String(topic_id)]-row_1[String(topic_id)];
            });

            
            if(model == 1){                        
                $('#tableRelevantDocumentsClass_Model1').bootstrapTable("destroy");
                $('#tableRelevantDocumentsClass_Model1').bootstrapTable({
                    toggle:true,
                    pagination: true,
                    search: true,
                    sorting: true,
                    //showRefresh: true, Hacer que esto funcione! ver :  https://examples.bootstrap-table.com/#view-source
                    //showExport:true,
                    //showColumns: true,
                    columns:[
                        {
                            field: String(topic_id),
                            formatter:to_percentage,
                            title: '%',
                            sortable:'true'
                        },{
                            field: column_text_name,
                            escape:"true",
                            title: 'Document',
                            sortable:'true'
                        }
                    ],
                    data: relevantDocumentsDict
                });

            }
            else{//model == 2
                var column_text_name = get_name_text_column_on_relevant_documents(relevantDocumentsDict)
                $('#tableRelevantDocumentsClass_Model2').bootstrapTable("destroy");
                $('#tableRelevantDocumentsClass_Model2').bootstrapTable({
                    //data: relevantDocumentsDict[topic_id].slice(0,R)
                    toggle:true,
                    pagination: true,
                    search: true,
                    sorting: true,
                    columns:[
                        {
                            field: String(topic_id),
                            formatter:to_percentage,
                            title: '%',
                            sortable:'true'
                        },{
                            field: column_text_name,
                            escape:"true",
                            title: 'Document',
                            sortable:'true'
                        }
                    ],
                    data: relevantDocumentsDict
                });
            
            }
            $(".search-input").attr("placeholder", "Search on documents").val("").focus().blur();

        
        }
        
        function get_RGB_by_relevance(c1_r,c1_g,c1_b, c2_r, c2_g, c2_b, r_min, r_max, r_actual){
            var final_color_r = c1_r+((r_actual-r_min)/(r_max-r_min))*(c2_r-c1_r)
            var final_color_g = c1_g+((r_actual-r_min)/(r_max-r_min))*(c2_g-c1_g)
            var final_color_b = c1_b+((r_actual-r_min)/(r_max-r_min))*(c2_b-c1_b)
            
            return [final_color_r,final_color_g,final_color_b]
        }

        // minor fixes
        //This is the special configuration needed for the user study
        if(type_vis == 1){
            document.getElementById("DocumentsPanel").style.height="80%";
            if(is_human_in_the_loop == false){
                d3.select("#"+topicReverse).remove()
                d3.select("#"+topicSplit).remove()
                d3.select("#"+topicMerge).remove()
            }
        }
        if(type_vis == 2){
            document.getElementById(topicMerge).disabled = true;
            document.getElementById(topicSplit).disabled = true;
            document.getElementById(topicReverse).disabled = true;
        }
        if(old_topic_model_states.length>0){
            document.getElementById(topicReverse).disabled = false;

            }
            else{
                document.getElementById(topicReverse).disabled = true;

        } 
        if(type_vis==2){
            //delete buttons that users wont use in the user study
            d3.select("#"+topicReverse).remove()
            d3.select("#"+topicSplit).remove()
            d3.select("#"+topicSplit+"rightPanel").remove()
            d3.select("#"+topicMerge).remove()
            d3.select("#"+topicMerge+"rightPanel").remove()
            //show full text of topic name on the left panel
            //topic_name_div
            document.getElementById("topic_name_div").style.width="75%";
            document.getElementById("topic_name_div_right_panel").style.width="75%";            
            document.getElementById("topic_buttons_div").style.width="25%";
            document.getElementById("topic_buttons_div_right_panel").style.width="25%";
            //document.getElementsByClassName('bootstrap-table ').style.height='80%';
            


            if( scenario_2_is_baseline_metric == true ) { // it means we are using the metric baseline
                //we need to remove the omega slider, in this case                         
                d3.select("#TopicSimilarityMetricPanel").remove()       
            }                   
        }    
        


    }
    
    if (typeof data_or_file_name === 'string'){
        
        d3.json(data_or_file_name, function(error, data) {visualize(data);});
    }

        
    else{
        
        visualize(data_or_file_name);
        
    }
        


};


