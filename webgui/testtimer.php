
<img  src="http://www.kitco.cn/CN/live_charts/usdx.gif" style="border: 1px solid #000000;" id="price1"  />

<script>
if (document.getElementById("price1")) {var intervalprice1 = setInterval(loadprice1,60000);}
///60秒自动刷新一次
</script>

<script>
function loadprice1(){
auimgurl=document.getElementById("price1").src;
document.getElementById("price1").src=auimgurl+ "?rnd=" + Math.random();
//转载请保留出处: www.tc711.com 原创
}
</script>

