<?php
  header('image/png');
  $img=imagecreatetruecolor(300, 30);  
  $text_color=imagecolorallocate($img, 200, 200, 200);
  $time = date("F j, Y, g:i:s a");
  //echo $time;
  imagestring($img, 5, 5, 5,  $time, $text_color);
  imagepng($img);
  imagedestroy($img);
?>
