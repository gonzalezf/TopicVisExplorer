
console.log('cargando este arhcivo');




$('#user_study_code_modal').modal({
    backdrop: 'static',
});

d3.select("#start_user_study_with_code_button")
                .on("click", function(){
                    var user_code = document.getElementById("user_study_code_input").value
                    console.log(' este es el user code ingresado', user_code);

                    var post_user_code = {
                        user_code: user_code,                        
                    };


                    $.ajax({
                        type: 'POST',
                        url: '/redirect_with_user_study_code',
                        data: JSON.stringify(post_user_code),
                        success: function(url) {
                            console.log(' ESTA DATA FUE RECIBIDA', url)
                            if(url != 'error'){
                                window.location.href = url;
                                console.log('yaaay, redirect done');
                            }else{
                                alert('The code was not found! Please make sure you typed the code correctly. Otherwise, contact felipe.gonzalez@dal.ca ');
                            }

                        },
                        error: function(XMLHttpRequest, textStatus, errorThrown) { 
                            alert("Status: " + textStatus +" Error: " + errorThrown + ' Please contact felipe.gonzalez@dal.ca')             
                        }, 
                        contentType: "application/json"             
                    })                
                })




