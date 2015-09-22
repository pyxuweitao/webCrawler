var page = require('webpage').create(),
    system = require('system'),
    address;

if( system.args.length === 1 ){
    phantom.extit(1);
}
else{
    address = "https://detail.tmall.com/item.htm?id=";
    itemID  = system.args[1];
    var sc = page.open(address+itemID, function(status) {
        if (status != 'success') {
            phantom.exit(1);
        }



                var sc = page.evaluate(function () {
                 var res = "{";
                     //evaluate是对目标网页执行的js代码，所以不能引用本js的外部的全局变量。
                    try {
                        var attrList = document.getElementById("J_AttrUL").getElementsByTagName("li"); //天猫
                    }catch(e){
                        var attrList = document.querySelectorAll(".attributes-list>li"); //淘宝
                    }

                for( var i = 0; i < attrList.length; i++ ){
                  res = res + attrList[i].innerHTML + "@";
                }
                 res += "}";
            return res;

            });
                console.log(sc);
                phantom.exit();






//        page.onLoadFinished = function(status){
//            if( status == 'success') {
//                console.log("ok");
//                console.log(sc);
//            }
//            phantom.exit(1);
//        };




    });}


