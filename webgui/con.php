<?php
/**
 * Simple example of extending the SQLite3 class and changing the __construct
 * parameters, then using the open method to initialize the DB.
 */

$dbfile = '../mol_pulsars.db';

class db extends SQLite3
{
    function __construct()
    {
        global $dbfile;
        $this->open($dbfile);
    }
}

$db = new db();


?>
