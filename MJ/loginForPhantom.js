var page = require('webpage').create(),
    system = require('system'),
    address;

if( system.args.length === 1 ){
    phantom.extit(1);
}
else{
    address = system.args[1];
    var sc = page.open(address, function(status) {
        if (status != 'success') {
            phantom.exit(1);
        }


        var sc = page.evaluate(function (v1, v2) {

                //evaluate是对目标网页执行的js代码，所以不能引用本js的外部的全局变量。
            document.querySelector('div.item:nth-child(4) > input:nth-child(1)').value = v1;//'13888888888';//system.args[2];
            document.querySelector('div.item:nth-child(5) > input:nth-child(1)').value = v2;//'p123456p';//system.args[3];
            document.querySelector('.ui-button').click();
        }, system.args[2], system.args[3]);
//    console.log(sc);

        page.onLoadFinished = function(status){
            if( status == 'success') {
                page.render("nihao.png");
                for( var i = 0; i < page.cookies.length; i++ ){
                    console.log(page.cookies[i].name+'='+page.cookies[i].value);
                }
                phantom.exit();
            }
        };

        //phantom.exit(1);
    });}

//}
//
//            window.setTimeout(function(){
//                page.render("baidu3.png");
//                console.log('*********************');
//                console.log(sc);
//                console.log('*********************');
//                console.log('==============');
//                    for( var i = 0;i < page.cookies.length; i++ )
//                        console.log(page.cookies[i].key+':'+page.cookies[i].value);
//                    console.log('==============');
//               phantom.exit();
//            },10000)
//        }
//
//    });

