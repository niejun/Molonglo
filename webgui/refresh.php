<script>
setInterval(function(){


  $(document).ready(function(){
  var preloads = ["datepng.php"];

  $(preloads).each(function(){
  $(‘‘)[0].src = this;
  });

  //rest of your code here..
  });

  /*
  var date = new Date();
  var minute = date.getMinutes();
  var second = date.getSeconds() - 1;
  var path = "currentpulsars.png?k="+Math.random();
  var bufferImage = new Image(); //缓冲图片
  bufferImage.src = path;
  document.getElementById("currentcatalog").src=bufferImage.src;
  document.getElementById("time").innerHTML=Date();
  //alert(Date());
  */
}, 1000);
</script>
<p id="time"></p>
<img id="currentcatalog" src="datepng.php" title="Pulsars"></img>

