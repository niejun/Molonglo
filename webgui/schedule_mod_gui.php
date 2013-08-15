<html>
<head>
<script src="//ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js">
</script>
<script>
$(document).ready(
  function(){
    $(".manual_schedule_button").click(
      function(){
        $.post("schedule_mod_core.php",{schedule_mode:"manual"});
      }
    );
  }
);



</script>

</head>
<body>

<p id="schedule_status"></p>

<button type="button" id="manual_schedule_button">Manual</button>
<button type="button" id="automatic_schedule_button">Automatic</button>

</body>
</html>


<?php



?>
