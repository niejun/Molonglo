<html>
<head>
<script src="//ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js">
</script>
<script>
var points = new Array();
$(document).ready(function(){
 $("#currentcatalog").click(function(e){
        var widthh=e.originalEvent.x-$(this).offset().left||e.originalEvent.layerX-$(this).offset().left||0;//
        var heightt=$(this).height()-(e.originalEvent.y-$(this).offset().top)||$(this).height()-(e.originalEvent.layerY-$(this).offset().top)||0;//
        ewd = -90.0 + (widthh - 48)/9.0 * 2.0;
        nsd = -90.0 + (heightt - 34)/9.0 * 2.0;
        points.push(ewd);
        points.push(nsd);
        var tempstring="";
        for(var i=0;i<points.length;i=i+2){
          tempstring = tempstring + "<tr><td>"+Math.round(points[i]*100)/100+"</td><td>"+Math.round(points[i+1]*100)/100+"</td></tr>";
        }
        $("#add_list").html(tempstring);
        
    })
});

$(document).ready(function(){
  $("#submitadd").click(function(){
    $.post("addtojoblist.php",{
      coords:points.toString()
    },
    function(data, status){
      $("#log").html(data);
      points = [];
      $("#add_list").html("");
    });
  });
});


$(document).ready(function(){
  $("#clearadd").click(function(){
    points = [];
    $("#add_list").html("");
  });
});

setInterval(function(){
$(document).ready(function(){
    var tempstring="";
    $.get("getjoblist.php",function(data, status){
      var tmpdata = data.split(",");
      
      if (tmpdata.length>0){
        if (tmpdata.length>1 && tmpdata[1]!=0){
          $("#observing").html(tmpdata[0]);
        }
        else{
          $("#observing").html("Stopped");
        }
        if (tmpdata.length>2){
          for(var i=2;i<tmpdata.length;i=i+2){
            tempstring = tempstring + "<tr><td>"+tmpdata[i]+"</td></tr>";
          }
          $("#joblist").html(tempstring);
        }
        else{
          $("#joblist").html("Empty");
        }
      }
    });

  });
},3000);


setInterval(function(){
  $(document).ready(function(){
    
    $("#currentcatalog").attr("src", "currentpulsars.png");
    alert("Reload +");
  });
}, 3000);

</script>
</head>

<body>





<table width="100%" border="1" cellspacing="0" cellpadding="0">
  <tr>
    <td colspan="3">
      <img id="banner" width="1280" height="100" src="banner.png" title="Banner"></img>
    </td>
  </tr>
  <tr>
    <td width="64%" height="234">
      <img id="currentcatalog" width="900" height="750" src="currentpulsars.png" title="Pulsars"></img>
    </td>
    <td width="18%">
      <table id="add_list">Points</table>
    </td>
    <td width="18%">
      <table border="1" cellspacing="0" cellpadding="0">
        <tr>
          <td>Observing</td>
        </tr>
        <tr>
          <td id="observing">observing
          </td>
        </tr>
        <tr>
          <td>Job List
          </td>
        </tr>
        <tr>
          <td id="joblist">joblist
          </td>
        </tr>
      </table>
    </td>
  </tr>
  <tr>
    <td height="40">&nbsp;</td>
    <td>
      <button type="button" id="submitadd">Submit</button>
      <button type="button" id="clearadd">Clear</button>
    </td>
    <td>test</td>
  </tr>
  <tr>
    <td height="105" colspan="3">
      <p id="log"></p>
    </td>
  </tr>
</table>
<?php

echo "test";



?>

</body>
</html>


