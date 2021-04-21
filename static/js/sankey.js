//https://www.d3-graph-gallery.com/graph/sankey_basic.html
d3.sankey = function() {
  var sankey = {},
      nodeWidth = 24,
      nodePadding = 8,
      size = [1, 1],
      min_target_node_value = -1,
      nodes = [],
      links = [];

  

  sankey.nodeWidth = function(_) {
    if (!arguments.length) return nodeWidth;
    nodeWidth = +_;
    return sankey;
  };

  sankey.nodePadding = function(_) {
    if (!arguments.length) return nodePadding;
    nodePadding = +_;
    return sankey;
  };

  sankey.nodes = function(_) {
    if (!arguments.length) return nodes;
    nodes = _;
    return sankey;
  };

  sankey.links = function(_) {
    if (!arguments.length) return links;
    links = _;
    return sankey;
  };

  sankey.jsonDataArray = function(_) {
    if (!arguments.length) return jsonData;
    jsonDataArray = _;
    //console.log("esto fue lo recibido en json data", jsonDataArray)
    return sankey;
  };


  sankey.size = function(_) {
    if (!arguments.length) return size;
    size = _;
    return sankey;
  };

  sankey.min_target_node_value = function(_) {
    if (!arguments.length) return min_target_node_value;
    min_target_node_value = +_;
    
    return sankey;
  };

  sankey.layout = function(iterations) {
    computeNodeLinks();
    computeNodeValues();
    computeNodeBreadths();
    computeNodeDepths(iterations);
    computeLinkDepths();
    return sankey;
  };

  sankey.relayout = function() {
    computeLinkDepths();
    return sankey;
  };

  sankey.link = function() {
    var curvature = .5;

    function link(d) {
      var x0 = d.source.x + d.source.dx,
          x1 = d.target.x,
          xi = d3.interpolateNumber(x0, x1),
          x2 = xi(curvature),
          x3 = xi(1 - curvature),
          y0 = d.source.y + d.sy + d.dy / 2,
          y1 = d.target.y + d.ty + d.dy / 2;
      return "M" + x0 + "," + y0
           + "C" + x2 + "," + y0
           + " " + x3 + "," + y1
           + " " + x1 + "," + y1;
    }

    link.curvature = function(_) {
      if (!arguments.length) return curvature;
      curvature = +_;
      return link;
    };

    return link;
  };

  // Populate the sourceLinks and targetLinks for each node.
  // Also, if the source and target are not objects, assume they are indices.
  function computeNodeLinks() {
    nodes.forEach(function(node) {
      node.sourceLinks = [];
      node.targetLinks = [];
    });
    links.forEach(function(link) {
      var source = link.source,
          target = link.target;
      if (typeof source === "number") source = link.source = nodes[link.source];
      if (typeof target === "number") target = link.target = nodes[link.target];
      source.sourceLinks.push(link);
      target.targetLinks.push(link);
    });
  }

  // Compute the value (size) of each node by summing the associated links.
  function computeNodeValues() {

    //calcular el minimo valor (alto del nodo) distinto de cero diejeijde dejidei
    var min_height = Infinity;
    nodes.forEach(function(node) {
      if(d3.sum(node.sourceLinks, value)!= 0){
        if( d3.sum(node.sourceLinks, value) < min_height){
          min_height = d3.sum(node.sourceLinks, value)
        }
      }
      if(d3.sum(node.targetLinks, value)!= 0){
        if( d3.sum(node.targetLinks, value) < min_height){
          min_height = d3.sum(node.targetLinks, value)
        }
      }
    });
    //////console.log("cual es el min heigthmen este caso", min_height)
    //if min_height is infinity, that means that there are not any paths in the sankey diagram. I will add a dummy min height to still showing the topics
    if(min_height == Infinity){
      min_height = 1;
      nodes.forEach(function(node) {
        //////console.log("a verr cual es el node", node)
        node.x = 0;
      });  
      //////console.log("estos son la posicion x final de los nodos", nodes)
    }

    nodes.forEach(function(node) {
      node.value = Math.max(min_height,
        d3.sum(node.sourceLinks, value),
        d3.sum(node.targetLinks, value)
      );
    });

    //////console.log("COMPUTE NODE VALUEEEES , FINAL NODE", nodes)
  }

  // Iteratively assign the breadth (x-position) for each node.
  // Nodes are assigned the maximum breadth of incoming neighbors plus one;
  // nodes with no incoming links are assigned breadth zero, while
  // nodes with no outgoing links are assigned the maximum breadth.
  function computeNodeBreadths() {
    var remainingNodes = nodes,
        nextNodes,
        x = 0;

    while (remainingNodes.length) {
      nextNodes = [];
      remainingNodes.forEach(function(node) {
        node.x = x;
        node.dx = nodeWidth;
        node.sourceLinks.forEach(function(link) {
          if (nextNodes.indexOf(link.target) < 0) {
            nextNodes.push(link.target);
          }
        });
      });
      remainingNodes = nextNodes;
      ++x;
    }

    //
    if(x == 1){
      x = 2;
    }
    moveSinksRight(x);
    ////console.log("  ---  ------SCALE NODE BREADTHS", size[0], nodeWidth, x)
    scaleNodeBreadths((size[0] - nodeWidth) / (x - 1));
  }
  /*
  function moveSourcesRight() {
    nodes.forEach(function(node) {
      if (!node.targetLinks.length) {
        node.x = d3.min(node.sourceLinks, function(d) { return d.target.x; }) - 1;
      
      }
    });
  }
  */
  function moveSinksRight(x) {
    nodes.forEach(function(node) {
      
      if (!node.sourceLinks.length) {
        node.x = x - 1;
      }
      if(node.node < min_target_node_value){ //nodos del primer modelo aparecen a la izquierda
        //////console.log("esto se cumple o no??")
        node.x = 0;
      }
    });

    ////console.log("veamos los nodos que se reciben aqui, ", nodes, x)
  }

  function scaleNodeBreadths(kx) {
    nodes.forEach(function(node) {
      ////console.log("ANTES veamos cual es el kx", kx, node.x)
      node.x *= kx;
      ////console.log("DESPUES veamos cual es el kx", kx, node.x)
    });
  }

  function computeNodeDepths(iterations) {
    var nodesByBreadth = d3.nest()
        .key(function(d) { return d.x; })
        .sortKeys(d3.ascending)
        .entries(nodes)
        .map(function(d) { return d.values; });

    //
    initializeNodeDepth();
    resolveCollisions();
    for (var alpha = 1; iterations > 0; --iterations) {
      relaxRightToLeft(alpha *= .99);
      resolveCollisions();
      relaxLeftToRight(alpha);
      resolveCollisions();
    }

    function initializeNodeDepth() {
      var ky = d3.min(nodesByBreadth, function(nodes) {
        return (size[1] - (nodes.length - 1) * nodePadding) / d3.sum(nodes, value);
      });

      nodesByBreadth.forEach(function(nodes) {
        nodes.forEach(function(node, i) {
          node.y = i;
          node.dy = node.value * ky;
        });
      });

      links.forEach(function(link) {
        link.dy = link.value * ky;
      });
    }

    function relaxLeftToRight(alpha) {
      nodesByBreadth.forEach(function(nodes, breadth) {
        nodes.forEach(function(node) {
          if (node.targetLinks.length) {
            var y = d3.sum(node.targetLinks, weightedSource) / d3.sum(node.targetLinks, value);
            node.y += (y - center(node)) * alpha;
          }
        });
      });

      function weightedSource(link) {
        return center(link.source) * link.value;
      }
    }

    function relaxRightToLeft(alpha) {
      nodesByBreadth.slice().reverse().forEach(function(nodes) {
        nodes.forEach(function(node) {
          if (node.sourceLinks.length) {
            var y = d3.sum(node.sourceLinks, weightedTarget) / d3.sum(node.sourceLinks, value);
            node.y += (y - center(node)) * alpha;
          }
        });
      });

      function weightedTarget(link) {
        return center(link.target) * link.value;
      }
    }

    function resolveCollisions() {
      nodesByBreadth.forEach(function(nodes) {
        var node,
            dy,
            y0 = 0,
            n = nodes.length,
            i;

        // Push any overlapping nodes down.
        nodes.sort(ascendingDepth);
        for (i = 0; i < n; ++i) {
          node = nodes[i];
          dy = y0 - node.y;
          if (dy > 0) node.y += dy;
          y0 = node.y + node.dy + nodePadding;
        }

        // If the bottommost node goes outside the bounds, push it back up.
        dy = y0 - nodePadding - size[1];
        if (dy > 0) {
          y0 = node.y -= dy;

          // Push any overlapping nodes back up.
          for (i = n - 2; i >= 0; --i) {
            node = nodes[i];
            dy = node.y + node.dy + nodePadding - y0;
            if (dy > 0) node.y -= dy;
            y0 = node.y;
          }
        }
      });
    }

    function ascendingDepth(a, b) { //ojo, se esta ordenando en base a este atributo! quizas aqui es donde hay que añadir la frecuencia del topico. Hay que mandar esos datos al sankey
      //console.log("ascending receives", a, b) //probemos ordenando por la frecuencia. 

      if(a.node >= min_target_node_value){
        var Freq_1 = jsonData_2.mdsDat.Freq[a.node-min_target_node_value]    
      }
      else{
        var Freq_1 = jsonData.mdsDat.Freq[a.node]                       
      }
      if(b.node >= min_target_node_value){
        var Freq_2 = jsonData_2.mdsDat.Freq[b.node-min_target_node_value]    
      }
      else{
        var Freq_2 = jsonData.mdsDat.Freq[b.node]                       
      }
      
      //console.log("freq1, freq2", Freq_1, Freq_2)
      //return Freq_1-Freq_2
      return Freq_2-Freq_1
      //return a.y - b.y;
    }
  }

  function computeLinkDepths() {
    nodes.forEach(function(node) {
      node.sourceLinks.sort(ascendingTargetDepth);
      node.targetLinks.sort(ascendingSourceDepth);
    });
    nodes.forEach(function(node) {
      var sy = 0, ty = 0;
      node.sourceLinks.forEach(function(link) {
        link.sy = sy;
        sy += link.dy;
      });
      node.targetLinks.forEach(function(link) {
        link.ty = ty;
        ty += link.dy;
      });
    });

    function ascendingSourceDepth(a, b) {
      return a.source.y - b.source.y;
    }

    function ascendingTargetDepth(a, b) {
      return a.target.y - b.target.y;
    }
  }

  function center(node) {
    return node.y + node.dy / 2;
  }

  function value(link) {
    //console.log('ASHJKASJKASJKAS AQUI')
    //return link.value;
    return link.value;

  }

  return sankey;
};