

                .attr("transform", function(d){
                    return  "translate("+(xScale(+new_positions[d.topics-1][0]))+","+(yScale(+new_positions[d.topics-1][0]))+")";
                })


                .attr("transform", function(d){
                    
                    return  "translate("+(xScale(new_positions[d.topics-1][0]))+","+(yScale(new_positions[d.topics-1][0]))+")";
                })


                //cmabiar la propiedad del x e y no mas
        //http://bl.ocks.org/larskotthoff/11406992
        function arrangeLabels() {
            console.log("executing arrange labels function!! :)");
            var move = 1;
            while(move > 0) {
              move = 0;
              //var svg = d3.selectAll('#'+leftPanelID);
              //console.log("este es el svg que estoy pescando", svg);
              d3.selectAll(".txt")
                 .each(function() {
                     //console.log("estoy en estooo", this);
                   var that = this,
                       a = this.getBoundingClientRect();
                   d3.selectAll(".txt")
                      .each(function() {
                        if(this != that) {
                          var b = this.getBoundingClientRect();
                          if((Math.abs(a.left - b.left) * 2 < (a.width + b.width)) &&
                             (Math.abs(a.top - b.top) * 2 < (a.height + b.height))) {
                            // overlap, move labels
                            console.log("ay no overlap entre estos", this, that);
                            console.log("veamos esto primer elemento", d3.select(this));
                            //var nuevas = [d3.select(this).attr("x"), d3.select(this).attr("y")];
                            //console.log("estas son las nuevaaas", nuevas);
                            console.log("y este otoroo", d3.select(this).attr("transform"));
                            console.log("veamos esto segundo elemento", d3.select(that));
                            console.log("y este otoroo", d3.select(that).attr("transform"));

                            var dx = (Math.max(0, a.right - b.left) +
                                     Math.min(0, a.left - b.right)) * 0.01,
                                dy = (Math.max(0, a.bottom - b.top) +
                                     Math.min(0, a.top - b.bottom)) * 0.02,
                                //tt = d3.transform(d3.select(this).attr("transform")),                                            
                                tt = getTranslation(d3.select(this).attr("transform")),
                                //tt = [d3.select(this).attr("x"), d3.select(this).attr("y")],
                                //to = d3.transform(d3.select(that).attr("transform"));
                                to = getTranslation(d3.select(that).attr("transform"));                                
                                //to = [d3.select(that).attr("x"), d3.select(that).attr("y")];
                            move += Math.abs(dx) + Math.abs(dy);
                            console.log("a veeer", tt, to);
                          
                            //to.translate = [ to.translate[0] + dx, to.translate[1] + dy ];
                            to.translate = [ to[0] + dx, to[1] + dy ];
                            //tt.translate = [ tt.translate[0] - dx, tt.translate[1] - dy ];
                            tt.translate = [ tt[0] - dx, tt[1] - dy ];
                            console.log("estos son los objetos finales", to, tt);
                            d3.select(this).attr("transform", "translate(" + tt.translate + ")");
                            d3.select(that).attr("transform", "translate(" + to.translate + ")");
                            a = this.getBoundingClientRect();
                          }
                        }
                      });
                 });
            }
        }