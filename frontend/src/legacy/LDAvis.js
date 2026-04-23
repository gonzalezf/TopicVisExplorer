/* Original code taken from https://github.com/cpsievert/LDAvis */
/* Copyright 2013, AT&T Intellectual Property */
/* MIT Licence */
/* Canonical source: frontend/src/legacy/LDAvis.js (Vite). A mirror may exist at
   src/topicvisexplorer/web/legacy/static/js/LDAvis.js for legacy template loads; keep in sync. */

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
var is_human_in_the_loop;
var scenario_2_is_baseline_metric;
var is_first_time_sankey_diagram = true;
var global_sankey_links_filtered;
var sankey_topics_automatic_match;
var name_topics_sankey = {};
var inverted_links_filtered; 
var is_tutorial = 'undefined';
var testing;
var story_hil_operations = [];
var old_topic;
var first_time_clicking_circle = false;
var topics_with_error = [];
var topics_splitted = [];

function randomIntFromInterval(min, max) { // min and max included 
    return Math.floor(Math.random() * (max - min + 1) + min);
}

function randomNumber(min, max) {
    return Math.random() * (max - min) + min;
}

function isTutorial(){
    //var curren_url = window.location.href;
    var queryString  = window.location.search;
    var urlParams = new URLSearchParams(queryString);
    var scenario = urlParams.get('scenario')

    if(scenario == null  || scenario == 'single_demo' || scenario == 'multi_demo_baseline' || scenario == 'multi_demo'){
        is_tutorial = true;
    }
    else{
        is_tutorial = false;

    }

}
isTutorial()


// === Modernization: Hotjar / IRB clickstream removed ===
// The open-source library does not ship third-party analytics. Session
// telemetry was removed; use the Export topics button for a local JSON
// snapshot of the current model view.



//this function allow to access some values on the matrix_sankey
function get_new_omega(old_omega){
    if(type_vis==2 && scenario_2_is_baseline_metric == true){
        return old_omega;
    }
    var values_omega_temp = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60,0.70,  0.80, 0.90];
    var new_omega = (1.0-old_omega).toFixed(2);
    if(old_omega == 1.00 || old_omega == 0.00){
        new_omega = Number(new_omega).toFixed(1);
    }
    else if ( values_omega_temp.includes(Number(new_omega)) ){
        new_omega = Number(new_omega).toFixed(1);

    }
    else{
        new_omega = Number(new_omega).toFixed(2);

    }
    return new_omega;
}



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
            lambda_b: 0.6,
            min_value_filtering:-1.0,
            max_value_filtering: 1.0,
            lambda_lambda_topic_similarity:0.2, //que tanta info tiene vector top keywords y que tanta info tiene vector top relevant documents
            lambda_topic_similarity:-1.0, //este filtra las lineas (el ancho que de similitud). If this value is very low, it is going to show all the paths. 
            topic: 1,
            term: ""
        };


    //for the user study. The omega value will be random

    // Set up a few 'global' variables to hold the data:
    var K, // number of topics
        mdsData, // (x,y) locations and topic proportions
        //mdsData3, // topic proportions for all terms in the viz
        lamData, // all terms that are among the top-R most relevant for all topics, lambda values
        lambda = {
            old: 0.6,
            current: 0.6
        },
        /** Corpus B (right panel) relevance; independent of lambda (left) for /multicorpora. */
        lambda_b = {
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
        color1_2 = "#5C059E", //morado
        

        color2_1 = "#60F5B7", //verde claro
        color2_2 = "#0BA37C", //verde oscuro
                
        color_topic_1_1 = '#93bafc',// celeste
        color_topic_1_2 = '#0044B8',
        
        color_topic_2_1 = '#fa8276',// naranjo
        color_topic_2_2 = '#BD1100';


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

    /** createBarPlot overwrites the shared `barheight` for each chart; /multicorpora has two. If we keep the last
     *  chart's `barheight` for both, the y-scale is wrong for the other panel and bars are clipped. */
    var barheightByPlotId = { barplot_1: 530, barplot_2: 530 };
    function tveBarheightFor(barPlotId) {
        if (barPlotId && barheightByPlotId[barPlotId] != null) {
            return barheightByPlotId[barPlotId];
        }
        return barheight;
    }

    /**
     * Left uses #BarPlotDiv_zero (wraps the λ slider); right uses #BarPlotDiv_b_zero (empty until the chart). The
     * right slot often stretches in the column and createBarPlot sees a much larger rch, so the left chart SVG
     * ends up much shorter. Match both to max(left, right) so band scales and padding match.
     */
    function tveEqualizeMulticorpusBarChartHeights() {
        if (type_vis !== 2) {
            return;
        }
        var a = document.querySelector("#BarPlotDiv_zero > svg");
        var b = document.querySelector("#BarPlotDiv_b_zero > svg");
        if (!a || !b) {
            return;
        }
        var ha = a.getBoundingClientRect().height;
        var hb = b.getBoundingClientRect().height;
        if (ha < 2 || !isFinite(ha)) {
            ha = parseFloat(a.getAttribute("height")) || 0;
        }
        if (hb < 2 || !isFinite(hb)) {
            hb = parseFloat(b.getAttribute("height")) || 0;
        }
        var hT = Math.max(ha, hb, 180);
        a.setAttribute("height", hT);
        b.setAttribute("height", hT);
        var nbh = Math.max(8, hT - 0.5 * termwidth);
        barheightByPlotId["barplot_1"] = nbh;
        barheightByPlotId["barplot_2"] = nbh;
        barheight = nbh;
    }
        
    // controls how big the maximum circle can be
    // doesn't depend on data, only on mds width and height:
    var rMax = 60;

    // proportion of area of MDS plot to which the sum of default topic circle areas is set
    var circle_prop = 0.20;
    

    // opacity of topic circles:
    var base_opacity = 0.3,
    highlight_opacity = 0.5;

    // lambda selection names are specific to *this* vis
    
    var lambda_select = to_select + "-lambda";

    // get rid of the # in the to_select (useful) for setting ID values
    var visID = to_select.replace("#", "");
    var topicID = visID + "-topic";
    var lambdaID = visID + "-lambda";
    var lambdaIDRightPanel =  lambdaID+"RightPanel"; 



    var termID = "barplotterm-";

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
    /** Type 2: min(corpusA R, corpusB R, 20) so left/right show the same number of default terms. */
    var sankeyTermActiveCap = 20

    /**
     * Opt-in bar-count debugging (left vs right keyword list length).
     * In the browser console: window.TVE_DEBUG_BARS = true
     * or: localStorage.setItem('TVE_DEBUG_BARS','1') then reload.
     * Filter console by [TVE bars]
     */
    var tveBarsDebugWelcome = false;
    function tveLogBars(phase, info) {
        try {
            var w = (typeof window !== "undefined") ? window : null;
            var on = w && w.TVE_DEBUG_BARS === true;
            if (!on && typeof localStorage !== "undefined") {
                on = localStorage.getItem("TVE_DEBUG_BARS") === "1";
            }
            if (on && typeof console !== "undefined" && console.log) {
                if (!tveBarsDebugWelcome) {
                    tveBarsDebugWelcome = true;
                    console.log(
                        "[TVE bars] debug on (reload after localStorage, or set window.TVE_DEBUG_BARS). " +
                        "Logs are browser-only (not the terminal). Click topics or move λ to emit lines."
                    );
                }
                if (info !== undefined) {
                    console.log("[TVE bars]", phase, info);
                } else {
                    console.log("[TVE bars]", phase);
                }
            }
        } catch (e) { /* ignore */ }
    }

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

    var isSettingInitial = true

    var number_top_keywords_name = 3

    
    var real_last_clicked_sankey_model_1
    var real_last_clicked_sankey_model_2

    var BarPlotPanelDivId = 'BarPlotPanelDiv'


    

    var sliderDivIDLambdaTopicSimilarity = "sliderDivLambdaTopicSimilarity"
    //to_select = BarPlotPanelDivId

    /** d3.select("#id") with empty parent throws; resolve real element first. */
    function tveD3SelectById(anchor, context) {
        var s = (anchor == null) ? "" : String(anchor);
        s = s.replace(/^#+/, "").trim();
        if (!s) {
            throw new Error("TopicVisExplorer: empty id " + (context ? "(" + context + ")" : "in tveD3SelectById"));
        }
        var el = document.getElementById(s);
        if (!el) {
            throw new Error("TopicVisExplorer: missing DOM #" + s + (context ? " in " + context : ""));
        }
        return d3.select(el);
    }
    
    //Get relevant documents from ajax
    if(type_vis==1){

    }
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

    // === Modernization: Phase 4d ===
    // POST /Add_Remove_Word with the currently-selected topic and the
    // clicked word. On success, rebuild `lamData` from the returned
    // `tinfo` (tinfo carries every (Term, Category, logprob, loglift,
    // ...) combination across all topics, so we can replace the array
    // wholesale and let the existing `topic_on()` machinery redraw).
    //
    // We deliberately do NOT touch mdsData here: add/remove word is a
    // display-only edit per add_remove_word.py's docstring -- it leaves
    // doc_topic_dists unchanged, which means the (x, y) topic
    // coordinates in the central panel are stable. Keeping the central
    // panel pinned matches the paper's intended UX.
    //
    // Bar-chart +/− controls were removed (no D3 text nodes); this
    // function is retained for a possible future control surface or
    // programmatic use. E2E for the old UI is in word_ops.spec.ts (skipped).
    // Forward-declared late-bound bag for closure-private helpers
    // (``topic_on``, ``updateRelevantDocuments``). Populated near the
    // end of ``visualize(data)`` once those have been defined. See the
    // Phase 4d/4e wiring notes inside ``visualize``.
    var _tveInternals = {};

    function _tveDebug(phase, message, extra) {
        if (typeof window !== "undefined" && window.TVE_DEBUG) {
            if (extra !== undefined) {
                console.info("[TVE " + phase + "]", message, extra);
            } else {
                console.info("[TVE " + phase + "]", message);
            }
        }
    }

    function _tveShowServerError(xhr, op) {
        var msg = op + " failed.";
        try {
            var body = JSON.parse(xhr.responseText);
            if (body && body.message) {
                msg += "\n\n" + body.message;
            } else if (body && body.detail) {
                msg += "\n\n" + (typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail));
            } else {
                msg += "\n\n(HTTP " + xhr.status + ")";
            }
        } catch (e) {
            msg += "\n\n(HTTP " + xhr.status + ")";
        }
        console.error("[TopicVisExplorer]", op, "HTTP", xhr.status);
        alert(msg);
    }

    function _tveAddRemoveWord(word, action){
        if (typeof vis_state === "undefined" || !vis_state || !vis_state.topic || vis_state.topic <= 0){
            // Defensive: only relevant when a topic is selected; bar chart
            // is empty otherwise.
            console.warn("[TopicVisExplorer] add/remove word skipped: no topic selected");
            return;
        }
        $.ajax({
            type: 'POST',
            url: '/Add_Remove_Word',
            async: true,
            data: JSON.stringify({ topic_id: vis_state.topic, word: word, action: action }),
            contentType: 'application/json',
            success: function(resp){
                if (!resp || !resp.PreparedDataObtained_fromPython){
                    console.error("[TopicVisExplorer] /Add_Remove_Word returned no PreparedData");
                    return;
                }
                var newTinfo = resp.PreparedDataObtained_fromPython.tinfo;
                if (!newTinfo || !newTinfo.Term){
                    console.error("[TopicVisExplorer] /Add_Remove_Word: malformed tinfo");
                    return;
                }
                // Rebuild lamData from the new tinfo wholesale. Same
                // recipe used by the original `visualize(data)` body
                // around line ~460.
                lamData = [];
                for (var i = 0; i < newTinfo.Term.length; i++){
                    var obj = {};
                    for (var key in newTinfo){
                        obj[key] = newTinfo[key][i];
                    }
                    lamData.push(obj);
                }
                // Re-trigger the existing topic-selection machinery so
                // bars get redrawn with the new term mass.
                var topicEl = document.getElementById(topicID + vis_state.topic);
                if (topicEl && typeof _tveInternals.topic_on === "function"){
                    _tveInternals.topic_on(topicEl);
                }
            },
            error: function(xhr, textStatus, errorThrown){
                console.error("[TopicVisExplorer] /Add_Remove_Word failed", textStatus || errorThrown);
            }
        });
    }

    // === Modernization: Phase 4e ===
    // Build the bootstrap-table column descriptor for the single-corpus
    // documents panel and inject a third "exclude" column. The column
    // is rendered as a small button per row whose ``data-doc-id``
    // attribute carries the source document index. A delegated click
    // handler (registered once at init time) calls
    // ``/Exclude_Document``, refreshes ``relevantDocumentsDict`` from
    // the server response, and re-renders the table.
    //
    // Visual-baseline impact: zero. The exclude column only appears
    // *after* the user selects a topic, which the visual baselines do
    // not exercise.
    // Inlined percentage formatter so this helper does not need to
    // close over ``to_percentage`` (which lives inside ``visualize``).
    function _tvePercentFormatter(number){
        return (number * 100).toFixed(1) + '%';
    }

    function _tveHtmlEscape(s) {
        if (s == null) {
            return '';
        }
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }
    function _tveDocumentTextCellFormatter(value) {
        return '<div class="tve-doc-cell">' + _tveHtmlEscape(value) + '</div>';
    }

    function _tveDocumentColumnsModel1(topic_id, column_text_name){
        var cols = [
            {
                field: String(topic_id),
                formatter: _tvePercentFormatter,
                title: '%',
                sortable: 'true'
            },
            {
                field: column_text_name,
                escape: false,
                title: 'Document',
                sortable: 'true',
                formatter: _tveDocumentTextCellFormatter
            },
            {
                field: 'doc_id',
                title: '',
                sortable: false,
                searchable: false,
                width: 30,
                formatter: function(value, row){
                    if (value === undefined || value === null) {
                        // Backwards-compat: legacy fixtures that don't
                        // carry doc_id simply don't render the button.
                        return '';
                    }
                    return '<button type="button" class="btn btn-sm btn-link tve-doc-exclude-ctrl" '
                        + 'data-doc-id="' + value + '" '
                        + 'aria-label="Exclude this document from the selected topic" '
                        + 'title="Exclude this document from the selected topic">'
                        + '\u2715</button>';
                }
            }
        ];
        return cols;
    }

    function _tveExcludeDocument(docId){
        if (typeof vis_state === "undefined" || !vis_state || !vis_state.topic || vis_state.topic <= 0){
            console.warn("[TopicVisExplorer] exclude doc skipped: no topic selected");
            return;
        }
        if (typeof docId !== "number" || isNaN(docId)) {
            console.warn("[TopicVisExplorer] exclude doc skipped: invalid doc_id", docId);
            return;
        }
        $.ajax({
            type: 'POST',
            url: '/Exclude_Document',
            async: true,
            data: JSON.stringify({ topic_id: vis_state.topic, doc_id: docId }),
            contentType: 'application/json',
            success: function(resp){
                if (!resp || !resp.PreparedDataObtained_fromPython){
                    console.error("[TopicVisExplorer] /Exclude_Document returned no PreparedData");
                    return;
                }
                // Drop the excluded row from the in-memory documents
                // dict so the table reflects the new state immediately.
                // Note: ``row.doc_id`` arrives from the server as a
                // JSON number, but bootstrap-table sometimes coerces
                // dataset attributes to strings. Compare loosely so a
                // numeric click target also matches a stringified row.
                if (typeof relevantDocumentsDict !== "undefined" && relevantDocumentsDict){
                    relevantDocumentsDict = relevantDocumentsDict.filter(function(row){
                        return row.doc_id != docId; // eslint-disable-line eqeqeq
                    });
                }
                // Rebuild lamData (term mass shifts when a document
                // is dropped because the topic-term distribution gets
                // re-derived from the surviving doc_topic_dists).
                var newTinfo = resp.PreparedDataObtained_fromPython.tinfo;
                if (newTinfo && newTinfo.Term){
                    lamData = [];
                    for (var i = 0; i < newTinfo.Term.length; i++){
                        var obj = {};
                        for (var key in newTinfo){ obj[key] = newTinfo[key][i]; }
                        lamData.push(obj);
                    }
                }
                // Refresh the documents panel and the keyword bars for
                // the currently-selected topic. Both helpers live in
                // the ``visualize`` closure; we reach them via the
                // late-bound ``_tveInternals`` bag (see ``visualize``).
                if (typeof _tveInternals.updateRelevantDocuments === "function"){
                    _tveInternals.updateRelevantDocuments(vis_state.topic - 1, relevantDocumentsDict, 1);
                }
                var topicEl = document.getElementById(topicID + vis_state.topic);
                if (topicEl && typeof _tveInternals.topic_on === "function"){
                    _tveInternals.topic_on(topicEl);
                }
            },
            error: function(xhr, textStatus, errorThrown){
                console.error("[TopicVisExplorer] /Exclude_Document failed", textStatus || errorThrown);
            }
        });
    }

    function updateTopicNamesCircles(data, id_topic_splitted, old_mdsData, old_frequency){
        // set the number of topics to global variable K:
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

        var length_tinfo =   Object.keys(data['tinfo']['Term']).length;

      
        lamData = [];
        for (var i = 0; i <  length_tinfo ; i++) {
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




        var dat3 = lamData.slice(0, R);

        //assign name to array

        var new_subtopics_id = []
        var freq_splitted_total = 0;
        d3.select("#name_topics")
                    .data(mdsData)
                    .enter()
                    .each(
                    function(d) {
                        var dat2 = lamData.filter(function(e) {
                            return e.Category == "Topic"+d.topics;
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
                        if(d.topics == id_topic_splitted || name_topics_circles[topicID + d.topics] == undefined){// como hay varios topicos undefined, esto tira un calculo equivaco a aveces

                            name_topics_circles[topicID + d.topics] = 'New subtopic '+name_string;
                            new_subtopics_id.push(d.topics)
                            freq_splitted_total  = mdsData.find(element => element.topics == d.topics).Freq;
                            topics_splitted.push( topicID + d.topics);
                            //topicID + d.topics
                        }else{
                            //get antiguas frecuencias
                            var old_element  = old_mdsData.find(element => element.topics == d.topics);
                            mdsData.find(element => element.topics == d.topics).Freq = old_element.Freq;

                            
                        }

                    });    
        freq_splitted_total +=  mdsData.find(element => Number(element.topics) == Number(id_topic_splitted)).Freq;
        for ( var i = 0; i < new_subtopics_id.length; i++){
           
            var current_id =new_subtopics_id[i];

            var current_freq = mdsData.find(element => Number(element.topics) == Number(current_id)).Freq;
            mdsData.find(element => element.topics == current_id).Freq = old_frequency*(current_freq/freq_splitted_total);
        }
    
    }

    
  

    function visualize(data) {
        // set the number of topics to global variable K:
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
                            return e.Category == "Topic"+d.topics;
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
        // Keep UI omega in sync with the value used for MDS (slider was 0.2 vs 0.8 before).
        vis_state.lambda_lambda_topic_similarity = String(lambda_lambda_topic_similarity.current);
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
                lambda_b.old = lambda_b.current;
                lambda_b.current = document.getElementById(lambdaIDRightPanel).value;
                vis_state.lambda_b = +this.value;
                d3.select("#"+lambdaIDRightPanel).property("value", vis_state.lambda_b);
                d3.select("#"+lambdaIDRightPanel + "-value").text(vis_state.lambda_b);
                var increased = lambda_b.old < vis_state.lambda_b;
                if (vis_state.topic > 0) {
                    reorder_bars_new(increased, "right");
                }
                document.getElementById(lambdaIDRightPanel).value = vis_state.lambda_b;
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

                    var expectedTopicCat;
                    if (d.node < 0) {
                        expectedTopicCat = "Default";
                    } else if (d.node >= min_target_node_value) {
                        expectedTopicCat = "Topic" + (d.node - min_target_node_value + 1);
                    } else {
                        expectedTopicCat = "Topic" + (d.node + 1);
                    }
                    var dat2 = lamData.filter(function(e) {
                        return e.Category == expectedTopicCat;
                    });
                    var lrelName = d.node >= min_target_node_value ? vis_state.lambda_b : vis_state.lambda;
                    for (var i = 0; i < dat2.length; i++) {
                        dat2[i].relevance = lrelName * dat2[i].logprob +
                            (1 - lrelName) * dat2[i].loglift;
                        if (isNaN(dat2[i].relevance)) {
                            dat2[i].relevance = -Infinity;
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
            inverted_links_filtered = graph;




            var node_padding = 25
            d3.selectAll('#svgCentralSankeyDiv').remove();
            d3.selectAll('#divider_central_panel_sankey').remove();
            
            var svgCentralSankeyDiv = tveD3SelectById("CentralPanel", "visualize_sankey #svgCentralSankeyDiv").append("div");
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

            sankey_topics_automatic_match = []
            var links_filtered =  graph.links.filter(function(el){
                if((Number(threshold_min) <= Number(el.value.toFixed(2)) )&&(Number(el.value.toFixed(2)) <= Number(threshold_max) )){
         
                    return true;

                }
                return (Number(threshold_min) <= Number(el.value.toFixed(2)) )&&(Number(el.value.toFixed(2)) <= Number(threshold_max))

                }
            );

            //add a link dummy para que siempre dibuje algo
            global_sankey_links_filtered = links_filtered; // i need this variable just for the user study
            if( links_filtered.length == 0){
                
            }



            var margin = {top: 10, right: 10, bottom: 10, left: 10};
            
            var formatNumber = d3.format(",.2f"),    // two decimal places
                format = function(d) { 
                    if(scenario_2_is_baseline_metric == true){
                        return "similarity score: "+formatNumber(d);

                    }else{
                        return "similarity score: "+formatNumber(d);

                    }
                
                },
                color = d3.scaleOrdinal(d3.schemeAccent);
            


            var svg_sankey = tveD3SelectById("svgCentralSankeyDiv", "visualize_sankey #svg_sankey").append("svg");
            svg_sankey
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
                .on("click", function(d){
                    var _ns = nodes_filtered[Number(d.source.node)];
                    var _nt = nodes_filtered[Number(d.target.node)];
                    var _pnL = tvePairedNFromTwoBoxes(_ns, _nt, min_target_node_value);
                    topic_on_sankey(_ns, min_target_node_value, _pnL, true);
                    topic_on_sankey(_nt, min_target_node_value, _pnL, true);


                    

                    isSettingInitial = false;
                    if(Number(d.source.node)>=min_target_node_value){
                        real_last_clicked_sankey_model_2 = nodes_filtered[Number(d.source.node)];

                    }
                    else{
                        real_last_clicked_sankey_model_1 = nodes_filtered[Number(d.source.node)];
                    }
                    if(Number(d.target.node)>=min_target_node_value){
                        real_last_clicked_sankey_model_2 = nodes_filtered[Number(d.target.node)];

                    }
                    else{
                        real_last_clicked_sankey_model_1 = nodes_filtered[Number(d.target.node)];
                    }
                    vis_state.topic = Number(d.target.node);
                    splitting_topic = vis_state.topic;
                }) 
                .sort(function(a, b) { return b.dy - a.dy; }); // el dy de aqui tambien hay que modificarlo

            
    
            link.append("title")
                .text(function(d) {
                    var match = { 
                        'source_node':topicID + d.source.node,
                        'source_name': name_topics_sankey[topicID + d.source.node],
                        'link_value': format(d.value),
                        'target_node': topicID + d.target.node,
                        'target_name': name_topics_sankey[topicID + d.target.node],
                    }

                    var title = name_topics_sankey[topicID + d.source.node] + " → " + 
                    name_topics_sankey[topicID + d.target.node] + "\n" + format(d.value);
                    sankey_topics_automatic_match.push(JSON.stringify(match));

                    return title;});
                    
        
            // add in the nodes

            var node = svg_sankey.append("g").selectAll(".node")
                .data(nodes_filtered)//.data(graph.nodes)
                .enter().append("g")
                .attr("class", "node")
                .attr("transform", function(d) { 
                    return "translate(" + d.x + "," + d.y + ")"; }) // el d.y de aqui tambien hay que modificarlo
                .on("click", function(d){

                    isSettingInitial = false;
                    var mtv0 = min_target_node_value;
                    var other0 = (d.node >= mtv0) ? real_last_clicked_sankey_model_1 : real_last_clicked_sankey_model_2;
                    var _pnn = tvePairedNFromTwoBoxes(d, other0, mtv0);
                    if(d.node>=mtv0){
                        real_last_clicked_sankey_model_2 = d;
                    } else {
                        real_last_clicked_sankey_model_1 = d;
                    }
                    topic_on_sankey(d, mtv0, _pnn, true);
                    topic_on_sankey(other0, mtv0, _pnn, true);
                    vis_state.topic = d.node;
                    splitting_topic = d.node;
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

                        return color_topic_1_1;
                        
                    }
                    else{
                        return color_topic_2_1;
                        
                    }
                     
                })
                .style("stroke", function(d) { 
                    return d3.rgb(d.color).darker(2); })
                .style("opacity", 0.6)
                .append("title")
                    .text(function(d) { 
                        return name_topics_sankey[topicID + d.node] ;}) 
        
        // add in the title for the nodes
            node.append("text")
                .attr("x", -6)
                .attr("y", function(d) { return d.dy / 2; })
                .attr("dy", ".35em")
                .attr("width", function(d) {
                    return 0.45*d3.selectAll('#svg_sankey').node().getBoundingClientRect().width
                    
                })
                .attr("class", "txt")
                .attr("font-weight", "bold")
                .attr("text-anchor", "end")
                .attr("transform", null)
                .text(function(d){
                    if(d.node>=min_target_node_value){ //model 2
                        
                        var Freq = jsonData_2.mdsDat.Freq[d.node-min_target_node_value];    
                        var freq_current_topic = Math.round(Freq * 10) / 10;
                        var labeling_user_study = 'N'+String(d.node-min_target_node_value+1);  
                        
                        

                  
                    }
                    else{
                        var Freq = jsonData.mdsDat.Freq[d.node];                       
                        var freq_current_topic = Math.round(Freq * 10) / 10;
                        var labeling_user_study = 'E'+String(d.node+1);  
  
                    }



                    //return labeling_user_study+' - '+"("+freq_current_topic+"%) "+ name_topics_sankey[topicID + d.node];}
                    return labeling_user_study+' - '+ name_topics_sankey[topicID + d.node];}

                    //return name_topics_sankey[topicID + d.node] ;}                                                
                ) //.text(function(d) { return d.name; })
                .filter(function(d) { return d.x < user_width_sankey / 2; })
                .attr("x", 6 + sankey.nodeWidth())
                .attr("text-anchor", "start");
        

            if(last_clicked_model_2!=-1){
                d3.select("#"+last_clicked_model_2).style("fill",color2_1)
            }
            if(last_clicked_model_1!=-1){
                d3.select("#"+last_clicked_model_1).style("fill",color1_1)
            }

            
            
            if(isSettingInitial){
                real_last_clicked_sankey_model_1 = nodes_filtered[0];
                real_last_clicked_sankey_model_2 = nodes_filtered[min_target_node_value];
                

            }
            var _pair0 = tvePairedNFromTwoBoxes(
                real_last_clicked_sankey_model_1,
                real_last_clicked_sankey_model_2,
                min_target_node_value
            );
            topic_on_sankey(real_last_clicked_sankey_model_1, min_target_node_value, _pair0, true);
            topic_on_sankey(real_last_clicked_sankey_model_2, min_target_node_value, _pair0, true);
            vis_state.topic = real_last_clicked_sankey_model_2.node;
            splitting_topic = vis_state.topic;
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
            current_state_dict.merged_topic_to_delete =  _.cloneDeep(merged_topic_to_delete);
            current_state_dict.name_merged_topic_to_delete = _.cloneDeep(name_merged_topic_to_delete);
            current_state_dict.topics_splitted = _.cloneDeep(topics_splitted);

            
            current_state_dict.lamData = _.cloneDeep(lamData);
            current_state_dict.mdsData = _.cloneDeep(mdsData);
            current_state_dict.new_circle_positions = _.cloneDeep(new_circle_positions);
            current_state_dict.name_topics_circles = _.cloneDeep(name_topics_circles);
            current_state_dict.current_topic_id = _.cloneDeep(vis_state.topic);
            //radio input infromation for topic splitting
            current_state_dict.slider_topic_splitting_values = _.cloneDeep(slider_topic_splitting_values);

            old_topic_model_states.push(current_state_dict);

            if(old_topic_model_states.length>0){
                document.getElementById(topicReverse).disabled = false;

            }
            else{
                document.getElementById(topicReverse).disabled = true;

            }
        }
        
        function splitting_topics_document_based_scenario_1(){
            _tveDebug("split", "starting", {
                topic_id: vis_state.topic,
                splitting_topic: splitting_topic,
                currentK: mdsData && mdsData.length
            });
            $('#loadMe').modal({
                backdrop: 'static',
                keyboard: false
            });

            setTimeout(function(){
                $("#loadMe").modal('hide');
            }, 120000);


            var old_frequency  = mdsData.find(element => element.topics == vis_state.topic).Freq;
            //console.log(' OJOO!!!!', vis_state.topic, splitting_topic, mdsData, old_frequency)
            var rawSeeds = slider_topic_splitting_values[splitting_topic];
            if (rawSeeds) {
                ['TopicA', 'TopicB'].forEach(function (k) {
                    if (rawSeeds[k] && Array.isArray(rawSeeds[k])) {
                        rawSeeds[k] = rawSeeds[k].filter(function (x) { return x && typeof x === "object"; });
                    }
                });
            }
            var postDataTopicSplitting = {
                new_document_seeds: rawSeeds,
                old_circle_positions: new_circle_positions,
                topic_id: vis_state.topic,
                current_number_of_topics: Object.values(new_circle_positions['0.0']).length,
                //mdsData: mdsData, 
                //lamData: lamData                
            };
            testing = mdsData;

            //4.- Create new new_position circle arrray
            var new_dict_topic_splitting; 
            _tveDebug("split", "POST /Topic_Splitting_Document_Based (waiting for server…)", {
                topic_id: postDataTopicSplitting.topic_id,
                current_number_of_topics: postDataTopicSplitting.current_number_of_topics
            });
            $.ajax({
                type: 'POST',
                url: '/Topic_Splitting_Document_Based',
                async: true,
                data: JSON.stringify(postDataTopicSplitting),
                success: function(data) {
                                
                    new_dict_topic_splitting = data;
                    global_topic_splitting_data = new_dict_topic_splitting;
                    new_circle_positions = JSON.parse(new_dict_topic_splitting['new_circle_positions']); 
                   
                    //1. Update relevantDocumentsDict
                    relevantDocumentsDict = JSON.parse(new_dict_topic_splitting['relevantDocumentsDict_fromPython'].replace(/\bNaN\b/g, "null"));
        
                    //update lambdata with the new informsation
                    updateTopicNamesCircles(new_dict_topic_splitting['PreparedDataObtained_fromPython'], vis_state.topic, mdsData, old_frequency);
                    document.getElementById("renameTopicId").value = name_topics_circles[topicID + vis_state.topic];

        
                    //see_most_relevant_keywords(12)
                    createMdsPlot(1, mdsData, get_new_omega(lambda_lambda_topic_similarity.current)); //update central panel
        
                    topic_on(document.getElementById(topicID+vis_state.topic));
                    
                    //reset selection of documents for topic splitting.
                    slider_topic_splitting_values[splitting_topic] = {};
                    story_hil_operations.push('split');
                    _tveDebug("split", "finished — layout and tables updated (K = " + mdsData.length + ")");
                    
                },
                error: function(xhr, textStatus, errorThrown) {
                    _tveDebug("split", "request failed", { status: xhr && xhr.status, textStatus: textStatus });
                    _tveShowServerError(xhr, "Split topic");
                },
                complete: function () {
                    $("#loadMe").modal("hide");
                },
                contentType: "application/json"             
            });                                
        }

      

        function merging_topics_scenario_1(topic_name_1, topic_name_2){
            _tveDebug("merge", "starting", { with: topic_name_2, base: topic_name_1 });
            $('#loadMe').modal({
                backdrop: 'static',
                keyboard: false
            })

            //make sure you have lower case "o"
            setTimeout(function(){
                $("#loadMe").modal('hide');

            }, 120000);
    
            //get index topic from name    
            var current_index = 0;
            for (var [key, value] of Object.entries(name_topics_circles)) {
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

                if(row_topic_1.Freq>row_topic_1.Total){
                    row_topic_1.Total = row_topic_1.Freq;
                }
                
                if(row_topic_2.Freq>row_topic_2.Total){
                    row_topic_2.Total = row_topic_2.Freq;
                }
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

                if(isNaN(new_relevance)){
                    new_relevance = -Infinity;
                }
                

                row_topic_1.relevance = new_relevance;
                row_topic_2.relevance = new_relevance;

           
                
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
            _tveDebug("merge", "POST /get_new_topic_vector (waiting for server…)", {
                index_topic_name_1: index_topic_name_1,
                index_topic_name_2: index_topic_name_2,
                omega: vis_state.lambda_lambda_topic_similarity
            });

            $.ajax({
                type: 'POST',
                url: '/get_new_topic_vector',
                async: true,
                data: JSON.stringify(postData),                
                success: function(data) {
                                
                    new_circle_positions = data;
                    //5.- get new topic name                    
                    var new_merged_topic_name = 'New merged topic '+name_topics_circles[topicID + (index_topic_name_1+1)].trim()+' & '+ name_topics_circles[topicID + (index_topic_name_2+1)].trim();

                    name_topics_circles[topicID + (index_topic_name_1+1)] = new_merged_topic_name;
                    name_topics_circles[topicID + (index_topic_name_2+1)] = new_merged_topic_name+"-delete";
                    merged_topic_to_delete.push(index_topic_name_2+1);
                    name_merged_topic_to_delete.push(new_merged_topic_name+"-delete");
                        
                    d3.selectAll('#svgMdsPlot').remove();
                    d3.selectAll('#divider_central_panel').remove();
                    document.getElementById("renameTopicId").value = name_topics_circles[topicID + vis_state.topic];
                    $('#idTopic').html(topicID + vis_state.topic);
                    createMdsPlot(1, mdsData, get_new_omega(lambda_lambda_topic_similarity.current)); //update central panel
                    topic_on(document.getElementById(topicID+vis_state.topic));         
                    $("#loadMe").modal('hide');
                    story_hil_operations.push('merge');
                    _tveDebug("merge", "finished — new circle positions received (omega keys: " + Object.keys(new_circle_positions).join(", ") + ")");

                },
                error: function(xhr, textStatus, errorThrown) {
                    _tveDebug("merge", "request failed", { status: xhr && xhr.status, textStatus: textStatus });
                    _tveShowServerError(xhr, "Merge topics");
                    $("#loadMe").modal('hide');
                }, 
                contentType: "application/json",
                dataType: 'json'

             });

        }


        function createMdsPlot(number, mdsData, lambda_lambda_topic_similarity){
            var central = document.getElementById("CentralPanel");
            if (!central) {
                throw new Error("TopicVisExplorer: #CentralPanel is missing. Serve the app with the FastAPI template and hard-refresh the page.");
            }
                        
            //if  previous mdsplot exists, remove it
            d3.selectAll('#svgMdsPlot').remove();
            d3.selectAll('#divider_central_panel').remove();

            //we need to append this to the central panel, not to the old svg
            //all draws of central panel must appear in this svg variable

            var divider_central_panel = document.createElement("hr");
            divider_central_panel.setAttribute("class", "rounded");
            divider_central_panel.setAttribute("id", "divider_central_panel");
            central.appendChild(divider_central_panel) 
            

            var svg = d3.select(central).append("svg")
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
                tveD3SelectById(leftPanelID, "createMdsPlot circleGuide " + size).append("circle")
                    .attr('class', "circleGuide" + size)
                    .attr('r', rSize)
                    .attr('cx', cx)
                    .attr('cy', 0.88*mdsheight + rSize)
                    .style('fill', 'none')
                    .style('stroke-dasharray', '2 2')
                    .style('stroke', '#999');
                tveD3SelectById(leftPanelID, "createMdsPlot lineGuide " + size).append("line")
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


            tveD3SelectById(leftPanelID, "createMdsPlot circleGuideTitle").append("text")
                .attr("x", 10)
                .attr("y", 0.88*mdsheight-10)
                .attr('class', "circleGuideTitle")
                .style("text-anchor", "left")
                .style("fontWeight", "bold")
                .text("Topic frequency");
            tveD3SelectById(leftPanelID, "createMdsPlot circleGuideLabelSmall").append("text")
                .attr("x", cx2 + 10)
                .attr("y", 0.88*mdsheight + 2 * newSmall)
                .attr('class', "circleGuideLabelSmall")
                .style("text-anchor", "start")
                .text(defaultLabelSmall);
            tveD3SelectById(leftPanelID, "createMdsPlot circleGuideLabelMedium").append("text")
                .attr("x", cx2 + 10)
                .attr("y", 0.88*mdsheight + 2 * newMedium)
                .attr('class', "circleGuideLabelMedium")
                .style("text-anchor", "start")
                .text(defaultLabelMedium);
            tveD3SelectById(leftPanelID, "createMdsPlot circleGuideLabelLarge").append("text")
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
            //console.log(' estas son las nuevas posiciones', new_positions);
            var cx_new_positions = -1;
            var cy_new_positions = -1;
            points.append("circle")
                .attr("class", "dot")
                .style("opacity",base_opacity)
                .style("fill", color_topic_1_1)
                .attr("r", function(d) {
                    var current_element  = mdsData.find(element => element.topics == d.topics);

                    return (Math.sqrt((current_element.Freq/100)*mdswidth*mdsheight*circle_prop/Math.PI)); //se hace esto porque el new_positions array no inclue 'Freq', en cambioe el MdsDATA YA LO OBTIENE
                    
                })
                .attr("cx", function(d) {
                    cx_new_positions+=1
                    //console.log('este es el cx_new_positions', cx_new_positions);
                    if(new_positions[cx_new_positions]!= undefined){
                        return (xScale(+new_positions[cx_new_positions][0])); 

                    }
                    else{
                        name_topics_circles[topicID + d.topics] = name_topics_circles[topicID + d.topics]+'_topicwitherror'
                        topics_with_error.push(d.topics+'-'+name_topics_circles[topicID + d.topics]);
                    }

                    //return (xScale(+new_positions[d.topics-1][0])); 


                })
                .attr("cy", function(d) {
                    //return (yScale(+d.y));
                    cy_new_positions+=1;
                    if(new_positions[cy_new_positions] != undefined){
                        return (yScale(+new_positions[cy_new_positions][1]));

                    }

                    //return (yScale(+new_positions[d.topics-1][1]));
                })
                .attr("stroke", "black")
                .attr("id", function(d) {        
                    return (topicID + d.topics);
                })
                .on("click", function(d) {



                    // prevent click event defined on the div container from firing
                    // http://bl.ocks.org/jasondavies/3186840
                    d3.event.stopPropagation();
                    old_topic = topicID + vis_state.topic;
                    if (vis_state.topic > 0 && old_topic != this.id) {
                        topic_off(document.getElementById(old_topic));
                    }
                    if(first_time_clicking_circle==true){
                        if (typeof introJs === "function") { try { introJs().exit(true); } catch(e){} }
                        topic_off(document.getElementById(topicID+'5'));
                        first_time_clicking_circle = false;
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
                        return name_topics_circles[topicID + d.topics] ;});

            // text to indicate topic
        var frequency_circle_d = -1;                
        var cx_new_positions = -1;
        var cy_new_positions = -1;
        points.append("text")
        .attr("class", "txt")
        .attr("width", function(d) {
            frequency_circle_d+=1;
            if(new_positions[frequency_circle_d] == undefined){
                return 0;

            }
            var current_element  = mdsData.find(element => element.topics == d.topics);

            return (2*Math.sqrt((current_element.Freq/100)*mdswidth*mdsheight*circle_prop/Math.PI));
            //return (2*Math.sqrt((mdsData[d.topics-1].Freq/100)*mdswidth*mdsheight*circle_prop/Math.PI))

        })
        .attr("x", function(d) {
            
            cx_new_positions+=1;
            if(new_positions[cx_new_positions] != undefined){
                return (xScale(new_positions[cx_new_positions][0]));

            }

            //return (xScale(new_positions[d.topics-1][0]));

        })
        .attr("y", function(d) {
            cy_new_positions+=1;
            if(new_positions[cy_new_positions] != undefined){
                return (yScale(new_positions[cy_new_positions][1]));

            }

        })
        .attr("id", function(d) {        
            return ("text-"+topicID + d.topics);
        })
        .on("click", function(d) {



            // prevent click event defined on the div container from firing
            // http://bl.ocks.org/jasondavies/3186840
            d3.event.stopPropagation();
            old_topic = topicID + vis_state.topic;
            if (vis_state.topic > 0 && old_topic != this.id) {
                topic_off(document.getElementById(old_topic));
            }
            if(first_time_clicking_circle==true){
                if (typeof introJs === "function") { try { introJs().exit(true); } catch(e){} }
                topic_off(document.getElementById(topicID+'5'));
                first_time_clicking_circle = false;
            }
            
            // make sure topic input box value and fragment reflects clicked selection
            vis_state.topic = d.topics;
            

            splitting_topic= vis_state.topic
            
            document.getElementById("renameTopicId").value = name_topics_circles[topicID + d.topics]
            $('#idTopic').html(topicID + d.topics);
            
            topic_on(document.getElementById(topicID+d.topics));             
        })
        .attr("stroke", "black")
        .style("stroke-opacity", .2)
        .attr("opacity", 1)
        .style("text-anchor", "middle")
        .style("font-size", "11px")  
        .append("tspan")
            .attr("dy", "0em")
            .text(function(d){
                var freq_current_topic = Math.round(mdsData[d.topics-1].Freq* 10) / 10;
                
                return "("+freq_current_topic+"%)";
            })
        .append("tspan")
            .attr("dy", "2em")
            .attr('class', 'txt')
            .text(function(d){
                return name_topics_circles[topicID + d.topics];
            });


        //overflow-text in svg
       
        d3.selectAll('.txt').call(dotme);
                        
        //remove topic merged
        for(var i = 0; i<merged_topic_to_delete.length; i++){
            var d_topics_current = merged_topic_to_delete[i];
            d3.selectAll('#text-'+topicID + d_topics_current).remove();
            d3.selectAll("#circles_center-"+topicID + d_topics_current).remove();            
            d3.selectAll('#'+topicID + d_topics_current).remove();

        }
        //topicos errados
        for(var i = 0; i<topics_with_error.length; i++){

            var d_topics_current = Number(topics_with_error[i].split('-')[0]);
            var d_name_current = topics_with_error[i].split('-')[1]
            if(d_name_current ==name_topics_circles[topicID + d_topics_current] ){
                d3.selectAll('#text-'+topicID + d_topics_current).remove();
                d3.selectAll("#circles_center-"+topicID + d_topics_current).remove();            
                d3.selectAll('#'+topicID + d_topics_current).remove();
            }            
        }


        arrangeCircles();        

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


          
        
       if( type_vis === 1){
           
 



            createMdsPlot(1, mdsData, get_new_omega(lambda_lambda_topic_similarity.current))        
            createBarPlot("#BarPlotPanelDiv", dat3, barFreqsID,"bar-totals", "terms", "bubble-tool", "xaxis", R) //esto crea el bar plot por primera vez. 
            d3.selectAll('#tableRelevantDocumentsClass_Model1').attr("transform", "translate("  +0 + "," +0+ ")")

            
            splitting_topic= vis_state.topic // es 1 by default
            
            document.getElementById("renameTopicId").value = name_topics_circles[topicID + vis_state.topic]
            $('#idTopic').html(topicID + vis_state.topic);
            topic_on(document.getElementById(topicID+vis_state.topic))
        
       }

       if(type_vis === 2){
            // Three-column template: A | Sankey | B. Document tables live under
            // the left/right column roots; create id hooks when not in HTML.
            (function ensureMulticorpusDocumentPanelRoots() {
                var elLeft = document.getElementById("BarPlotPanel");
                var elRight = document.getElementById("BarPlotPanel_2");
                if (!elLeft || !elRight) { return; }
                if (!document.getElementById("DocumentsPanel")) {
                    var d1 = document.createElement("div");
                    d1.id = "DocumentsPanel";
                    d1.setAttribute("class", "tve-documents-nested");
                    elLeft.appendChild(d1);
                }
                if (!document.getElementById("DocumentsPanel_2")) {
                    var d2 = document.createElement("div");
                    d2.id = "DocumentsPanel_2";
                    d2.setAttribute("class", "tve-documents-nested");
                    elRight.appendChild(d2);
                }
            })();

            get_name_node_sankey(matrix_sankey[get_new_omega(lambda_lambda_topic_similarity.current)], vis_state.lambda_topic_similarity)
            var R_b = Math.min(jsonData_2['R'], 20);
            var lamDataB0 = [];
            for (var ib = 0; ib < jsonData_2['tinfo'].Term.length; ib++) {
                var ob = {};
                for (var keyb in jsonData_2['tinfo']) {
                    ob[keyb] = jsonData_2['tinfo'][keyb][ib];
                }
                lamDataB0.push(ob);
            }
            // Initial bar charts use Category == "Default". Do not use lamData.slice(0, R) —
            // that is the first R rows across all categories, so each corpus can yield a
            // different number of "Default" rows. Filter Default from full tinfo, same cap each side.
            var _sankeyTermCap = Math.min(R, R_b, number_terms_sankey);
            var defA0 = lamData.filter(function(d) { return d.Category == "Default"; });
            var defB0 = lamDataB0.filter(function(d) { return d.Category == "Default"; });
            var n0 = Math.min(_sankeyTermCap, defA0.length, defB0.length);
            var dat3_sankey_a = defA0.slice(0, n0);
            var dat3_sankey_b = defB0.slice(0, n0);
            sankeyTermActiveCap = n0;
            // Add barplot into the left panel
            createBarPlot("#BarPlotDiv_zero", dat3_sankey_a, barFreqsID,"bar-totals", "terms", "bubble-tool", "xaxis", n0);
            // Add barplot into the right panel (corpus B: own tinfo, not corpus A)
            createBarPlot("#BarPlotDiv_b_zero", dat3_sankey_b, barFreqsID_2,"bar-totals_2", "terms_2", "bubble-tool_2", "xaxis_2", n0);
            tveEqualizeMulticorpusBarChartHeights();

            // Add documents into the left column
           var RelevantDocumentsTableDiv = document.createElement("div");
           RelevantDocumentsTableDiv.setAttribute("id", "RelevantDocumentsTableDiv");
           RelevantDocumentsTableDiv.setAttribute("class", "RelevantDocumentsSankeyDiagram mt-4");
           document.getElementById("DocumentsPanel").appendChild(RelevantDocumentsTableDiv);
           const  div = document.getElementById('RelevantDocumentsTableDiv');
           div.insertAdjacentHTML('afterbegin', '<table  id="tableRelevantDocumentsClass_Model1" class="table table-hover"> <thead> <tr> <th class="text-center" data-field="topic_perc_contrib" scope="col">%</th> <th class="text-center" data-field="text" scope="col">Tweet</th> </tr> </thead> </table>');


           // Add documents into the right column
           var RelevantDocumentsTableDiv_2 = document.createElement("div");
           RelevantDocumentsTableDiv_2.setAttribute("id", "RelevantDocumentsTableDiv_2");
           RelevantDocumentsTableDiv_2.setAttribute("class", "RelevantDocumentsSankeyDiagram mt-4");
           document.getElementById("DocumentsPanel_2").appendChild(RelevantDocumentsTableDiv_2);
           const  div_2 = document.getElementById('RelevantDocumentsTableDiv_2');
           div_2.insertAdjacentHTML('afterbegin', '<table  id="tableRelevantDocumentsClass_Model2" class="table table-hover"> <thead> <tr> <th class="text-center" data-field="topic_perc_contrib" scope="col">%</th> <th class="text-center" data-field="text" scope="col">Tweet</th> </tr> </thead> </table>');

            var _matrixSankey0 = matrix_sankey[get_new_omega(lambda_lambda_topic_similarity.current)];
            var _minF0 = vis_state.min_value_filtering;
            var _maxF0 = vis_state.max_value_filtering;
            requestAnimationFrame(function () {
                tveEqualizeMulticorpusBarChartHeights();
                visualize_sankey(_matrixSankey0, _minF0, _maxF0);
            });
       }
       




        function createBarPlot(to_select, dat3, barFreqsID_actual, bar_totals_actual, terms_actual,  splitting, xaxis_class, number_terms){
            var _termCap = (typeof number_terms === "number" && number_terms > 0) ? Math.min(number_terms, 20) : R;
            var plotRootId = String(to_select).replace(/^#+/, "").trim();
            if (!plotRootId) { throw new Error("TopicVisExplorer: createBarPlot: empty to_select"); }
            var rootD3 = tveD3SelectById(plotRootId, "createBarPlot root");
            var rootEl = rootD3.node();
            var rch = rootEl.clientHeight || 0;
            var rbb = rootEl.getBoundingClientRect();
            if (rch < 4) { rch = rbb.height || 0; }
            if (rch < 4) { rch = 260; }
            var svgH = Math.max(180, Math.floor(0.35 * rch));

            var svg = rootD3.append("svg") // BarPlotPanelDiv or BarPlotDiv_zero / BarPlotDiv_b_zero
            .attr("width", "100%")
            .attr("height", svgH);

            var bounds_barplot = svg.node().getBoundingClientRect();
            if (bounds_barplot.height < 8) {
                barheight = svgH - 0.5 * termwidth;
            } else {
                barheight = bounds_barplot.height - 0.5*termwidth;
            }
            barheightByPlotId[barFreqsID_actual] = barheight;
            var _bw = bounds_barplot.width;
            if (_bw < 4) { _bw = rbb.width || 0; }
            barwidth = _bw - 1.5*termwidth
        
            
        
            var barDefault2 = dat3.filter(function(d) {
                return d.Category == "Default";
            });
            
            barDefault2 = barDefault2.slice(0, _termCap)
            
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
            

                var legH = Math.max(36, Math.floor(0.03 * rch));
                var legend_svg = rootD3.append("svg")
                .attr("width", "100%")
                .attr("height", legH)
                .attr("id", bar_totals_actual+"legend_svg")
                
                mdsheight = 0
                var barguide = {"width": 100, "height": 15};
                tveD3SelectById(bar_totals_actual+"legend_svg", "createBarPlot legend " + bar_totals_actual).append("rect")
                    .attr("x", 0)
                    .attr("y", mdsheight + 10)
                    .attr("height", barguide.height)
                    .attr("width", (barguide.width/2))
                    .style("fill", color1_1)
                    .attr("opacity", 0.4);
                tveD3SelectById(bar_totals_actual+"legend_svg", "createBarPlot legendText1 " + bar_totals_actual).append("text")
                    .attr("x", (barguide.width/2)+ 5)
                    .attr("y", mdsheight + 10 + barguide.height/2)
                    .style("dominant-baseline", "middle")
                    .text("Overall term frequency");
                
                tveD3SelectById(bar_totals_actual+"legend_svg", "createBarPlot legend2 " + bar_totals_actual).append("rect")
                    .attr("x", 1.8*barguide.width+ 5)
                    .attr("y", mdsheight + 10)
                    .attr("height", barguide.height)
                    .attr("width", (barguide.width/4))
                    .style("fill", color2_1)
                    .attr("opacity", 0.8);
                tveD3SelectById(bar_totals_actual+"legend_svg", "createBarPlot legendText2 " + bar_totals_actual).append("text")
                    .attr("x", 1.8*barguide.width+(barguide.width/4) + 10 )
                    .attr("y", mdsheight + 10 + barguide.height/2 )
                    .style("dominant-baseline", "middle")
                    .text("Estimated term frequency within the selected topic");
                
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
                .attr("height", y.bandwidth()/2)
                .attr("width", function(d) {
                    return Math.max(0, x(d.Total));
                })
                .style("fill", color2_2)
                .attr("opacity", 0.4);
            
            // Add word labels to the side of each bar
            basebars
                .append("text")
                .attr("x", -5)
                .attr("class", terms_actual)
                .attr("y", function(d) {
                    return y(d.Term) + 9;
                })
                .attr("id", function(d) {
                    return (termID + d.Term);
                })
                .style("text-anchor", "end") // right align text - use 'middle' for center alignment
                .text(function(d) {
                    return d.Term;
                })
                .on("mouseover", function() {
                    //this.style["fontWeight"] = "bolder"
                    var current_term = this.id.split('-')[1];
                    d3.selectAll('#barplotterm-'+current_term).style("font-weight",'bolder');
                    if(type_vis==1){
                        d3.select('#bar-totals-'+current_term).style("fill",color1_2);
                        d3.select('#bar-freq-estimated-'+current_term).style("fill",color2_2);
                    }
                    else{
                        d3.select('#bar-totals-'+current_term).style("fill",color1_2);
                        d3.select('#overlay-'+current_term).style("fill",color2_2);

                        d3.select('#bar-totals_2-'+current_term).style("fill",color1_2);
                        d3.select('#overlay_2-'+current_term).style("fill",color2_2);
                    }                    
                })
                .on("mouseout", function() {
                    
                    var current_term = this.id.split('-')[1];

                    d3.selectAll('#barplotterm-'+current_term).style("font-weight",'normal');
                    if(type_vis==1){
                        d3.select('#bar-freq-estimated-'+current_term).style("fill",color2_1);
                        d3.select('#bar-totals-'+current_term).style("fill",color1_1);
                    }
                    else{
                        d3.select('#bar-totals-'+current_term).style("fill",color1_1);
                        d3.select('#overlay-'+current_term).style("fill",color2_1);

                        d3.select('#bar-totals_2-'+current_term).style("fill",color1_1);
                        d3.select('#overlay_2-'+current_term).style("fill",color2_1);
                    }                    
                });

            // Add/remove word (+/−) SVG controls were removed from the bar chart;
            // ``_tveAddRemoveWord`` remains for a possible future UI.

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
                var svgRightPanel = tveD3SelectById("BarPlotPanel_2", "init_forms right column").append("div");
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
                var _bp2a = document.getElementById("BarPlotPanel_2");
                if (!_bp2a) { throw new Error("TopicVisExplorer: init_forms: missing #BarPlotPanel_2 (append right slider)"); }
                _bp2a.appendChild(inputDivRightPanel_zero);

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
                lambdaInputRightPanel.step = jsonData_2['lambda.step'] != null ? jsonData_2['lambda.step'] : data['lambda.step'];
                lambdaInputRightPanel.value = vis_state.lambda_b;
                lambdaInputRightPanel.id = lambdaID+"RightPanel";
                lambdaInputRightPanel.setAttribute("list", "ticks"); 
                sliderDivRightPanel.appendChild(lambdaInputRightPanel);

                var lambdaLabelRightPanel = document.createElement("label");
                lambdaLabelRightPanel.setAttribute("id", lambdaLabelID+"RightPanel");
                lambdaLabelRightPanel.setAttribute("class", "ColumnDiv");
                lambdaLabelRightPanel.setAttribute("for", lambdaID+"RightPanel");
                lambdaLabelRightPanel.innerHTML = "Relevance score: &#955 = <span id='" + lambdaID+"RightPanel" + "-value'>" + vis_state.lambda_b + "</span>";
                lambdaDivRightPanel.appendChild(lambdaLabelRightPanel);

                // Create the svg to contain the slider scale:
                var scaleContainerRightPanel = tveD3SelectById("RelevanceSliderContenedorRightPanel", "init_forms right RelevanceSlider scale").append("svg")
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
                var inputDivBZero = document.createElement("div");
                inputDivBZero.setAttribute("id", "BarPlotDiv_b_zero");
                var _bp2b = document.getElementById("BarPlotPanel_2");
                if (!_bp2b) { throw new Error("TopicVisExplorer: init_forms: missing #BarPlotPanel_2 (append BarPlotDiv_b_zero)"); }
                _bp2b.appendChild(inputDivBZero);
            }

            d3.selectAll('#'+BarPlotPanelDivId).remove();

            var svgLeftPanel = tveD3SelectById("BarPlotPanel", "init_forms left column").append("div");
            svgLeftPanel.attr("id", BarPlotPanelDivId);
            //svgLeftPanel.attr("class", "border_box my-1")
            
            if(type_vis==1){
                var topicNameRow = document.createElement("div");
                topicNameRow.setAttribute("id", "full_topic_name_row")
                topicNameRow.setAttribute("class", "RowDiv ") //border_box my-1
                document.getElementById(BarPlotPanelDivId).appendChild(topicNameRow)

                var topicNameDiv = document.createElement("div");
                topicNameDiv.setAttribute("id", "topic_name_div_full_row")
                topicNameDiv.setAttribute("class", "ColumnDiv")
                topicNameRow.appendChild(topicNameDiv) 



            }
            var topicDiv = document.createElement("div");
            topicDiv.setAttribute("id", "topic_name_and_buttons_div")
            topicDiv.setAttribute("class", "RowDiv ") //border_box my-1
            document.getElementById(BarPlotPanelDivId).appendChild(topicDiv) 
            if(type_vis==1){
                var topicButtonsDivLeft = document.createElement("div");
                topicButtonsDivLeft.setAttribute("id", "topic_buttons_div_left_full_row")
                topicButtonsDivLeft.setAttribute("class", "ColumnDiv")
                topicDiv.appendChild(topicButtonsDivLeft) 

                var topicButtonsDivRight = document.createElement("div");
                topicButtonsDivRight.setAttribute("id", "topic_buttons_div_right_full_row")
                topicButtonsDivRight.setAttribute("class", "ColumnDiv")
                topicDiv.appendChild(topicButtonsDivRight) 
            }

            if(type_vis==2){
                var topicNameDiv = document.createElement("div");
                topicNameDiv.setAttribute("id", "topic_name_div")
                topicNameDiv.setAttribute("class", "ColumnDiv")
                topicDiv.appendChild(topicNameDiv) 

                var topicButtonsDiv = document.createElement("div");
                topicButtonsDiv.setAttribute("id", "topic_buttons_div")
                topicButtonsDiv.setAttribute("class", "ColumnDiv")
                topicDiv.appendChild(topicButtonsDiv) 

            }
            
            
            
            var reverse = document.createElement("button");
            reverse.setAttribute("id", topicReverse);

                    
            reverse.setAttribute("class", "btn btn-primary btnTopic");
            reverse.innerHTML = "Undo";
            //reverse.setAttribute("disabled", true);

            var help = document.createElement("button");
            help.setAttribute("id", 'help_button');

                    
            help.setAttribute("class", "btn btn-info btnTopic");
            help.innerHTML = "<i class='fas fa-1x fa-info-circle'></i>";

            var export_topics_button = document.createElement("button");
            export_topics_button.setAttribute("id", "export_topics_button");
            export_topics_button.setAttribute("class", "btn btn-secondary btnTopic");
            export_topics_button.setAttribute("title", "Download a JSON snapshot of the current topics (local file, no server upload)");
            export_topics_button.innerHTML = "<i class='fas fa-1x fa-file-download'></i>";

            if(type_vis==1){
                topicButtonsDivRight.appendChild(help);
                topicButtonsDivRight.appendChild(export_topics_button);
    
            }
            else{
                topicButtonsDiv.appendChild(help);
                topicButtonsDiv.appendChild(export_topics_button);
    
                topicButtonsDiv.appendChild(reverse);
            }

            d3.select("#export_topics_button").on("click", function(){
                var _urlParams = new URLSearchParams(window.location.search);
                var _scen = _urlParams.get("scenario") || "default";
                var _topicsOut = [];
                if (type_vis == 1 && name_topics_circles) {
                    Object.keys(name_topics_circles).forEach(function(k){
                        var topicNum = parseInt(String(k).replace(String(topicID), ""), 10);
                        if (isNaN(topicNum)) { return; }
                        var terms = [];
                        if (lamData && lamData.length) {
                            var cat = "Topic" + topicNum;
                            terms = lamData.filter(function(d){ return d.Category === cat; })
                                .slice(0, 20)
                                .map(function(d){ return d.Term; });
                        }
                        _topicsOut.push({ id: topicNum, label: name_topics_circles[k], top_terms: terms });
                    });
                } else if (type_vis == 2 && name_topics_sankey) {
                    Object.keys(name_topics_sankey).forEach(function(k){
                        _topicsOut.push({ key: k, label: name_topics_sankey[k] });
                    });
                }
                var exportObj = {
                    _tve_version: "1.0",
                    type_vis: type_vis,
                    scenario: _scen,
                    exported_at: new Date().toISOString(),
                    lambda: vis_state ? vis_state.lambda : null,
                    lambda_b: vis_state ? vis_state.lambda_b : null,
                    omega_topic_similarity: vis_state ? vis_state.lambda_lambda_topic_similarity : null,
                    current_topic_id: vis_state ? vis_state.topic : null,
                    topics: _topicsOut,
                    circle_positions: (typeof new_circle_positions !== "undefined") ? new_circle_positions : null
                };
                if (type_vis == 1 && is_human_in_the_loop == true) {
                    exportObj.relevantDocumentsDict = (typeof relevantDocumentsDict !== "undefined") ? relevantDocumentsDict : null;
                }
                var blob = new Blob([JSON.stringify(exportObj, null, 2)], { type: "application/json" });
                var a = document.createElement("a");
                a.href = URL.createObjectURL(blob);
                a.download = "tve_topics_" + _scen.replace(/[^a-zA-Z0-9_-]+/g, "_") + ".json";
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(a.href);
            });

  

  

            d3.select("#help_button")
            .on("click", function() {
                show_tutorial()

            });


            d3.select("#apply_reverse_topic_model") //el usuario desea continuar con el mergin
                .on("click", function() {
                    var last_state_dict = old_topic_model_states.pop();
                    

                    relevantDocumentsDict = last_state_dict.relevantDocumentsDict;
                    lamData = last_state_dict.lamData;
                    mdsData = last_state_dict.mdsData;
                    new_circle_positions = last_state_dict.new_circle_positions;
                    name_topics_circles = last_state_dict.name_topics_circles;
                    vis_state.topic = last_state_dict.current_topic_id;
                    slider_topic_splitting_values = last_state_dict.slider_topic_splitting_values;
                    
                    topics_splitted = last_state_dict.topics_splitted;


                    merged_topic_to_delete =  last_state_dict.merged_topic_to_delete;
                    name_merged_topic_to_delete = last_state_dict.name_merged_topic_to_delete;

                    //quitar del arreglo de topicos a no mostrar. En un split hay que crear la condicion para saber de que arreglo sacar el ultimo topico baneado
                    
                    var last_operation = story_hil_operations.pop();
                    if(last_operation =='merge'){
                        merged_topic_to_delete.pop();
                        name_merged_topic_to_delete.pop();
                    }



                    d3.selectAll('#svgMdsPlot').remove();
                    d3.selectAll('#divider_central_panel').remove();
        
                    document.getElementById("renameTopicId").value = name_topics_circles[topicID + vis_state.topic]
                    $('#idTopic').html(topicID + vis_state.topic);
        
        
        
                    createMdsPlot(1, mdsData, get_new_omega(lambda_lambda_topic_similarity.current)); //update central panel
                    topic_on(document.getElementById(topicID+vis_state.topic));
        

                    $.ajax({
                        type: 'POST',
                        url: '/undo_merge_splitting',
                        async: false,
                        success: function() {
                        },
                        
        
                     });

                    
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

          
           d3.select("#apply_topic_merging") //el usuario desea continuar con el mergin
                .on("click", function() {


                    //hacer_merge = true
                    
                    var merging_final_topic_1 = document.getElementById("merging_topic_1_name").innerText;
                    var merging_final_topic_2 =  $("#selectTopicMerge" ).val()


                    save_state_data()

                    merging_topics_scenario_1(merging_final_topic_1, merging_final_topic_2);

                    
                });
       
           

           var split = document.createElement("button");
           split.setAttribute("id", topicSplit);
           split.setAttribute("class", "btn btn-primary btnTopic");           
           split.innerHTML = "Split";

           //split.setAttribute("disabled", true);

  
        
            var edit = document.createElement("button");
            edit.setAttribute("id", topicEdit);
            edit.setAttribute("class", "btn btn-primary btnTopic");
            edit.innerHTML = "Rename";

            if(type_vis==1){
                topicButtonsDivLeft.appendChild(edit);
                topicButtonsDivLeft.appendChild(merge);

                topicButtonsDivLeft.appendChild(split);
                topicButtonsDivLeft.appendChild(reverse);



            }
            else{
                topicButtonsDiv.appendChild(edit);

            }

            d3.select("#"+topicReverse)
            .on("click", function() {

                $('#ReverseModel').modal(); 
            });
            d3.select("#"+topicMerge)
            .on("click", function() {
                var current_element_to_merge = mdsData.find(element => Number(element.topics) == Number(merging_topic_1));
                //name_topics_circles[topicID + current_element_to_merge.topics];

                if(! topics_splitted.includes(topicID +current_element_to_merge.topics)){
                    

                    /*
                    for (const [key, value] of Object.entries(name_topics_circles )) {
                        console.log(' key', key, 'value', value);
                    }
                    */

 
        
                    if(merging_topic_1!=-1){  
                        $('.merging_topic_1').html(merging_topic_1); //this is one topic wish I would like to merge
                        //populate el dropdown, topics should be sorted according to the distance to the current topic
                        $('#selectTopicMerge').empty();
                        var topics_name_sorted_by_distance = get_topics_sorted_by_distance(mdsData, get_new_omega(lambda_lambda_topic_similarity.current), merging_topic_1)
                        $.each(topics_name_sorted_by_distance, function(i, p) {
                            //add the array with the topics sorted according to the distance to the current topic
                            if(i!=0 && ( !(name_merged_topic_to_delete.includes(topics_name_sorted_by_distance[i])))){ //el primer elemento no se ocupa, ya que es el mismo topico con el q se quiere unir. ESTO NO OCURRE ASI EN EL SCENARIO 2. Ojo, tambien chequeamos que ese elemento no haya que borrarse
                                
                                

                                var current_index = 1;
                                for (var [key, value] of Object.entries(name_topics_circles)) {
                                    if(value.trim() == topics_name_sorted_by_distance[i].trim()){
                                    
                                        var index_topic_name_1 = current_index;
                                    }                                    
                                    current_index+=1;
                                }
                                if(! topics_splitted.includes(topicID +index_topic_name_1)){

                                    $('#selectTopicMerge').append($('<option></option>').val(topics_name_sorted_by_distance[i]).html(topics_name_sorted_by_distance[i]));
                                }


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

                }
                else{
                    $('#cant_merge_this_topic').modal();                        

                }                
            });

            
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
                    createMdsPlot(1, mdsData, get_new_omega(lambda_lambda_topic_similarity.current))


                    topic_on(document.getElementById(topicID+vis_state.topic))


                })
            }
            else{
                d3.select("#rename_topic_button")
                .on("click", function(){

                    //rename the topic



                    name_topics_sankey[document.getElementById("idTopic").innerText] = document.getElementById("renameTopicId").value
                    
                    
                    //visualize the new name
                    visualize_sankey(matrix_sankey[get_new_omega(lambda_lambda_topic_similarity.current)], vis_state.min_value_filtering, vis_state.max_value_filtering)
                    $('#topic_name_selected_1').html(name_topics_sankey[document.getElementById("idTopic").innerText])                    


                  
                })
            }
            d3.select("#rename_topic_button2")
                .on("click", function(){


                    //cambiar el nombre del topico segun lo especifique el usuario
                    name_topics_sankey[document.getElementById("idTopic2").innerText] = document.getElementById("renameTopicId2").value
                    
                    visualize_sankey(matrix_sankey[get_new_omega(lambda_lambda_topic_similarity.current)], vis_state.min_value_filtering, vis_state.max_value_filtering)
                    $('#topic_name_selected_2').html(name_topics_sankey[document.getElementById("idTopic2").innerText])                    
                    //visualizar el nuevo nombre
                    
                })

            //colocar #apply_merging.  "aqui esta el antiguo codigo para el merge"

            function tveSplitDocumentCount(arr) {
                if (!arr || !Array.isArray(arr)) { return 0; }
                var n = 0;
                for (var i = 0; i < arr.length; i++) {
                    if (arr[i] && typeof arr[i] === "object") { n++; }
                }
                return n;
            }
            function tveSplittingSeedsStatus(seeds) {
                if (seeds == null || typeof seeds !== "object") {
                    return { ok: false, reason: "no_seed_bucket" };
                }
                var a = seeds.TopicA;
                var b = seeds.TopicB;
                if (typeof a === "undefined") { return { ok: false, reason: "missing_a" }; }
                if (typeof b === "undefined") { return { ok: false, reason: "missing_b" }; }
                if (!Array.isArray(a)) { return { ok: false, reason: "missing_a" }; }
                if (!Array.isArray(b)) { return { ok: false, reason: "missing_b" }; }
                if (tveSplitDocumentCount(a) < 1) { return { ok: false, reason: "empty_a" }; }
                if (tveSplitDocumentCount(b) < 1) { return { ok: false, reason: "empty_b" }; }
                return { ok: true, reason: "ok" };
            }
            function tveSplitModalMessageForReason(reason) {
                switch (reason) {
                case "missing_a":
                case "empty_a":
                    return "Add at least one document to new subtopic A (choose the A radio in at least one row).";
                case "missing_b":
                case "empty_b":
                    return "Add at least one document to new subtopic B (choose the B radio in at least one row).";
                case "no_seed_bucket":
                default:
                    return "You need at least one document in new subtopic A and at least one in new subtopic B. Use the A, B, or neither radios for each document row.";
                }
            }
            function tveSetSplitModalValidation(message) {
                var $el = $("#tve_split_validation_alert");
                if (!$el.length) { return; }
                if (!message) {
                    $el.addClass("d-none").empty();
                    return;
                }
                $el.removeClass("d-none");
                $el.empty();
                $("<div>", { "class": "alert alert-warning mb-0", role: "alert" }).text(message).appendTo($el);
            }
            function tveUpdateSplitModalStatus() {
                var seeds = slider_topic_splitting_values[splitting_topic];
                var st = tveSplittingSeedsStatus(seeds);
                var a = seeds && Array.isArray(seeds.TopicA) ? tveSplitDocumentCount(seeds.TopicA) : 0;
                var b = seeds && Array.isArray(seeds.TopicB) ? tveSplitDocumentCount(seeds.TopicB) : 0;
                var $status = $("#tve_split_subtopic_status");
                if ($status.length) {
                    $status.text("Subtopic A: " + a + " document(s) — Subtopic B: " + b + " document(s). Both need at least one to split.");
                }
                if (st.ok) {
                    tveSetSplitModalValidation(null);
                }
            }

            d3.select("#"+topicSplit)
            .on("click",function(){

                    splitting_topic = vis_state.topic;
                    _tveDebug("split", "open split modal (synced splitting_topic from vis_state.topic)", {
                        vis_state_topic: vis_state.topic,
                        splitting_topic: splitting_topic
                    });
                    tveSetSplitModalValidation(null);
                    $('#topic_to_split_name').html(name_topics_circles[topicID + vis_state.topic]);                    
                    $('#SplitTopicModal').modal();
    
                    updateRelevantDocumentsTopicSplitting(vis_state.topic - 1, relevantDocumentsDict, 1);
                    setTimeout(function () { tveUpdateSplitModalStatus(); }, 0);
                           
            });

            $("#apply_topic_splitting").click(function() {
                if (splitting_topic !== vis_state.topic) {
                    _tveDebug("split", "apply: splitting_topic out of sync with vis_state.topic (stale split modal?)", {
                        splitting_topic: splitting_topic,
                        vis_state_topic: vis_state.topic
                    });
                }
                var seeds = slider_topic_splitting_values[splitting_topic];
                var st = tveSplittingSeedsStatus(seeds);
                _tveDebug("split", "apply_topic_splitting", {
                    splitting_topic: splitting_topic,
                    vis_state_topic: vis_state.topic,
                    status: st
                });
                if (!st.ok) {
                    tveSetSplitModalValidation(tveSplitModalMessageForReason(st.reason));
                    tveUpdateSplitModalStatus();
                    return;
                }
                tveSetSplitModalValidation(null);
                $("#SplitTopicModal").modal("hide");
                save_state_data();
                splitting_topics_document_based_scenario_1();
            });


    
            var inputDiv_zero = document.createElement("div");
            inputDiv_zero.setAttribute("id", "BarPlotDiv_zero"); //inputDiv_zero.setAttribute("class", "border_box my-1");
            var _barPlotWrap = document.getElementById(BarPlotPanelDivId);
            if (!_barPlotWrap) { throw new Error("TopicVisExplorer: init_forms: missing #" + BarPlotPanelDivId + " (BarPlot left stack)"); }
            _barPlotWrap.appendChild(inputDiv_zero);
            
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
            var scaleContainer = tveD3SelectById(sliderDivID, "init_forms RelevanceSlider scale").append("svg")
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
            var svgCentralPanel = tveD3SelectById("CentralPanel", "init_forms TopicSimilarity panel").append("div");
            svgCentralPanel.attr("id", "TopicSimilarityMetricPanel");
    
            var sliderDivLambdaTopicSimilarity = document.createElement("div");
            sliderDivLambdaTopicSimilarity.setAttribute("id", sliderDivIDLambdaTopicSimilarity);
            sliderDivLambdaTopicSimilarity.setAttribute("class", "RowDiv");
            document.getElementById("TopicSimilarityMetricPanel").appendChild(sliderDivLambdaTopicSimilarity)  //document.getElementById(visID).appendChild(inputDiv); //creo que esto debiera estar unido al svg mejor


            if(type_vis==2){


                
                /* This section is to allow users to filtering paths on sankey diagram*/

                var min_similarity_score = Infinity
                var max_similarity_score = -Infinity
                if(scenario_2_is_baseline_metric == true){
                    var graph_temp = matrix_sankey[get_new_omega(lambda_lambda_topic_similarity.current)];

                    graph_temp.links.filter(function(el){
                        if(el.value < min_similarity_score){
                            min_similarity_score = el.value;
                        }
    
                        if(el.value > max_similarity_score){
                            max_similarity_score = el.value;
                        }
                    });
                    var inverted_scale = d3.scaleLinear()
                    .domain([min_similarity_score, max_similarity_score])
                    .range([max_similarity_score, min_similarity_score]);


                    //aqui hay q dar vuelta la wea
                    if(scenario_2_is_baseline_metric==true){
                            graph_temp.links = graph_temp.links.map(function(e) { 
                            e.value = inverted_scale.invert(e.value);
                            //e.value = -e.value; 
                            return e;
                        });        
                    }
                    matrix_sankey[get_new_omega(lambda_lambda_topic_similarity.current)] = graph_temp;
                                        
                }
                else{
                    var min_similarity_score = -1.0;
                    var max_similarity_score = 1.0;
                }


                min_similarity_score =   Math.round(  min_similarity_score* 100) / 100
                max_similarity_score = Math.round(  max_similarity_score* 100) / 100
               

                var svgCentralPanelFiltering = tveD3SelectById("CentralPanel", "init_forms TopicSimilarity filtering").append("div");
                svgCentralPanelFiltering.attr("id", "TopicSimilarityMetricPanelFiltering");

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

                
                
                var slider = document.getElementById('lamdaInputTopicSimilarity');
                

                if(is_first_time_sankey_diagram == true){
                    if(type_vis==2){
                        var initial_filtering_value = randomNumber(min_similarity_score, max_similarity_score);
                        if(scenario_2_is_baseline_metric==false){
                            vis_state.lambda_lambda_topic_similarity = Math.random().toFixed(2) // Omega random , chosen randomly for the user study  

                        }   

                    }

                }

                if(scenario_2_is_baseline_metric == false){
                    var range_slider = noUiSlider.create(slider, {
                        //start: [(max_similarity_score)*0.65, max_similarity_score],
                        start: [initial_filtering_value, max_similarity_score],                    
                        connect: true,
                        range: {
                            'min': min_similarity_score,
                            'max': max_similarity_score
                        }
                    });
                    var origins = slider.getElementsByClassName('noUi-origin');
                    if (origins[1]) { origins[1].setAttribute('disabled', true); }
                    if (origins[1]) { origins[1].setAttribute('class', 'disabled_slider'); }

                }
                else{
                    var range_slider = noUiSlider.create(slider, {
                        //start: [(max_similarity_score)*0.65, max_similarity_score],
                        start: [initial_filtering_value, max_similarity_score],                    
                        connect: true,
                        range: {
                            'min': min_similarity_score,
                            'max': max_similarity_score
                        }
                    });
                    var origins2 = slider.getElementsByClassName('noUi-origin');
                    if (origins2[1]) { origins2[1].setAttribute('disabled', true); }
                    if (origins2[1]) { origins2[1].setAttribute('class', 'disabled_slider'); }

                    //origins[1].setAttribute('disabled', true);

                }

                //disable right handle of the slider                    
                //read values from slider slider-value-lower
                
                var lambdaLabelTopicSimilarity = document.createElement("label");
                lambdaLabelTopicSimilarity.setAttribute("id", "LabelFilteringTopicSimilarity");
                lambdaLabelTopicSimilarity.setAttribute("class", "ColumnDiv");
                lambdaLabelTopicSimilarity.setAttribute("for", "lambdaInputTopicSimilarityFiltering");
                lambdaLabelTopicSimilarity.innerHTML = "Filtering = [<span id='slider-value-lower'></span> - <span id='slider-value-upper'>]";
                sliderDivFiltering.appendChild(lambdaLabelTopicSimilarity);

                

                slider.noUiSlider.on('update', function (values, handle) {
                    

    
                    //por ahora, values[1] siempre sera el maximo score, vamos a desabilitar ese handle a mano
                    
                    document.getElementById("LabelFilteringTopicSimilarity").innerHTML = "Filtering = [<span id='slider-value-lower'>"+values[0]+"</span>, <span id='slider-value-upper'>"+values[1]+"</span>]";
                    
                    if(scenario_2_is_baseline_metric==false){
                        vis_state.max_value_filtering = 1.0;
                        vis_state.min_value_filtering = Number(values[0]);


                    }
                    else{
                    vis_state.max_value_filtering = Number(max_similarity_score);
                    vis_state.min_value_filtering = Number(values[0]);                
                    }
                    //Do not change max_value:


                    if(scenario_2_is_baseline_metric == false){
                        visualize_sankey(matrix_sankey[get_new_omega(lambda_lambda_topic_similarity.current)], vis_state.min_value_filtering, vis_state.max_value_filtering)

                    }else
                    {
                        visualize_sankey(matrix_sankey[get_new_omega(lambda_lambda_topic_similarity.current)], vis_state.min_value_filtering, vis_state.max_value_filtering)
                    }


        
                });


                
                var scaleContainerTopicSimilarityFiltering = tveD3SelectById("sliderDivInputFilteringTopicSimilarity", "init_forms filtering slider scale").append("svg")
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
            lambdaInputLambdaTopicSimilarity.value = lambda_lambda_topic_similarity.current;
            lambdaInputLambdaTopicSimilarity.id = "lambdaInputLambdaTopicSimilarity";
            lambdaInputLambdaTopicSimilarity.setAttribute("list", "ticks"); // to enable automatic ticks (with no labels, see below)
            sliderDivInputOmegaTopicSimilarity.appendChild(lambdaInputLambdaTopicSimilarity);

            var lambdaLabelLambdaTopicSimilarity = document.createElement("label");
            lambdaLabelLambdaTopicSimilarity.setAttribute("id", "LambdaLabelLambdaTopicSimilarity");
            lambdaLabelLambdaTopicSimilarity.setAttribute("class", "ColumnDiv");
            lambdaLabelLambdaTopicSimilarity.setAttribute("for", "lambdaInputLambdaTopicSimilarity");
            lambdaLabelLambdaTopicSimilarity.innerHTML = "Omega score: &#937; = <span id=\"lambdaInputLambdaTopicSimilarity-value\"></span>";
            sliderDivLambdaTopicSimilarity.appendChild(lambdaLabelLambdaTopicSimilarity);
            var _omegaValEl = document.getElementById("lambdaInputLambdaTopicSimilarity-value");
            if (_omegaValEl) {
                _omegaValEl.textContent = String(vis_state.lambda_lambda_topic_similarity);
            }


            // Create the svg to contain the slider scale:
            var scaleContainerOmegaTopicSimilarity = tveD3SelectById(sliderDivID + "OmegaTopicSimilarity", "init_forms OmegaTopicSimilarity scale").append("svg")
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
    


            (function tveBindOmegaTopicSimilaritySlider() {
                var _omegaDebounce = null;
                function _tveOmegaLabelOnly() {
                    var inp = document.getElementById("lambdaInputLambdaTopicSimilarity");
                    var v = inp ? inp.value : "";
                    var el = document.getElementById("lambdaInputLambdaTopicSimilarity-value");
                    if (el) { el.textContent = v; }
                }
                function _tveApplyOmegaReplot() {
                    lambda_lambda_topic_similarity.old = lambda_lambda_topic_similarity.current;
                    lambda_lambda_topic_similarity.current = document.getElementById("lambdaInputLambdaTopicSimilarity").value;
                    vis_state.lambda_lambda_topic_similarity = lambda_lambda_topic_similarity.current;
                    _tveOmegaLabelOnly();
                    if (typeof window !== "undefined" && window.__tveDebug) {
                        var _key = get_new_omega(lambda_lambda_topic_similarity.current);
                        var _pos0 = (typeof new_circle_positions !== "undefined" && new_circle_positions && new_circle_positions[_key]) ? new_circle_positions[_key][0] : null;
                        console.log("[tve omega]", { current: lambda_lambda_topic_similarity.current, lookup_key: _key, first_point: _pos0 });
                    }
                    if(type_vis == 2){
                        visualize_sankey(matrix_sankey[get_new_omega(lambda_lambda_topic_similarity.current)], vis_state.min_value_filtering, vis_state.max_value_filtering);
                    }
                    if(type_vis == 1){
                        createMdsPlot(1, mdsData, get_new_omega(lambda_lambda_topic_similarity.current));
                        topic_on(document.getElementById(topicID+vis_state.topic));
                    }
                }
                // Range inputs: "mouseup" alone misses drags. Use "input" (live) + "change" (commit).
                d3.select("#lambdaInputLambdaTopicSimilarity")
                    .on("input", function() {
                        var v = document.getElementById("lambdaInputLambdaTopicSimilarity").value;
                        vis_state.lambda_lambda_topic_similarity = v;
                        _tveOmegaLabelOnly();
                        clearTimeout(_omegaDebounce);
                        _omegaDebounce = setTimeout(_tveApplyOmegaReplot, 85);
                    })
                    .on("change", function() {
                        clearTimeout(_omegaDebounce);
                        _tveApplyOmegaReplot();
                    });
            })();

            d3.select("#lambdaInputTopicSimilarityFiltering") //Filtering paths of sankey diagram
            .on("mouseup", function() {

                // store the previous lambda value
                lambda_topic_similarity.old = lambda_topic_similarity.current;
                
                lambda_topic_similarity.current = document.getElementById("lambdaInputTopicSimilarityFiltering").value;
                
                
                vis_state.lambda_topic_similarity =lambda_topic_similarity.current

                
                
                document.getElementById("lambdaInputTopicSimilarityFiltering-value").innerHTML = " <span id='lambdaInputTopicSimilarityFiltering-value'>" + Math.round( vis_state.lambda_topic_similarity * 100) / 100 + "</span>";

                document.getElementById("lambdaInputTopicSimilarityFiltering").value = vis_state.lambda_topic_similarity;
                //creo que este es el omega??
                
                visualize_sankey(matrix_sankey[get_new_omega(lambda_lambda_topic_similarity.current)], vis_state.min_value_filtering, vis_state.max_value_filtering)
                
            });






        }

        // function to re-order the bars (gray and red), and terms:

        function reorder_bars_helper(to_select, increase, topic_id_in_model, barFreqsID_actual, bar_totals_actual, terms_actual, overlay, xaxis_class){
            var _lamDataLocal = lamData;
            var _relLambda = vis_state.lambda;
            if (type_vis === 2) {
                if (barFreqsID_actual === "barplot_2") {
                    _lamDataLocal = [];
                    for (var j = 0; j < jsonData_2['tinfo'].Term.length; j++) {
                        var row = {};
                        for (var _k in jsonData_2['tinfo']) {
                            row[_k] = jsonData_2['tinfo'][_k][j];
                        }
                        _lamDataLocal.push(row);
                    }
                    _relLambda = vis_state.lambda_b;
                } else {
                    _lamDataLocal = [];
                    for (var j2 = 0; j2 < jsonData['tinfo'].Term.length; j2++) {
                        var row2 = {};
                        for (var k2 in jsonData['tinfo']) {
                            row2[k2] = jsonData['tinfo'][k2][j2];
                        }
                        _lamDataLocal.push(row2);
                    }
                    _relLambda = vis_state.lambda;
                }
            }
            var dat2 = _lamDataLocal.filter(function(d) {
                return d.Category == "Topic" + topic_id_in_model;
            });
            for (var i = 0; i < dat2.length; i++) {
                dat2[i].relevance = _relLambda * dat2[i].logprob +
                    (1 - _relLambda) * dat2[i].loglift;
                if (isNaN(dat2[i].relevance)) {
                    dat2[i].relevance = -Infinity;
                }
            }
            dat2.sort(fancysort("relevance"));
            var _capR = (type_vis === 2) ? sankeyTermActiveCap : R;
            var bLre;
            var bRre;
            if (type_vis === 2) {
                bLre = (typeof topic_id_model_1 === "number" && topic_id_model_1 >= 0) ?
                    { node: topic_id_model_1 } : real_last_clicked_sankey_model_1;
                bRre = (typeof topic_id_model_2 === "number" && topic_id_model_2 >= 0) ?
                    { node: topic_id_model_2 + min_target_node_value } : real_last_clicked_sankey_model_2;
                _capR = tvePairedNFromTwoBoxes(bLre, bRre, min_target_node_value);
            }
            var dat3 = dat2.slice(0, _capR);
            var _barH = tveBarheightFor(barFreqsID_actual);
            if (type_vis === 2) {
                tveLogBars("reorder_bars_helper", {
                    chart: barFreqsID_actual,
                    topicIdInModel: topic_id_in_model,
                    _capR: _capR,
                    dat2AfterSortLen: dat2.length,
                    dat3SliceLen: dat3.length,
                    bLeftNode: bLre && bLre.node,
                    bRightNode: bRre && bRre.node,
                    barH: _barH,
                    barheightGlobal: barheight
                });
            }
            
            var y = d3.scaleBand()
                    .domain(dat3.map(function(d) {
                        return d.Term;
                    }))
                    .rangeRound([0, _barH])
                    .padding(0.15);
            
            var x = d3.scaleLinear()
                    .domain([1, d3.max(dat3, function(d) {
                        return d.Total;
                    })])
                    .range([0, barwidth])
                    .nice();

            // Change Total Frequency bars
            // `select("#" + id).selectAll("#… #…")` can match 0 under the chart <g> (wrong scope).
            // Select direct descendants by class under the same chart g as topic_on_sankey.
            var graybars = d3.select("#" + barFreqsID_actual)
                    .selectAll("rect." + bar_totals_actual)
                    .data(dat3, function(d) {
                        return d.Term;
                    });

            // Change word labels
            var labels = d3.select("#" + barFreqsID_actual)
                    .selectAll("text." + terms_actual)
                    .data(dat3, function(d) {
                        return d.Term;
                    });

            // Create red bars (drawn over the gray ones) to signify the frequency under the selected topic
            var redbars = d3.select("#" + barFreqsID_actual)
                    .selectAll("rect." + overlay)
                    .data(dat3, function(d) {
                        return d.Term;
                    });

            // adapted from http://bl.ocks.org/mbostock/1166403

            var xAxis = d3.axisTop(x).tickSize(-_barH).ticks(6);
            
            // New axis definition:
            var newaxis = d3.selectAll(to_select + " ."+xaxis_class);

            // define the new elements to enter:
            var graybarsEnter = graybars.enter().append("rect")
                    .attr("class", bar_totals_actual)
                    .attr("x", 0)
                    .attr("y", function(d) {
                        return y(d.Term) + _barH + margin.bottom + 2 * rMax;
                    })
                    .attr('id', function(d){
                        return bar_totals_actual+'-'+d.Term;
                    })
                    .attr("height", y.bandwidth()/2)
                    .style("fill", color1_1)
                    .attr("opacity", 0.4);

            var labelsEnter = labels.enter()
                    .append("text")
                    .attr("x", -5)
                    .attr("class", terms_actual)
                    .attr("y", function(d) {
                        return y(d.Term) + 9 + _barH + margin.bottom + 2 * rMax;
                    })
                    .style("text-anchor", "end")
                    .attr("id", function(d) {
                        return (termID + d.Term);
                    })
                    .text(function(d) {
                        return d.Term;
                    })
                    .on("mouseover", function() {
                        var current_term = this.id.split('-')[1];
                        d3.selectAll('#barplotterm-'+current_term).style("font-weight",'bolder');
                        if(type_vis==1){
                            d3.select('#bar-totals-'+current_term).style("fill",color1_2);
                            d3.select('#bar-freq-estimated-'+current_term).style("fill",color2_2);
                        }
                        else{
                            d3.select('#bar-totals-'+current_term).style("fill",color1_2);
                            d3.select('#overlay-'+current_term).style("fill",color2_2);

                            d3.select('#bar-totals_2-'+current_term).style("fill",color1_2);
                            d3.select('#overlay_2-'+current_term).style("fill",color2_2);
                        }                                            
                    })
            
                    .on("mouseout", function() {
                        var current_term = this.id.split('-')[1];

                        d3.selectAll('#barplotterm-'+current_term).style("font-weight",'normal');
                        if(type_vis==1){
                            d3.select('#bar-freq-estimated-'+current_term).style("fill",color2_1);
                            d3.select('#bar-totals-'+current_term).style("fill",color1_1);
                        }
                        else{
                            d3.select('#bar-totals-'+current_term).style("fill",color1_1);
                            d3.select('#overlay-'+current_term).style("fill",color2_1);
    
                            d3.select('#bar-totals_2-'+current_term).style("fill",color1_1);
                            d3.select('#overlay_2-'+current_term).style("fill",color2_1);
                        }                    

                    });

            var redbarsEnter = redbars.enter().append("rect")
                    .attr("class", overlay)
                    .attr("x", 0)
                    .attr("y", function(d) {
                        return  (y.bandwidth()/2)+ y(d.Term) + _barH + margin.bottom + 2 * rMax;
                    }) 
                    .attr('id', function(d){
                        return 'bar-freq-estimated-'+d.Term;
                    })
                    .attr("height", y.bandwidth()/2)
                    .style("fill", color2_1)
                    .attr("opacity", 0.8);


            if (increase) {
                graybarsEnter
                    .attr("width", function(d) {
                        return Math.max(0, x(d.Total));
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
                        return y(d.Term) + 9;
                    });
                redbarsEnter
                    .attr("width", function(d) {
                        return Math.max(0, x(d.Freq));
                    })
                    .transition().duration(duration)
                    .delay(duration)
                    .attr("y", function(d) {
                        return (y.bandwidth()/2)+y(d.Term);
                    });

                graybars.transition().duration(duration)
                    .attr("width", function(d) {
                        return Math.max(0, x(d.Total));
                    })
                    .transition().duration(duration)
                    .attr("y", function(d) {
                        return y(d.Term);
                    });
                labels.transition().duration(duration)
                    .delay(duration)
                    .attr("y", function(d) {
                        return y(d.Term) + 9;
                    });
                redbars.transition().duration(duration)
                    .attr("width", function(d) {
                        return Math.max(0, x(d.Freq));
                    })
                    .transition().duration(duration)
                    .attr("y", function(d) {
                        return (y.bandwidth()/2) + y(d.Term);
                    });

                // Transition exiting rectangles to the bottom of the barchart:
                graybars.exit()
                    .transition().duration(duration)
                    .attr("width", function(d) {
                        return Math.max(0, x(d.Total));
                    })
                    .transition().duration(duration)
                    .attr("y", function(d, i) {
                        return _barH + margin.bottom + 6 + i * 18;
                    })
                    .remove();
                labels.exit()
                    .transition().duration(duration)
                    .delay(duration)
                    .attr("y", function(d, i) {
                        return _barH + margin.bottom + 18 + i * 18;
                    })
                    .remove();
                redbars.exit()
                    .transition().duration(duration)
                    .attr("width", function(d) {
                        return Math.max(0, x(d.Freq));
                    })
                    .transition().duration(duration)
                    .attr("y", function(d, i) {
                        return _barH + margin.bottom + 6 + i * 18;
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
                        return Math.max(0, x(d.Total));
                    });
                labelsEnter
                    .transition().duration(duration)
                    .attr("y", function(d) {
                        return y(d.Term) + 9;
                    });
                redbarsEnter
                    .attr("width", 50) // FIXME by looking up old width of these bars
                    .transition().duration(duration)
                    .attr("y", function(d) {
                        return (y.bandwidth()/2)+y(d.Term);
                    })
                    .transition().duration(duration)
                    .attr("width", function(d) {
                        return Math.max(0, x(d.Freq));
                    });

                graybars.transition().duration(duration)
                    .attr("y", function(d) {
                        return y(d.Term);
                    })
                    .transition().duration(duration)
                    .attr("width", function(d) {
                        return Math.max(0, x(d.Total));
                    });
                labels.transition().duration(duration)
                    .attr("y", function(d) {
                        return y(d.Term) + 9;
                    });
                redbars.transition().duration(duration)
                    .attr("y", function(d) {
                        return  (y.bandwidth()/2)+y(d.Term);
                    })
                    .transition().duration(duration)
                    .attr("width", function(d) {
                        return Math.max(0, x(d.Freq));
                    });

                // Transition exiting rectangles to the bottom of the barchart:
                graybars.exit()
                    .transition().duration(duration)
                    .attr("y", function(d, i) {
                        return _barH + margin.bottom + 6 + i * 18 + 2 * rMax;
                    })
                    .remove();
                labels.exit()
                    .transition().duration(duration)
                    .attr("y", function(d, i) {
                        return _barH + margin.bottom + 18 + i * 18 + 2 * rMax;
                    })
                    .remove();
                redbars.exit()
                    .transition().duration(duration)
                    .attr("y", function(d, i) {
                        return _barH + margin.bottom + 6 + i * 18 + 2 * rMax;
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




        /**
         * Sorted relevance list for a Sankey node (no global lamData mutation).
         * Used to pair how many terms we show for corpus A vs B.
         */
        function tveGetSankeyNodeTerms(box, mtv) {
            if (box == null || box.node === undefined) { return []; }
            var _lam = [];
            var _j = (box.node >= mtv) ? jsonData_2 : jsonData;
            for (var i = 0; i < _j['tinfo'].Term.length; i++) {
                var obj = {};
                for (var key in _j['tinfo']) {
                    obj[key] = _j['tinfo'][key][i];
                }
                _lam.push(obj);
            }
            var _ex;
            if (box.node < 0) {
                _ex = "Default";
            } else if (box.node >= mtv) {
                _ex = "Topic" + (box.node - mtv + 1);
            } else {
                _ex = "Topic" + (box.node + 1);
            }
            var d2 = _lam.filter(function(d) {
                if (box.node < 0) { return d.Category == "Default"; }
                return d.Category == _ex;
            });
            var lSort = (box.node >= mtv) ? lambda_b.current : lambda.current;
            for (var j = 0; j < d2.length; j++) {
                d2[j].relevance = lSort * d2[j].logprob + (1 - lSort) * d2[j].loglift;
                if (isNaN(d2[j].relevance)) { d2[j].relevance = -Infinity; }
            }
            d2.sort(fancysort("relevance"));
            return d2;
        }
        function tvePairedNFromTwoBoxes(b1, b2, mtv) {
            if (type_vis !== 2) { return sankeyTermActiveCap; }
            if (!b1 || !b2) { return sankeyTermActiveCap; }
            var a = tveGetSankeyNodeTerms(b1, mtv);
            var b = tveGetSankeyNodeTerms(b2, mtv);
            var _pairN = Math.min(sankeyTermActiveCap, a.length, b.length);
            tveLogBars("tvePairedNFromTwoBoxes", {
                cap: sankeyTermActiveCap,
                leftTermsLen: a.length,
                rightTermsLen: b.length,
                nodeLeft: b1 && b1.node,
                nodeRight: b2 && b2.node,
                pairN: _pairN
            });
            return _pairN;
        }

        // function to update bar chart when a topic is selected
        // the circle argument should be the appropriate circle element
        // optPairN: when set, both sides use min(cap, n1, n2) from paired refresh
        // skipCrossPlaceholder: true for paired calls so the two "Select a topic" hints do not fight
        function topic_on_sankey(box, min_target_node_value, optPairN, skipCrossPlaceholder ){
            if (skipCrossPlaceholder == null) { skipCrossPlaceholder = false; }
            if(box.node>=min_target_node_value){
                //pertenece al modelo de corpus 2
                to_select = "#BarPlotPanel_2"
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
                    d3.select("#"+last_clicked_model_2).style("fill",color_topic_2_1)
                }

                
                last_clicked_model_2 = "node_"+box.node
                d3.select("#"+last_clicked_model_2).style("fill",color_topic_2_2) //color2_2
                //d3.select("#"+last_clicked_model_2).style("opacity", 1.0)
                document.getElementById("renameTopicId2").value = name_topics_sankey[topicID + box.node] 
                $('#idTopic2').html(topicID + box.node); 
                $('#topic_name_selected_2').html(name_topics_sankey[topicID + box.node] );
                if (!skipCrossPlaceholder) {
                $('#topic_name_selected_1').html("Select a topic on the left (corpus A) in the Sankey.");
                }

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
                    d3.select("#"+last_clicked_model_1).style("fill",color_topic_1_1)
                }

                last_clicked_model_1 = "node_"+box.node
                d3.select("#"+last_clicked_model_1).style("fill",color_topic_1_2)
                //cual es el d al que le estoy haciendo click??


                
                
                document.getElementById("renameTopicId").value = name_topics_sankey[topicID + box.node] 
                $('#idTopic').html(topicID + box.node);
                $('#topic_name_selected_1').html(name_topics_sankey[topicID + box.node]);
                if (!skipCrossPlaceholder) {
                $('#topic_name_selected_2').html("Select a topic on the right (corpus B) in the Sankey.");
                }
                
            }

            vis_state.topic = box.node
            splitting_topic = vis_state.topic

            Freq = Math.round(Freq * 10) / 10  


            var text = d3.select(to_select + " ."+bubble_tool);
            text.remove();

            
            
            
            var _expectedCat2;
            if (box.node < 0) {
                _expectedCat2 = "Default";
            } else if (box.node >= min_target_node_value) {
                _expectedCat2 = "Topic" + (box.node - min_target_node_value + 1);
            } else {
                _expectedCat2 = "Topic" + (box.node + 1);
            }
            var dat2 = lamData.filter(function(d) {
                if (box.node < 0) {
                    return d.Category == "Default";
                }
                return d.Category == _expectedCat2;
            });
            var lSort = (box.node >= min_target_node_value) ? lambda_b.current : lambda.current;
            for (var i = 0; i < dat2.length; i++) {
                dat2[i].relevance = lSort * dat2[i].logprob +
                    (1 - lSort) * dat2[i].loglift;
                if (isNaN(dat2[i].relevance)) {
                    dat2[i].relevance = -Infinity;
                }
            }


            dat2.sort(fancysort("relevance"));
            // truncate: paired multicorpora use optPairN = min(cap, nLeft, nRight)
            var nTake = (typeof optPairN === "number" && !isNaN(optPairN)) ?
                Math.min(optPairN, dat2.length) : sankeyTermActiveCap;
            var dat3 = dat2.slice(0, nTake);
            var _barH = tveBarheightFor(barFreqsID_actual);
            if (type_vis === 2) {
                tveLogBars("topic_on_sankey", {
                    side: (box.node >= min_target_node_value) ? "right" : "left",
                    sankeyNode: box.node,
                    barChart: barFreqsID_actual,
                    optPairN: optPairN,
                    sankeyTermActiveCap: sankeyTermActiveCap,
                    dat2FilteredLen: dat2.length,
                    nTake: nTake,
                    dat3SliceLen: dat3.length,
                    barH: _barH,
                    barheightGlobal: barheight
                });
            }

            //AddBackgroundColorToText(dat3)

            // scale the bars to the top R terms:
            var y = d3.scaleBand()
                    .domain(dat3.map(function(d) {
                        return d.Term;
                    }))
                    .rangeRound([0, _barH])
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

            var _tKeySankey = function(d) { return d.Term; };
            var _br = d3.select("#" + barFreqsID_actual);
            // Keyed join + exit: when pairN shrinks, stale bar/label DOM must be removed
            var _gray = _br.selectAll("rect." + bar_totals_actual).data(dat3, _tKeySankey);
            _gray.exit().remove();
            _gray = _gray.enter().append("rect").attr("class", bar_totals_actual).merge(_gray);
            _gray.attr("x", 0)
                .attr("y", function(d) {
                    return y(d.Term);
                })
                .attr('id', function(d){
                    return bar_totals_actual+'-'+d.Term;
                })
                .attr("height", y.bandwidth()/2)
                .attr("width", function(d) {
                    return Math.max(0, x(d.Total));
                })
                .style("fill", color1_1)
                .attr("opacity", 0.4);

            var _wlab = _br.selectAll("text." + terms_actual).data(dat3, _tKeySankey);
            _wlab.exit().remove();
            _wlab = _wlab.enter().append("text").attr("class", terms_actual).merge(_wlab);
            _wlab.attr("x", -5)
                .attr("y", function(d) {
                    return y(d.Term) + 9;
                })
                .attr("id", function(d) {
                    return (termID + d.Term);
                })
                .style("text-anchor", "end") // right align text - use 'middle' for center alignment
                .text(function(d) {
                    return d.Term;
                });

            var _ovl = _br.selectAll("rect." + overlay).data(dat3, _tKeySankey);
            _ovl.exit().remove();
            _ovl = _ovl.enter().append("rect").attr("class", overlay).merge(_ovl);
            _ovl.attr("x", 0)
                .attr("y", function(d) {
                    return y.bandwidth()/2 + y(d.Term);
                })
                .attr('id', function(d){
                    return overlay+'-'+d.Term;
                })
                .attr("height", y.bandwidth()/2)
                .attr("width", function(d) {
                    return Math.max(0, x(d.Freq));
                })
                .style("fill", color2_1)
                .attr("opacity", 0.8);

            // adapted from http://bl.ocks.org/mbostock/1166403

            var xAxis = d3.axisTop(x).tickSize(-_barH).ticks(6);

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
        function show_tutorial(){
            //elements of tutorial. Thus we dont need to write it everytime again and again
            function fix_tutorial_identification_elements(id_element, json){
                json["element"] = document.querySelector(id_element)
                return json
            }
            //element: document.querySelector('#svgMdsPlot'),
            var tutorial_steps = {}
            //take into consideration this tutorial
            //https://monkeylearn.com/blog/introduction-to-topic-modeling/#:~:text=Topic%20modeling%20is%20a%20machine,been%20previously%20classified%20by%20humans.
            
        
            tutorial_steps['start_tutorial'] = {title: 'Welcome!', intro: 'This tutorial will guide you in the usage of this interface.'};
            tutorial_steps['topic_modeling_definition'] = {title: 'What is topic modeling?', intro: '<div id="topic_modeling_definition"> It is an unsupervised machine learning technique capable of discovering <b style="color: #1f77b4;"> topics </b> in a collection of documents.' };
            tutorial_steps['topic_flight_cancelled'] = { intro: 'In this tool, a circle represents one of the topics found by the topic modeling algorithm.' ,    position: 'top' };
            tutorial_steps['most_relevant_keywords'] = {  title: 'Most relevant keywords', intro: "After selecting a topic, you will see its most relevant keywords. <br> <br>  These terms are automatically sorted according to the relevance to the topic (e.g., <i style='color: #1f77b4;'>'flight' </i> , <i style='color: #1f77b4;'>'cancel' </i>, <i style='color: #1f77b4;'>'delay' </i>)", position: 'right' };
            tutorial_steps['most_relevant_keywords_singlecorpus_dataset'] = {  title: 'Most relevant keywords', intro: "After selecting a topic, you will see its most relevant keywords. <br> <br>  These terms are automatically sorted according to the relevance to the topic.", position: 'right' };
            tutorial_steps['relevance_slider_most_relevant_keywords'] = {  title: 'Changing the ordering of the most relevant keywords', intro: "When topics are difficult to identify, it is better to explore different ordering of the keywords. To do so, you can change the  <i style='color: #1f77b4;'>relevance score </i> using this slider. <br> <br> A higher <i style='color: #1f77b4;'>relevance score </i> designates greater importance to the frequency of terms within the selected topic (green bar). But at the same time, it reduces the importance of their exclusivity, in other words, how rare these words are on other topics.", position: 'right' };
            tutorial_steps['documents_panel_scenario_1'] = { element: document.querySelector('#DocumentsPanel_first_scenario'), title: 'Most relevant documents', intro: "Here, you can see the most relevant documents associated with the selected topic. Documents more related to the chosen topic will have a higher contribution (%) to it." , position: 'left'};
            tutorial_steps['topic_flight_cancelled_interpretation'] = {  title: 'What is the selected topic about?', intro: "After reading its most relevant keywords (e.g, <i style='color: #1f77b4;'>'flight' </i> , <i style='color: #1f77b4;'>'cancel' </i>, <i style='color: #1f77b4;'>'delay' </i> , <i style='color: #1f77b4;'>'miss' </i>, etc) and its most relevant documents such as: <i style='color: #1f77b4;'> '<usernameremoved> 2 canceled flights later, agent claimed she put me on a new flight but then canceled it. coworker got on flight- now delayed. now?' </i> you may identify that the topic is about: <b style='color: #1f77b4'> 'airlines cancelling flights' </b>."};
            tutorial_steps['topic_interpretation'] = {  title: 'What is the selected topic about?', intro: "To identify the topic's meaning, you must read its most relevant keywords and its most relevant documents."};
            tutorial_steps['topic_flight_cancelled_rename_button'] = {  intro: "Now that you have a name in mind for this topic (<b style='color: #1f77b4'> 'airlines cancelling flights' </b>), you can rename it by clicking this button.", position:"left"};
            tutorial_steps['rename_button'] = {  intro: "After identifying the topic's meaning, you have to assign a better name to it by clicking this button. <br> <br> Initially, all the topics have as name their three most relevant keywords. <b> You have to change these names. </b>", position:"left"};
            tutorial_steps['scenario_1_global_view_of_topics'] = { title: 'Global view of topics', element: document.querySelector('#CentralPanel'), intro: "The central panel presents a global view of the topics found by the topic modeling algorithm. <br> <br> Here you can select other topics too." };                
            tutorial_steps['scenario_1_topic_frequency'] = { title: 'How prevalent each topic is?', intro: "The area of the circle indicates the frequency (%) of the topic in the dataset. <br> <br> In this case, all the topics have the same frequency (16%)" };
            tutorial_steps['omega_description'] = { element: document.querySelector('#TopicSimilarityMetricPanel'), title: 'Similarity between topics', intro: "This slider allows adjusting the similarity between topics. A higher omega score implies higher importance to the most relevant keywords, but a lower significance to the most relevant documents in the topic similarity calculation." };
            tutorial_steps['description_omega_slider'] = {title: 'Similarity between topics', intro: "The similarity between topics is calculated automatically. You can explore other results using this slider. <br> <br> The algorithm compares topics considering their most relevant documents and their most relevant keywords. <br> <br> During the  calculation of the similarity between two topics,  a higher <i style='color: #1f77b4;'>omega  score </i>implies higher importance to their  most relevant documents, but a lower significance to their most relevant keywords." };
            tutorial_steps['scenario_1_hil_buttons'] = { title: 'Modifying topic modeling results', intro: "After inspecting the topics, you may wish to join two similar topics into one (<b style='color: #1f77b4'> merge</b>) or to split a generic topic into two new subtopics  (<b style='color: #1f77b4'> split</b>). You can access these functionalities here."};
            tutorial_steps['scenario_1_reverse_button'] = { title: 'Modifying topic modeling results', intro: "If the results after applying a (<b style='color: #1f77b4'> topic merging </b>) or (<b style='color: #1f77b4'> topic splitting </b>) operation are not satisfactory, you can reverse the changes by clicking this button."};

            tutorial_steps['export_topics_json'] = { element: document.querySelector('#export_topics_button'), title: 'Export topics', intro: "Download a JSON file with the current topic labels, top terms, and layout. Nothing is uploaded to a server; the file is saved only on your computer." };
            tutorial_steps['help_button'] = { element: document.querySelector('#help_button'), title: 'Ask for help!', intro: "Finally, don't forget that you can always start the interactive tutorial here!" };



            //tutorial_steps['introduction_to_topic_modeling'] ={title: 'What is topic modeling?', intro: "Topic modeling is a technique that automatically analyzes text data to determine cluster words for a set of documents"}
        
            tutorial_steps['scenario_2_explanation'] = {title: 'Comparing datasets', intro: 'This visualization allows to  <b style="color: #1f77b4;"> identify </b>  and <b style="color: #1f77b4;"> compare  </b> topics from two different datasets' };
            tutorial_steps['scenario_2_box_explanation'] = { intro: 'Each topic found by the topic modeling algorithm is represented by a box.  <br><br> <b style="color: #1f77b4;">  All the topics from the same dataset have the same color </b> ' ,    position: 'top' };
            tutorial_steps['scenario_2_left_column_explanation'] = { intro: 'After selecting a topic on the left column on the central panel (lightblue box), you will see here all the information associated with that topic, such as its most relevant keywords and its most relevant documents.' ,    position: 'right' };
            tutorial_steps['scenario_2_box_second_dataset_explanation'] = { intro: 'Each topic of the second dataset appears with a pink color' ,    position: 'top' };
            tutorial_steps['scenario_2_right_column_explanation'] = { intro: 'Here you can see the information related to a topic of the second dataset (pink box)' ,    position: 'left' };
            //tutorial_steps['scenario_2_global_view_of_topics'] = {title: 'Global view of topics', element: document.querySelector('#CentralPanel'), intro: "The central panel presents a global view of the topics and aims to answer <b style='color: #1f77b4;'>How topics relate to each other? </b>" };
            tutorial_steps['explanation_of_sankey_diagram'] = { element: document.querySelector('#svg_sankey'), title: 'How  topics relate to each other? ', intro: "This interface allows identifying the similarity between topics from two different datasets. <br> <br> The similarity score between two topics is automatically calculated <br><br> The link between topics indicates their similarity. Topics that are more similar are connected with a <b style='color: #1f77b4;'>wider </b> link and they have a higher similarity score." };

            tutorial_steps['explanation_filtering_sankey'] = {  title: 'Filtering links', intro: "You can see more or fewer links in the visualization modifying this slider.", position: 'right' };
            tutorial_steps['explanation_filtering_sankey_part2'] = { title: 'Filtering links', intro: "The interface will only show links that have a similarity score in this range of values.", position: 'left' };
            tutorial_steps['rename_button_scenario_2_left'] = {  intro: "This button allows you to change the name of a topic of the first dataset (lightblue box).  <br> <br>  The topics' default name corresponds to their three most relevant keywords.", position:"right"};
            tutorial_steps['rename_button_scenario_2_right'] = {  intro: "Here you can assign a name to a topic of the second dataset (pink box)", position:"left"};

            

            //without element attribute
            
            tutorial_steps['scenario_1_topic_similarity'] = { title: 'How do topics relate to each other? ', intro: "Similar topics appear closer, while distinct topics appear more distant between each other" };
            tutorial_steps['only_rename_topic_button'] = {  title: 'Rename topics', intro: "You can use this button to rename a topic" };
            
            //tutorial_steps['scenario_2_explanation_of_datasets'] = {element: document.querySelector('#svg_sankey'), title: 'How topics relate to each other?', intro: "Each topic is represented as a box. Its color indicates to which dataset the topic belongs."};
        
            
        
            if(type_vis==1){
                if(is_human_in_the_loop == true){ // users can use topic splitting/ topic merging
                    if(is_tutorial == true){
                        topic_off(document.getElementById(topicID+'1'));
                        topic_on(document.getElementById(topicID+'5'));
                        first_time_clicking_circle = true;
                        introJs().setOptions({
                            steps: [
            
                                tutorial_steps['start_tutorial'],
                                tutorial_steps['topic_modeling_definition'],
                                fix_tutorial_identification_elements("#"+topicID+'5', tutorial_steps['topic_flight_cancelled']),                            
                                fix_tutorial_identification_elements("#barplot_1", tutorial_steps['most_relevant_keywords']),
                                fix_tutorial_identification_elements("#relevanceSliderDiv", tutorial_steps['relevance_slider_most_relevant_keywords']),
                                tutorial_steps['documents_panel_scenario_1'],
                                tutorial_steps['topic_flight_cancelled_interpretation'],                            
                                fix_tutorial_identification_elements('#LDAvisContainer-topic-edit', tutorial_steps['topic_flight_cancelled_rename_button']),
                                tutorial_steps['scenario_1_global_view_of_topics'],
                                fix_tutorial_identification_elements("#svgMdsPlot", tutorial_steps['scenario_1_topic_frequency']),
                                fix_tutorial_identification_elements("#svgMdsPlot", tutorial_steps['scenario_1_topic_similarity']),
    
                                fix_tutorial_identification_elements("#TopicSimilarityMetricPanel", tutorial_steps['description_omega_slider']),  
                                fix_tutorial_identification_elements("#topic_buttons_div_left_full_row", tutorial_steps['scenario_1_hil_buttons']),                                                                                                                                                      
                                fix_tutorial_identification_elements("#LDAvisContainer-topic-reverse", tutorial_steps['scenario_1_reverse_button']),                                                            

                                tutorial_steps['export_topics_json'],
                                tutorial_steps['help_button']        
                        ]
                        })
                        .oncomplete(function() {

                        })
                        .onbeforeexit(function () {
                            return confirm("Are you sure do you want to end the tutorial?");
                        })
                        .start();
                    }
                    else{ // Human in the loop - we are in single corpus and it is not a tutorial
                        introJs().setOptions({
                            steps: [            
                                tutorial_steps['start_tutorial'],
                                tutorial_steps['topic_modeling_definition'],
                                fix_tutorial_identification_elements("#"+topicID+'1', tutorial_steps['topic_flight_cancelled']),                            
                                fix_tutorial_identification_elements("#barplot_1", tutorial_steps['most_relevant_keywords_singlecorpus_dataset']),
                                fix_tutorial_identification_elements("#relevanceSliderDiv", tutorial_steps['relevance_slider_most_relevant_keywords']),
                                tutorial_steps['documents_panel_scenario_1'],
                                tutorial_steps['topic_interpretation'],
                                fix_tutorial_identification_elements('#LDAvisContainer-topic-edit', tutorial_steps['rename_button']),
                                tutorial_steps['scenario_1_global_view_of_topics'],
                                fix_tutorial_identification_elements("#svgMdsPlot", tutorial_steps['scenario_1_topic_frequency']),
                                fix_tutorial_identification_elements("#svgMdsPlot", tutorial_steps['scenario_1_topic_similarity']),
    
                                fix_tutorial_identification_elements("#TopicSimilarityMetricPanel", tutorial_steps['description_omega_slider']),                                                            
                                fix_tutorial_identification_elements("#topic_buttons_div", tutorial_steps['scenario_1_hil_buttons']),                                                                                            
                                fix_tutorial_identification_elements("#LDAvisContainer-topic-reverse", tutorial_steps['scenario_1_reverse_button']),                                                            
                                tutorial_steps['export_topics_json'],
                                tutorial_steps['help_button']        
                        ]
                        })
                        .oncomplete(function() {

                        })
                        .onbeforeexit(function () {
                            return confirm("Are you sure do you want to end the tutorial?");
                        })
                        .start();
                    }
                }

                else{ // SCENARIO 1 - NO HUMAN IN THE LOOP users cant use topic splitting and topic mergign
                    if(is_tutorial == true){
                        topic_off(document.getElementById(topicID+'1'));
                        topic_on(document.getElementById(topicID+'5'));
                        first_time_clicking_circle = true;
                        introJs().setOptions({
                            steps: [
            
                                tutorial_steps['start_tutorial'],
                                tutorial_steps['topic_modeling_definition'],
                                fix_tutorial_identification_elements("#"+topicID+'5', tutorial_steps['topic_flight_cancelled']),                            
                                fix_tutorial_identification_elements("#barplot_1", tutorial_steps['most_relevant_keywords']),
                                fix_tutorial_identification_elements("#relevanceSliderDiv", tutorial_steps['relevance_slider_most_relevant_keywords']),
                                tutorial_steps['documents_panel_scenario_1'],
                                tutorial_steps['topic_flight_cancelled_interpretation'],                            
                                fix_tutorial_identification_elements('#LDAvisContainer-topic-edit', tutorial_steps['topic_flight_cancelled_rename_button']),
                                tutorial_steps['scenario_1_global_view_of_topics'],
                                fix_tutorial_identification_elements("#svgMdsPlot", tutorial_steps['scenario_1_topic_frequency']),
                                fix_tutorial_identification_elements("#svgMdsPlot", tutorial_steps['scenario_1_topic_similarity']),
    
                                fix_tutorial_identification_elements("#TopicSimilarityMetricPanel", tutorial_steps['description_omega_slider']),                                                            
                                //tutorial_steps['scenario_1_hil_buttons'], // this is only for scenario 1 , hil
                                tutorial_steps['export_topics_json'],
                                tutorial_steps['help_button']        
                        ]
                        })
                        .oncomplete(function() {

                        })
                        .onbeforeexit(function () {
                            return confirm("Are you sure do you want to end the tutorial?");
                        })
                        .start();
                    }
                    else{ // Human in the loop - we are in single corpus and it is not a tutorial
                        introJs().setOptions({
                            steps: [            
                                tutorial_steps['start_tutorial'],
                                tutorial_steps['topic_modeling_definition'],
                                fix_tutorial_identification_elements("#"+topicID+'1', tutorial_steps['topic_flight_cancelled']),                            
                                fix_tutorial_identification_elements("#barplot_1", tutorial_steps['most_relevant_keywords_singlecorpus_dataset']),
                                fix_tutorial_identification_elements("#relevanceSliderDiv", tutorial_steps['relevance_slider_most_relevant_keywords']),
                                tutorial_steps['documents_panel_scenario_1'],
                                tutorial_steps['topic_interpretation'],
                                fix_tutorial_identification_elements('#LDAvisContainer-topic-edit', tutorial_steps['rename_button']),
                                tutorial_steps['scenario_1_global_view_of_topics'],
                                fix_tutorial_identification_elements("#svgMdsPlot", tutorial_steps['scenario_1_topic_frequency']),
                                fix_tutorial_identification_elements("#svgMdsPlot", tutorial_steps['scenario_1_topic_similarity']),
    
                                fix_tutorial_identification_elements("#TopicSimilarityMetricPanel", tutorial_steps['description_omega_slider']),                                                            
                                //tutorial_steps['scenario_1_hil_buttons'], // this is only for scenario 1 , hil
                                tutorial_steps['export_topics_json'],
                                tutorial_steps['help_button']        
                        ]
                        })
                        .oncomplete(function() {

                        })
                        .onbeforeexit(function () {
                            return confirm("Are you sure do you want to end the tutorial?");
                        })
                        .start();
                    }
                }
                
            }
            //-------------------------------------Scenario 2 --------------------------------------------------
            else{ // We are in scenario 2 - Metric proposed
                var id_node_selected_left = '#node_0';

                if(is_tutorial == true){
                    id_node_selected_left = '#node_4';
                    var tutorial_graph =  matrix_sankey[get_new_omega(lambda_lambda_topic_similarity.current)];
                    var tutorial_nodes = tutorial_graph.nodes;
                    var tutorial_topic_chosen = tutorial_nodes[4];
                    var tutorial_topic_chosen_2= tutorial_nodes[6];
                    var _ptut = tvePairedNFromTwoBoxes(tutorial_topic_chosen, tutorial_topic_chosen_2, 6);
                    real_last_clicked_sankey_model_1 = tutorial_topic_chosen;
                    real_last_clicked_sankey_model_2 = tutorial_topic_chosen_2;
                    topic_on_sankey(tutorial_topic_chosen, 6, _ptut, true);
                    topic_on_sankey(tutorial_topic_chosen_2, 6, _ptut, true);

                    isSettingInitial = false;

                }
                if(scenario_2_is_baseline_metric == false){                        
                    introJs().setOptions({
                        steps: [
                            tutorial_steps['scenario_2_explanation'],     
                            fix_tutorial_identification_elements(id_node_selected_left,tutorial_steps['scenario_2_box_explanation'] ),                                                          
                            fix_tutorial_identification_elements('#'+BarPlotPanelDivId, tutorial_steps['scenario_2_left_column_explanation']),
                            fix_tutorial_identification_elements("#node_6",tutorial_steps['scenario_2_box_second_dataset_explanation'] ),                                                          
                            fix_tutorial_identification_elements('#BarPlotPanel_2', tutorial_steps['scenario_2_right_column_explanation']),                                
                            fix_tutorial_identification_elements('#svg_sankey', tutorial_steps['explanation_of_sankey_diagram']),
                            fix_tutorial_identification_elements('#TopicSimilarityMetricPanelFiltering', tutorial_steps['explanation_filtering_sankey']),
                            fix_tutorial_identification_elements('#LabelFilteringTopicSimilarity', tutorial_steps['explanation_filtering_sankey_part2']),                                
                            fix_tutorial_identification_elements("#TopicSimilarityMetricPanel", tutorial_steps['description_omega_slider']),
                            fix_tutorial_identification_elements("#LDAvisContainer-topic-edit", tutorial_steps['rename_button_scenario_2_left']),                                                            
                            fix_tutorial_identification_elements("#LDAvisContainer-topic-edit_2", tutorial_steps['rename_button_scenario_2_right']),                                                                                                                            
                            tutorial_steps['export_topics_json'],
                            tutorial_steps['help_button']                                                                                                                                                          
                    ]
                    })
                    .oncomplete(function() {

                    })
                    .onbeforeexit(function () {
                        return confirm("Are you sure do you want to end the tutorial?");
                    })
                    .start();                                    
                }
                else{ // scenario 2, metric baseline. 
                    introJs().setOptions({
                        steps: [           
                            tutorial_steps['scenario_2_explanation'],     
                            fix_tutorial_identification_elements(id_node_selected_left,tutorial_steps['scenario_2_box_explanation'] ),                                                          
                            fix_tutorial_identification_elements('#'+BarPlotPanelDivId, tutorial_steps['scenario_2_left_column_explanation']),
                            fix_tutorial_identification_elements("#node_6",tutorial_steps['scenario_2_box_second_dataset_explanation'] ),                                                          
                            fix_tutorial_identification_elements('#BarPlotPanel_2', tutorial_steps['scenario_2_right_column_explanation']),                                
                            fix_tutorial_identification_elements('#svg_sankey', tutorial_steps['explanation_of_sankey_diagram']),
                            fix_tutorial_identification_elements('#TopicSimilarityMetricPanelFiltering', tutorial_steps['explanation_filtering_sankey']),
                            fix_tutorial_identification_elements('#LabelFilteringTopicSimilarity', tutorial_steps['explanation_filtering_sankey_part2']),                                
                            //fix_tutorial_identification_elements("#TopicSimilarityMetricPanel", tutorial_steps['description_omega_slider']),
                            fix_tutorial_identification_elements("#LDAvisContainer-topic-edit", tutorial_steps['rename_button_scenario_2_left']),                                                            
                            fix_tutorial_identification_elements("#LDAvisContainer-topic-edit_2", tutorial_steps['rename_button_scenario_2_right']),                                                                                                                            
                            tutorial_steps['export_topics_json'],
                            tutorial_steps['help_button']                                                             
                    ]
                    })
                    .oncomplete(function() {

                    })
                    .onbeforeexit(function () {
                        return confirm("Are you sure do you want to end the tutorial?");
                    })                    
                    .start();
                }                
            }
        }

        
        function topic_on(circle) {

            to_select = "#BarPlotPanelDiv"
            if (circle == null) return null;
                        
            // grab data bound to this element
            var d = circle.__data__;
            // Keep in sync with vis_state (topic_on is also called after merge/split, not only on circle click).
            splitting_topic = d.topics;
            mdswidth+margin.left+termwidth+(barwidth/2)
            // update name in visualization
            $('#topic_name_selected_1').html(name_topics_circles[topicID + d.topics]); 


            var Freq = Math.round(d.Freq * 10) / 10,
                topics = d.topics;
            // change opacity and fill of the selected circle
            circle.style.opacity = highlight_opacity;
            circle.style.fill = color_topic_1_2;

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
            var _hTopic = tveBarheightFor(barFreqsID);
            
            var y = d3.scaleBand()
                    .domain(dat3.map(function(d) {
                        return d.Term;
                    }))
                    .rangeRound([0, _hTopic])
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
                .attr('id', function(d){
                    return 'bar-totals-'+d.Term;
                })
                .attr("height", y.bandwidth()/2)
                .attr("width", function(d) {
                    return Math.max(0, x(d.Total));
                })
                .style("fill", color1_1)
                .attr("opacity", 0.4);

            // Change word labels
            d3.selectAll(to_select + " .terms")
                .data(dat3)
                .attr("x", -5)
                .attr("y", function(d) {
                    return y(d.Term) + 9; //to center bars
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
                .attr('id', function(d){
                    return 'bar-freq-estimated-'+d.Term;
                })
                .attr("y", function(d) {
                    return (y.bandwidth()/2)+y(d.Term);
                })
                .attr("height", y.bandwidth()/2)
                .attr("width", function(d) {
                    return Math.max(0, x(d.Freq));
                })
                .style("fill", color2_1)
                .attr("opacity", 0.8);

            // adapted from http://bl.ocks.org/mbostock/1166403

            var xAxis = d3.axisTop(x).tickSize(-_hTopic).ticks(6);

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
            circle.style.fill = color_topic_1_1;

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
            var _hOff = tveBarheightFor(barFreqsID);

            var y = d3.scaleBand()
                    .domain(dat2.map(function(d) {
                        return d.Term;
                    }))
                    .rangeRound([0, _hOff])
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
                .attr("height", y.bandwidth()/2)
                .attr("width", function(d) {
                    return Math.max(0, x(d.Total));
                })
                .style("fill", color1_1)
                .attr("opacity", 0.4);

            //Change word labels
            d3.selectAll(to_select + " .terms")
                .data(dat2)
                .attr("x", -5)
                .attr("y", function(d) {
                    return y(d.Term) + 9;
                })
                .style("text-anchor", "end") // right align text - use 'middle' for center alignment
                .text(function(d) {
                    return d.Term;
                });

            // adapted from http://bl.ocks.org/mbostock/1166403

           var xAxis = d3.axisTop(x).tickSize(-_hOff).ticks(6);

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
            
            return (number*100).toFixed(1) + '%';

        }



        function get_name_text_column_on_relevant_documents(relevantDocumentsDict){
            //get the name of the columns

            /* For the user study we are going to comment this
            var name_columns = Object.keys(relevantDocumentsDict[0])
            var column_text_name = ''
            name_columns.forEach(
                element => {
                    if(typeof relevantDocumentsDict[0][element] == "string"){                                            
                        column_text_name = element
                        
                    }
                })
            return column_text_name*/
                       
            return 'text'                           
        }


      

        function arrayRemove(arr, value) { 
            return arr.filter(function(ele){ 
                return ele != value; 
            });
        }

            //slider topic splitting
        $('#tableRelevantDocumentsClass_TopicSplitting').on('post-body.bs.table', function (e) {


            $('.radio_button_topic_splitting').off('click.tvesplit').on('click.tvesplit', function () {


                if ($(this).is(':checked')) {
                        //update the values in the dictionary                
                        if(slider_topic_splitting_values[splitting_topic] == undefined ){
                            slider_topic_splitting_values[splitting_topic] = {};
                            
                            
                        }
                        var current_id_radio_button = this.id;
                        // tveSp_{topicId}_{dDOCID|iIDX}_{TopicA|TopicB|TopicNone} — avoids indexOf -1
                        // when bootstrap-table re-wraps row objects.
                        var m = current_id_radio_button.match(/^tveSp_(\d+)_(d\d+|i\d+)_(TopicA|TopicB|TopicNone)$/);
                        var current_row;
                        if (m) {
                            var rowKey = m[2];
                            var current_class = m[3];
                            if (rowKey.charAt(0) === "d") {
                                var did = parseInt(rowKey.slice(1), 10);
                                current_row = current_relevant_documents_topic_splitting.find(function (r) {
                                    return r && r.doc_id == did;
                                });
                            } else {
                                var gi = parseInt(rowKey.slice(1), 10);
                                current_row = current_relevant_documents_topic_splitting[gi];
                            }
                        } else {
                            // legacy id shape (topic_index_class)
                            var parts = current_id_radio_button.split("_");
                            var current_index = parts[1];
                            var current_class = parts[2];
                            current_row = current_relevant_documents_topic_splitting[current_index];
                        }
                        if (!current_row) {
                            if (typeof window !== "undefined" && window.TVE_DEBUG) {
                                console.warn("[TVE split] could not resolve row for id " + current_id_radio_button);
                            }
                            tveUpdateSplitModalStatus();
                            return;
                        }


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

                    }
                tveUpdateSplitModalStatus();

            });
            
            if(slider_topic_splitting_values[splitting_topic] !== undefined ){
                var array_current_relevant_documents_topic_splitting = Object.values(current_relevant_documents_topic_splitting);
                for (const [key, value] of Object.entries(slider_topic_splitting_values[splitting_topic] )) {
                    for (var i = 0; i < slider_topic_splitting_values[splitting_topic][key].length; i++) {
                        var srow = slider_topic_splitting_values[splitting_topic][key][i];
                        var rowKey2;
                        if (srow && srow.doc_id != null && srow.doc_id !== undefined) {
                            rowKey2 = "d" + String(srow.doc_id);
                        } else {
                            var gix = array_current_relevant_documents_topic_splitting.findIndex( function (s) { return s == srow; } );
                            if (gix < 0) { gix = array_current_relevant_documents_topic_splitting.findIndex( function (s) { return s && srow && s.doc_id === srow.doc_id; } ); }
                            if (gix < 0) { gix = 0; }
                            rowKey2 = "i" + gix;
                        }
                        var elst = document.getElementById("tveSp_" + splitting_topic + "_" + rowKey2 + "_" + key);
                        if (elst != null) { elst.checked = true; }

                    }
                }               

            }
            tveUpdateSplitModalStatus();
        });
        //Show how the relevant keywords are being used in the most relevant documents. 
        //Maybe, also, we should increase the bold of the keyword in the left panel too. 



        function updateRelevantDocumentsTopicSplitting(topic_id, relevantDocumentsDict, model){
            var _row0 = relevantDocumentsDict && relevantDocumentsDict[0];
            _tveDebug("split", "updateRelevantDocumentsTopicSplitting", {
                topic_id: topic_id,
                splitting_topic: splitting_topic,
                model: model,
                hasPercentColumn: _row0 && (String(topic_id) in _row0)
            });
            var column_text_name = get_name_text_column_on_relevant_documents(relevantDocumentsDict)
            //sorted regarding to its contribution
            relevantDocumentsDict.sort(function(row_1, row_2){
                return row_2[String(topic_id)]-row_1[String(topic_id)];
            });
            var threshold_max_number_docs_splitting = (0.10*Object.keys(relevantDocumentsDict).length).toFixed(0)
            current_relevant_documents_topic_splitting = relevantDocumentsDict; // the documents are sorted according to the contribution to the specific topic 

            function tveRowKeyForSplitTable(row) {
                if (!row) { return "i0"; }
                if (row.doc_id != null && row.doc_id !== undefined) { return "d" + String(row.doc_id); }
                var gi = relevantDocumentsDict.indexOf(row);
                if (gi < 0) {
                    gi = relevantDocumentsDict.findIndex(function (r) {
                        return r && row && (r === row || (r.text === row.text));
                    });
                }
                if (gi < 0) { gi = 0; }
                return "i" + gi;
            }

            if(model == 1){
                $('#tableRelevantDocumentsClass_TopicSplitting').bootstrapTable("destroy");
                $('#tableRelevantDocumentsClass_TopicSplitting').bootstrapTable({
                    toggle:true,
                    //height:420,
                    pagination: true,

                    //showRefresh: true,
                    search: true,
                    sorting: true,
                    //uniqueId: column_text_name,
                    //idField: column_text_name, 
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
                            titleTooltip: 'Relevance of this document to the topic you are splitting (percentage of tokens).',
                            sortable:'true'
                        },{
                            field: column_text_name,
                            escape: false,
                            title: 'Document',
                            titleTooltip: 'Document text; sort or search in the table toolbar.',
                            sortable: 'true',
                            formatter: _tveDocumentTextCellFormatter
                        },
                        {
                            field: 'Term',
                            title: 'New subtopic A',
                            titleTooltip: 'At least one document must be assigned to A. Seed documents for the first new subtopic.',
                            align: 'center',
                            valign: 'middle',
                            clickToSelect: false,
                            formatter : function(value,row) {
                                var rk = tveRowKeyForSplitTable(row);
                                return '<input type="radio" name="tveSp_grp_'+splitting_topic+'_'+rk+'" id="tveSp_'+splitting_topic+'_'+rk+'_TopicA" class="radio_button_topic_splitting" />';
                             }                      
                          },
                          {
                             field: 'Term',
                             title: 'New subtopic B',
                             titleTooltip: 'At least one document must be assigned to B. Seed documents for the second new subtopic.',
                             align: 'center',
                             valign: 'middle',
                             clickToSelect: false,
                             formatter : function(value,row) {
                                var rk = tveRowKeyForSplitTable(row);
                                return '<input type="radio"  name="tveSp_grp_'+splitting_topic+'_'+rk+'" id="tveSp_'+splitting_topic+'_'+rk+'_TopicB" class="radio_button_topic_splitting" />';
     
                              }                      
                           },
                           {
                             field: 'Term',
                             title: 'Neither',
                             titleTooltip: 'Document is not a seed; you still need at least one A and one B elsewhere in the table.',
                             align: 'center',
                             valign: 'middle',
                             clickToSelect: false,
                             formatter : function(value,row) {
                                var rk = tveRowKeyForSplitTable(row);
                                return '<input type="radio" name="tveSp_grp_'+splitting_topic+'_'+rk+'"  id="tveSp_'+splitting_topic+'_'+rk+'_TopicNone" class="radio_button_topic_splitting" checked/>';
                              }                      
                           }                               
                      
                        
                    ],
                    data: relevantDocumentsDict.slice(0,threshold_max_number_docs_splitting) // We dont need to show to the user a huge number of documents
                });
            }

            

            $(".search-input").attr("placeholder", "Search on documents").val("").focus().blur();
            setTimeout(function () { tveUpdateSplitModalStatus(); }, 0);
        }

        var omited_events_table =['pre-body.bs.table','post-header.bs.table', 'reset-view.bs.table', 'pre-body.bs.table', 'post-body.bs.table', 'post-footer.bs.table', 'click-row.bs.table']
        $('#tableRelevantDocumentsClass_Model1').on('all.bs.table', function (e, name, args) {
            if(!omited_events_table.includes(name)){


            }
        });

        
        $('#tableRelevantDocumentsClass_Model1').highlight($(".search.bs.table").val());

        // === Modernization: Phase 4e ===
        // Delegated handler for the per-row exclude button. We bind on
        // the container (rather than each <button>) because bootstrap-
        // table replaces the entire <tbody> on every redraw / sort /
        // page change, which would orphan direct handlers.
        $('#tableRelevantDocumentsClass_Model1').on('click', '.tve-doc-exclude-ctrl', function(ev){
            ev.preventDefault();
            ev.stopPropagation();
            var docIdAttr = $(this).attr('data-doc-id');
            var docId = parseInt(docIdAttr, 10);
            _tveExcludeDocument(docId);
        });

        $('#tableRelevantDocumentsClass_Model1').on('search.bs.table', function (e, text){

            $('#tableRelevantDocumentsClass_Model1').highlight(text);
            //console.log(e);
            //console.log(text);
        });



        $('#tableRelevantDocumentsClass_Model2').on('all.bs.table', function (e, name, args) {
            if(!omited_events_table.includes(name)){

            }
        });

        $('#tableRelevantDocumentsClass_Model2').highlight($(".search.bs.table").val());

        $('#tableRelevantDocumentsClass_Model2').on('search.bs.table', function (e, text){

            $('#tableRelevantDocumentsClass_Model2').highlight(text);
            //console.log(e);
            //console.log(text);
        });


        $('#tableRelevantDocumentsClass_TopicSplitting').on('all.bs.table', function (e, name, args) {
            if(!omited_events_table.includes(name)){

            }
        });

        
        $('#tableRelevantDocumentsClass_TopicSplitting').highlight($(".search.bs.table").val());

        $('#tableRelevantDocumentsClass_TopicSplitting').on('search.bs.table', function (e, text){

            $('#tableRelevantDocumentsClass_TopicSplitting').highlight(text);
            //console.log(e);
            //console.log(text);
        });





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
                    columns: _tveDocumentColumnsModel1(topic_id, column_text_name),
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
                            escape: false,
                            title: 'Document',
                            sortable: 'true',
                            formatter: _tveDocumentTextCellFormatter
                        }
                    ],
                    data: relevantDocumentsDict
                });
            
            }
            $(".search-input").attr("placeholder", "Search on documents").val("").focus().blur();

        
        }
        


        // minor fixes
        //This is the special configuration needed for the user study
        if(is_tutorial==true){
            show_tutorial()

        }

        if(type_vis == 1){
            document.getElementById("DocumentsPanel").style.height="80%";
            d3.select("#"+topicEdit).attr('class', 'btn btn-primary btnTopicLeft');
            if(is_human_in_the_loop == false){
                d3.select("#"+topicReverse).remove();
                d3.select("#"+topicSplit).remove();
                d3.select("#"+topicMerge).remove();

            }
            else{
                //align buttons to the left
                d3.select("#"+topicMerge).attr('class', 'btn btn-primary btnTopicLeft');
                d3.select("#"+topicSplit).attr('class', 'btn btn-primary btnTopicLeft');
                d3.select("#"+topicReverse).attr('class', 'btn btn-primary btnTopicLeft');                
            }
        }
        if(type_vis == 2){
            if(document.getElementById(topicMerge)!= undefined){
                document.getElementById(topicMerge).disabled = true;

            }
            if(document.getElementById(topicSplit) != undefined){
                document.getElementById(topicSplit).disabled = true;

            }
            if(document.getElementById(topicReverse) != undefined){
                document.getElementById(topicReverse).disabled = true;

            }
        }
        // === Modernization: null-guard around getElementById (added during Vite/TS migration) ===
        // The legacy code unconditionally dereferenced `document.getElementById(topicReverse)`
        // here, but a few lines above (line ~4446) the same element may have
        // been removed via `d3.select(...).remove()` when human-in-the-loop is
        // disabled. In the script-tag deployment that path was never exercised
        // by the paper user study, so the latent null deref didn't surface.
        // Under bundler scope the page now hard-fails with "Cannot set
        // properties of null". Guarding it matches the style used at lines
        // 4459/4463/4467 just above and is a no-op when the element exists.
        var topicReverseEl = document.getElementById(topicReverse);
        if(topicReverseEl){
            topicReverseEl.disabled = old_topic_model_states.length > 0 ? false : true;
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
            document.getElementById("topic_name_div").style.width="65%";
            document.getElementById("topic_name_div_right_panel").style.width="65%";            
            document.getElementById("topic_buttons_div").style.width="35%";
            document.getElementById("topic_buttons_div_right_panel").style.width="35%";
            //document.getElementsByClassName('bootstrap-table ').style.height='80%';
            
            if( scenario_2_is_baseline_metric == true ) { // it means we are using the metric baseline
                //we need to remove the omega slider, in this case  
                d3.select("#TopicSimilarityMetricPanel").remove()       
            }                   
        }

        // === Modernization: expose closure-private helpers to the
        // outer LDAvis scope so the Phase 4d/4e edit-operation hooks
        // (`_tveAddRemoveWord`, `_tveExcludeDocument`) can call back
        // into the original render functions. The original script-tag
        // deployment used `window.*` accidentally because all the
        // legacy code lived in the global scope; under bundler scope
        // we have to thread the references explicitly. We bind them
        // through a single object on the LDAvis instance scope so the
        // exposure is opt-in, namespaced, and easy to remove later.
        _tveInternals.topic_on = topic_on;
        _tveInternals.updateRelevantDocuments = updateRelevantDocuments;
    }
    
    if (typeof data_or_file_name === 'string'){
        
        d3.json(data_or_file_name, function(error, data) {visualize(data);});
    }

        
    else{
        
        visualize(data_or_file_name);
        
    }
        


};




// === Modernization shim (added during Vite/TS migration; do not move into main bundle) ===
// In <script>-tag world the top-level `var LDAvis = ...` above became a
// window global automatically. Under bundler scope it does not, so we
// expose it explicitly here. All visualisation behaviour above this line
// is the verbatim paper-version code.
if (typeof window !== 'undefined') {
    window.LDAvis = LDAvis;
}
