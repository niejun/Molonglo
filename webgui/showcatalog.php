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
        points.push(widthh);
        points.push(heightt);
        var tempstring="";
        for(var i=0;i<points.length;i=i+2){
          tempstring = tempstring + "<tr><td>"+points[i]+"</td><td>"+points[i+1]+"</td></tr>";
        }
        $("#add_list").html(tempstring);
        
    })
});

$(document).ready(function(){
  $("#subm").click(function(){
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
    <td width="18%">&nbsp;</td>
  </tr>
  <tr>
    <td height="40">&nbsp;</td>
    <td>
      <button type="button" id="submitadd">Submit</button>
      <button type="button" id="clearadd">Clear</button>
    </td>
    <td>&nbsp;</td>
  </tr>
  <tr>
    <td height="105" colspan="3">
      <p id="log"></p>
    </td>
  </tr>
</table>
</body>
</html>

<?php





?>
