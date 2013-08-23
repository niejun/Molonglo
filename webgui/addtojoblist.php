<?php

include('mycon.php');

$ewdiff = 2.0;
$nsdiff = 2.0;
$radius = 2.0;

$coords = $_POST['coords'];
$arr = split(",", $coords);

$observablepulsars = query('select * from PulsarStatus');

for($i = 0;$i<count($arr);$i = $i+2){
  $ewd = $arr[$i];
  $nsd = $arr[$i+1];

  for($j = 0;$j<count($observablepulsars);$j++){
    if(abs($observablepulsars[$j]['ewd'] - $ewd) <= $ewdiff && abs($observablepulsars[$j]['nsd'] - $nsd) <= $nsdiff){
      if(hypot(abs($observablepulsars[$j]['ewd'] - $ewd), abs($observablepulsars[$j]['nsd'] - $nsd))<=$radius){
        $sql = "insert into PulsarJobList values('".$observablepulsars[$j]['jname']."', 0, 0, 0)";
        query($sql);
        echo $sql."<br/>";
      }
    }

  }

  #echo $ewd.$nsd;
}

#var_dump($observablepulsars);

#print_r($arr);



?>
