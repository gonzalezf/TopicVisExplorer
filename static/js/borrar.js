
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
    });

    $('.tableRelevantDocumentsClass_Split').on('uncheck.bs.table', function (e, row) {
    $.each(checkedRows, function(index, value) {
        if (value.id === row.id) {
        checkedRows.splice(index,1);
        }
    });
    });

    $("#add_cart").click(function() {
    $("#output").empty();
    $.each(checkedRows, function(index, value) {
        $('#output').append($('<li></li>').text(value.text+"---"+value.topic_perc_contrib+"---"+value.uncategorized+"---"+value.subtopic1+"---"+value.subtopic2));
    });
    });

    function updateRelevantDocumentsSplitting(topic_id, relevantDocumentsDict){
        console.log("funcion update relevant documents splitting, topic id", topic_id, "relevant documents dict", relevantDocumentsDict);
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
    }