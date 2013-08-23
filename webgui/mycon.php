<?php

$MYSQL_HOST = "localhost";
$MYSQL_USER = "scheduler";
$MYSQL_PASS = "molonglo";
#$MYSQL_PASS = "MMypssqrl";

$MYSQL_DB = "scheduler";



function query($sql){

    global $MYSQL_HOST,$MYSQL_USER,$MYSQL_PASS,$MYSQL_DB;
    $results = array();
    $link = mysql_connect($MYSQL_HOST, $MYSQL_USER, $MYSQL_PASS)
        or die("Could not connect : " . mysql_error()); 
    #print "Connected successfully";
    mysql_select_db($MYSQL_DB) or die("Could not select database");

    $result = mysql_query($sql) or die("Query failed : " . mysql_error()); 

    while ($line = mysql_fetch_array($result, MYSQL_ASSOC)) {
        $results [] = $line;
    }

    mysql_free_result($result);
    mysql_close($link);

    return $results;
}

#print_r(query("select * from PulsarList"));


?>
