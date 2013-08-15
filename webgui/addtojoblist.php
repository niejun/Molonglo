<?php

include('con.php');
#global $db;

#$result = $db->query('SELECT * FROM PulsarList');
#var_dump($result->fetchArray());

$ewdiff = 2.0;
$nsdiff = 2.0;
$radius = 2.0;

$coords = $_POST['coords'];
$arr = split(",", $coords);

$observablepulsars = array();
$results = $db->query('select * from PulsarStatus');
while ($row = $results->fetchArray()) {
  $observablepulsars[] = $row;
}

for($i = 0;$i<count($arr);$i = $i+2){
  $x = $arr[$i];
  $y = $arr[$i+1];
  $ewd = -90.0 + ($x-48)/9.0 * 2.0;
  $nsd = -90.0 + ($y-34)/9.0 * 2.0;

  for($j = 0;$j<count($observablepulsars);$j++){
    if(abs($observablepulsars[$j][1] - $ewd) <= $ewdiff && abs($observablepulsars[$j][2] - $nsd) <= $nsdiff){
      if(hypot(abs($observablepulsars[$j][1] - $ewd), abs($observablepulsars[$j][2] - $nsd))<=$radius){
        $sql = "insert into PulsarJobList values('".$observablepulsars[$j][0]."', 0, 0)";
        $db->query($sql);
        echo $observablepulsars[$j][0].$observablepulsars[$j][1].$observablepulsars[$j][2].$sql;
      }
    }

  }

  #echo $ewd.$nsd;
}

#var_dump($observablepulsars);

#print_r($arr);



?>
