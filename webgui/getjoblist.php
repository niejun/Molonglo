<?php

include('mycon.php');

$joblist = query('select * from PulsarJobList');
if (count($joblist)>0)
  for($i=0;$i<count($joblist);$i++){
    echo $joblist[$i]['jname'].",".$joblist[$i]['observing'];
    if ($i!=count($joblist)-1)
      echo ",";
  }


?>
