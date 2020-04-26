$(document).ready(function(){
    var num =0;
    var imnum = 0;
    var iround = 0;
    var initial = 0;
    var longest = 0;
    var adc = new Array();
    var highb = new Array();
    var t2 = new Array();
    var coordinates = new Array();

    const l1 = document.getElementById("label1");
    const l2 = document.getElementById("label2");
    const l3 = document.getElementById("label3");

    const prev = document.getElementById("previous");
    prev.addEventListener("click", previousImage);
    const nxt = document.getElementById("next");
    nxt.addEventListener("click", nextImage);
    const clr = document.getElementById("clear")
    clr.addEventListener("click", clearImage)

    const c1 = document.getElementById("canvas1");
    const c2 = document.getElementById("canvas2");
    const c3 = document.getElementById("canvas3");

    var ctx1 = c1.getContext("2d");
    var ctx2 = c2.getContext("2d");
    var ctx3 = c3.getContext("2d");

    $.ajax({type: 'GET', url: '/api/images',
        success : function(data) {
            console.log('success', data);

            longest = data.adc.length;
            if (data.highb.length>longest)
                longest = data.highb.length;
            if (data.t2.length>longest)
                longest =  data.t2.length;

            for(var i = 0; i<longest; i++){
                adc[i] =  new Image();
                if (i< data.adc.length)
                    adc[i].src =  data.adc[i];
                else
                    adc[i].src = 'static\placeholder.png';

                highb[i] =  new Image();
                if (i< data.highb.length)
                    highb[i].src =  data.highb[i];
                else
                    highb[i].src = 'static\placeholder.png';

                t2[i] =  new Image();
                if (i< data.t2.length)
                    t2[i].src =  data.t2[i];
                else
                    adc[i].src = 'static\placeholder.png';
            }

            adc[0].onload = ctx1.drawImage(adc[0],0,0);
            highb[0].onload = ctx2.drawImage(t2[0],0,0);
            t2[0].onload = ctx3.drawImage(highb[0],0,0);
            init(c1,ctx1);
            init(c2,ctx2);
            init(c3,ctx3);

        }
    });

    function init(c,ctx){
        c.width = 384;
        c.height = 384;
        c.addEventListener("click", RespondClick);
        c.addEventListener("wheel", Respondscroll);
        ctx.lineWidth = 3;
        ctx.strokeStyle = 'blue';
        console.log("initialized");
    }

    function Respondscroll(event){
        initial = imnum;
        num = num + event.deltaY;
        imnum = Math.round(num/100);

        if(imnum > longest -1)
            imnum = longest -1;
        else if(imnum<0)
            imnum = 0;

        num= imnum*100;
        if (initial != imnum)
            updateImages()
    }

    function previousImage(){
        imnum = Math.round(num/100);
        imnum = imnum -1;

        if(imnum > longest -1)
            imnum = longest -1;
        else if(imnum<0)
            imnum = 0;

        num= imnum*100;
        updateImages()
    }

    function nextImage(){
        imnum = Math.round(num/100);
        imnum = imnum +1;

        if(imnum > longest -1)
            imnum = longest -1;
        else if(imnum<0)
            imnum = 0;

        num= imnum*100;
        updateImages();
    }

    function clearImage(){
        console.log("clearing image");
        for (i = 0; i<coordinates.length; i++)
        {
            if (coordinates[i].slice == imnum)
            {
                coordinates.splice(i,1);
                console.log("spliced out" + i);
                i = i-1;
            }
        }
        updateImages();
    }

    function updateImages(){
        var first = true;
        console.log(num + "  :  " + imnum);

        ctx1.drawImage(adc[imnum], 0, 0);
        l1.innerHTML = "    adc:          " + (imnum+1) + "/" + adc.length;

        ctx2.drawImage(t2[imnum], 0, 0);
        l2.innerHTML =  "    T-2:          " + (imnum+1) + "/" + highb.length;

        ctx3.drawImage(highb[imnum], 0, 0);
        l3.innerHTML = "    High-B:          " + (imnum+1) + "/" + t2.length;

        ctx2.beginPath();
        for (i = 0; i<coordinates.length; i++){
            if (coordinates[i].slice == imnum)
            {
                if (first == true)
                {
                    first = false;
                    ctx2.moveTo(coordinates[i].x-getOffset(c2).left, coordinates[i].y-getOffset(c2).top);
                }
                else
                {
                    ctx2.lineTo(coordinates[i].x-getOffset(c2).left, coordinates[i].y-getOffset(c2).top);
                }
                ctx2.arc(coordinates[i].x-getOffset(c2).left, coordinates[i].y-getOffset(c2).top, 3, 0, 2 * Math.PI, false);
                console.log("slice " + coordinates[i].slice + ", x: " + coordinates[i].x + " | y: " +  coordinates[i].y);
            }
        }
        ctx2.closePath();
        ctx1.stroke();
        ctx2.stroke();
        ctx3.stroke();
    }

    function RespondClick(event){
        coordinates.push({slice: imnum, x: event.pageX, y: event.pageY})
        //console.log("slice " + event.pageX + ", x: " + event.pageY + " | y: " +  coordinates[0].y);
        updateImages();
    }

    function submission()
    {
        canvas.toBlob()
        const form = new FormData()
        form.append('image,blob')
    }

    function getOffset(el) {
        const rect = el.getBoundingClientRect();
        return {
            left: rect.left + window.scrollX,
            top: rect.top + window.scrollY
        };
    }
})








//    function init(c,ctx,firstSlice){
//        console.log(firstSlice);
//        c.width = 384;
//        c.height = 384;
//        c.addEventListener("click", RespondClick);
//        c.addEventListener("wheel", Respondscroll);
//        imageData = ctx.getImageData(0,0,384,384);
//        first = imageData.data;
//        console.log(imageData.data)
//        imageData.data = firstSlice;
//        second = imageData.data;
//        console.log(imageData.data)
//        if(first == second)
//            console.log("no difference");
//        ctx.putImageData(imageData, 0, 0);
//        ctx.beginPath();
//        ctx.moveTo(0,0);
//    }
//        $.ajax({type: 'GET', url: '/api/pixels',
//        success : function(data) {
//            console.log('success', data);
//            adc = data.adc;
//            highb = data.highb;
//            t2 = data.t2;
//
//            longest = adc.length;
//            if (highb.length>longest)
//                longest = highb.length;
//            if (t2.length>longest)
//                longest =  t2.length;
//
//            init(c1,ctx1,adc[0]);
//            init(c2,ctx2,highb[0]);
//            init(c3,ctx3,t2[0]);
//        }
//    });




//        if (event.target.id =="canvas1"){
//            if(firstClick == true){
//                ctx1.beginPath();
//                ctx1.moveTo(event.pageX-getOffset(event.target).left, event.pageY-getOffset(event.target).top);
//                firstClick = false;
//            }
//            else{
//                ctx1.lineTo(event.pageX-getOffset(event.target).left, event.pageY-getOffset(event.target).top);
//            }
//            ctx1.arc(event.pageX-getOffset(event.target).left, event.pageY-getOffset(event.target).top, 10, 0, 2 * Math.PI, false);
//            ctx1.moveTo(event.pageX-getOffset(event.target).left, event.pageY-getOffset(event.target).top);
//        }
//        else if (event.target.id == "canvas2"){
//            if(firstClick == true){
//                ctx2.moveTo(event.pageX-getOffset(event.target).left, event.pageY-getOffset(event.target).top);
//                firstClick =false;
//            }
//            else{
//                ctx2.lineTo(event.pageX-getOffset(event.target).left, event.pageY-getOffset(event.target).top);
//             }
//             ctx2.arc(event.pageX-getOffset(event.target).left, event.pageY-getOffset(event.target).top, 5, 0, 2 * Math.PI, false);
//             ctx2.moveTo(event.pageX-getOffset(event.target).left, event.pageY-getOffset(event.target).top);
//        }
//        else if (event.target.id == "canvas3"){
//            if(firstClick == true){
//                ctx3.moveTo(event.pageX-getOffset(event.target).left, event.pageY-getOffset(event.target).top);
//                firstClick = false;
//            }
//            else{
//                ctx3.lineTo(event.pageX-getOffset(event.target).left, event.pageY-getOffset(event.target).top);
//            }
//            ctx3.arc(event.pageX-getOffset(event.target).left, event.pageY-getOffset(event.target).top, 5, 0, 2 * Math.PI, false);
//            ctx3.moveTo(event.pageX-getOffset(event.target).left, event.pageY-getOffset(event.target).top);
//        }
//        ctx1.stroke();
//        ctx2.stroke();
//        ctx3.stroke();