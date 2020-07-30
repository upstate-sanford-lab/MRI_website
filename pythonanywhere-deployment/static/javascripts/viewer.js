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
    const clr = document.getElementById("clearMU");
    const nxt = document.getElementById("next");
    const smt = document.getElementById("submitMU");
    const deleteButton = document.getElementById("deleteFiles");
    const infoButton = document.getElementById("openInfo");
    const uploadButton = document.getElementById("openUpload");
    const sortDicomButton = document.getElementById("sortDicoms");
    const viewPort = document.getElementById("viewPort");
    const loader = document.getElementById("loading")

    document.getElementById("InformationTab").style.display = 'none';
    document.getElementById("uploadForm").style.display = 'none';
    document.getElementById("sortDicomsTab").style.display = 'none';
    loader.style.display = 'none';

    var dimensions = (viewPort.getBoundingClientRect().width/3) -30;

    prev.addEventListener("click", previousImage);
    nxt.addEventListener("click", nextImage);
    clr.addEventListener("click", clearMarkup);
    smt.addEventListener("click", submitMarkup);
    deleteButton.addEventListener("click", getImages);

    infoButton.addEventListener("click", function(){toggle_visibility("InformationTab")});
    uploadButton.addEventListener("click", function(){toggle_visibility("uploadForm")});
    sortDicomButton.addEventListener("click", function(){toggle_visibility("sortDicomsTab")});

    window.addEventListener("resize", updateDimensions);

    //window.addEventListener("resize", RespondResize);

    const c1 = document.getElementById("canvas1");
    const c2 = document.getElementById("canvas2");
    const c3 = document.getElementById("canvas3");

    var ctx1 = c1.getContext("2d");
    var ctx2 = c2.getContext("2d");
    var ctx3 = c3.getContext("2d");

    t2[0] = new Image();
    t2[0].src = 'static/placeholder.png';
    getImages();

    $(document.getElementsByClassName("window")).on( 'mousewheel DOMMouseScroll', function (e) {
      var e0 = e.originalEvent;
      var delta = e0.wheelDelta || -e0.detail;

      this.scrollTop += ( delta < 0 ? 1 : -1 ) * 30;
      e.preventDefault();
    });

    function toggle_visibility(id) {
        var e = document.getElementById(id);
        if(e.style.display == 'block')
            e.style.display = 'none';
        else
            e.style.display = 'block';
    }

    function getImages(){
        $.ajax({type: 'GET', url: '/api/images',
            success : function(data) {
                console.log('success', data);

                longest = data.adc.length;
                if (data.highb.length>longest)
                    longest = data.highb.length;
                if (data.t2.length>longest)
                    longest =  data.t2.length;

                if (longest == 0){
                    adc[0] = new Image();
                    adc[0].src = 'static/placeholder.png';
                    highb[0] = new Image();
                    highb[0].src = 'static/placeholder.png';
                    t2[0] = new Image();
                    t2[0].src = 'static/placeholder.png';
                }

                for(var i = 0; i<longest; i++){
                    adc[i] =  new Image();
                    if (i< data.adc.length)
                        adc[i].src =  data.adc[i];
                    else
                        adc[i].src = 'static/placeholder.png';

                    highb[i] =  new Image();
                    if (i< data.highb.length)
                        highb[i].src =  data.highb[i];
                    else
                        highb[i].src = 'static/placeholder.png';

                    t2[i] =  new Image();
                    if (i< data.t2.length)
                        t2[i].src =  data.t2[i];
                    else
                        adc[i].src = 'static/placeholder.png';
                }

                ctx2.lineWidth = 2;
                ctx2.strokeStyle = 'blue';

                init(c1);
                init(c2);
                init(c3);

                c2.addEventListener("click", RespondClick);
                adc[0].onload = updateImages;
                highb[0].onload = updateImages;
                t2[0].onload = updateImages;

            }, error: function(){
                alert("error receiving image data");
            }
        });
    }

    function init(c){
        c.addEventListener("wheel", Respondscroll);
        setDimensions(c)
    }
    function setDimensions(c){
        c.width = dimensions;
        c.height = dimensions;
    }

    function Respondscroll(event){
        initial = imnum;
        num = num + event.deltaY;
        imnum = Math.round(num/100);

        if (longest == 0)
            imnum = 0;
        else if(imnum > longest -1)
            imnum = longest -1;
        else if(imnum<0)
            imnum = 0;

        num= imnum*100;
        if (initial != imnum)
            updateImages();
    }

    function previousImage(){
        imnum = Math.round(num/100);
        imnum = imnum -1;
        if (longest == 0)
            imnum = 0;
        else if(imnum > longest -1)
            imnum = longest -1;
        else if(imnum<0)
            imnum = 0;

        num= imnum*100;
        updateImages();
    }

    function nextImage(){
        imnum = Math.round(num/100);
        imnum = imnum +1;

        if (longest == 0)
            imnum = 0;
        else if(imnum > longest -1)
            imnum = longest -1;
        else if(imnum<0)
            imnum = 0;

        num= imnum*100;
        updateImages();
    }

    function clearMarkup(){
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

    function submitMarkup(){
        loader.style.display = 'inline-block';
        var slices = "";
        var xcor = "";
        var ycor = "";
        var len = coordinates.length;
        for(i=0;i< len-1; i++)
        {
            slices = slices + coordinates[i].slice + ", ";
            xcor = xcor + Math.round(coordinates[i].x *(384/100)).toString() + ", ";
            ycor = ycor + Math.round(coordinates[i].y *(384/100)).toString() + ", ";
        }
        if(len>0)
        {
            slices = slices + coordinates[len-1].slice ;
            xcor = xcor + Math.round(coordinates[len-1].x*(384/100)).toString();
            ycor = ycor + Math.round(coordinates[len-1].y*(384/100)).toString();
        }

        console.log(xcor);
        console.log(ycor);

        $.ajax({type: 'POST',
          url: '/api/receiveMarkup',
          data: {primarySlice: imnum, slices: slices, x: xcor, y: ycor},
            success : function(server_message) {
                alert(server_message);
                loading.style.display = 'none';
            }, error: function(){
                alert("error with submission");
                loader.style.display = 'none';
            }
        });
    }

    function updateImages(){
        var first = true;
        console.log(num + "  :  " + imnum);
        setDimensions(c1);
        setDimensions(c2);
        setDimensions(c3);
        ctx1.drawImage(adc[imnum], 0, 0, dimensions, dimensions);
        ctx2.drawImage(t2[imnum], 0, 0, dimensions, dimensions);
        ctx3.drawImage(highb[imnum], 0, 0,dimensions, dimensions);
        ctx2.strokeStyle = 'blue';
        if (longest > 0){
            l1.innerHTML = "    adc:          " + (imnum+1) + "/" + adc.length;
            l2.innerHTML =  "    T-2:          " + (imnum+1) + "/" + highb.length;
            l3.innerHTML = "    High-B:          " + (imnum+1) + "/" + t2.length;
        }
        else {
            l1.innerHTML = "no images uploaded";
            l2.innerHTML = "no images uploaded";
            l3.innerHTML = "no images uploaded";
        }

        ctx2.beginPath();
        for (i = 0; i<coordinates.length; i++){
            if (coordinates[i].slice == imnum)
            {
                if (first == true)
                {
                    first = false;
                    ctx2.moveTo(coordinates[i].x * (dimensions/100), coordinates[i].y * (dimensions/100));
                }
                else
                {
                    ctx2.lineTo(coordinates[i].x * (dimensions/100), coordinates[i].y * (dimensions/100));
                }
                ctx2.arc(coordinates[i].x * (dimensions/100), coordinates[i].y * (dimensions/100), 3, 0, 2 * Math.PI, false);
                // console.log("dimensions " + dimensions)
                // console.log("slice " + coordinates[i].slice + ", x: " + Math.round(coordinates[i].x) + " | y: " +  Math.round(coordinates[i].y));
                // console.log("slice " + coordinates[i].slice + ", x * D: " + Math.round(coordinates[i].x* (dimensions/100)) + " | y * D: " +  Math.round(coordinates[i].y * (dimensions/100)));

            }
        }
        ctx2.closePath();
        ctx1.stroke();
        ctx2.stroke();
        ctx3.stroke();
    }

    function updateDimensions(){
        console.log(viewPort.getBoundingClientRect().width);
        dimensions = (viewPort.getBoundingClientRect().width / 3)-30;
        updateImages()
    }

    function RespondClick(event){
        x = (event.pageX - getOffset(c2).left)*(100/dimensions);
        y = (event.pageY - getOffset(c2).top)*(100/dimensions);
        coordinates.push({slice: imnum, x: x, y: y})
        //console.log("slice " + event.pageX + ", x: " + event.pageY + " | y: " +  coordinates[0].y);
        updateImages();
    }

    function getOffset(el) {
        var rect = el.getBoundingClientRect();
        return {
            left: rect.left + window.scrollX,
            top: rect.top + window.scrollY
        };
    }




// anonymizer scripts --------------------------------------------------------------------------------------------------------------------------------------

    // var fileCatcher = document.getElementById('file-catcher');
    // var fileInput = []
    // // fileInput[0] = document.getElementById('adc');
    // // fileInput[1] = document.getElementById('HighB');
    // // fileInput[2] = document.getElementById('T2');

    // fileInput[0] = document.getElementById('adcbox');
    // fileInput[1] = document.getElementById('highbbox');
    // fileInput[2] = document.getElementById('t2box');
    // // var fileListDisplay = document.getElementById('file-list-display');

    // for(h=0;h<3;h++)
    // {
    //     fileInput[h].addEventListener("dragenter", dragenter, false);
    //     fileInput[h].addEventListener("dragover", dragover, false);
    //     fileInput[h].addEventListener("drop", drop, false);
    // }
    // function dragenter(e) {
    //   e.stopPropagation();
    //   e.preventDefault();
    // }
    // function dragover(e) {
    //   e.stopPropagation();
    //   e.preventDefault();
    // }
    // function drop(e) {
    //   e.stopPropagation();
    //   e.preventDefault();

    //   const dt = e.dataTransfer;
    //   const files = dt.files;

    //   handleFiles(files, e.currentTarget.id);
    // }

    // var files = [];
    // var anonymizedFiles=[];
    // var sendFile;

    // function handleFiles(files,id){
    //     console.log(files)
    //     var isLast = false;
    //     for(i=0; i<files.length;i++){
    //         if(i==files.length-1){
    //             isLast = true;
    //         }
    //         anonymizeFile(files[i],i,isLast,id);
    //     }
    // }

    // function getTag(tag)
    // {
    //     var group = tag.substring(1,5);
    //     var element = tag.substring(5,9);
    //     var tagIndex = ("("+group+","+element+")").toUpperCase();
    //     var attr = TAG_DICT[tagIndex];
    //     return attr;
    // }

    // function anonymizeFile(file, num, isLast,id){
    //     console.log("anonymizing");
    //     var reader = new FileReader();
    //     reader.onload = (function(file) {
    //         var arrayBuffer = reader.result;
    //         var byteArray = new Uint8Array(arrayBuffer);
    //         var dataSet =  dicomParser.parseDicom(byteArray);

    //         var keys = [];
    //         for(var propertyName in dataSet.elements){
    //             keys.push(propertyName);
    //         };
    //         keys.sort();

    //         for(var k=0; k < keys.length; k++) {
    //             var propertyName = keys[k];
    //             var element = dataSet.elements[propertyName];

    //             var tag = getTag(element.tag);
    //             if(tag != undefined)
    //             {
    //                 //console.log("exists!")
    //                 var vr = tag.vr
    //                 if(dicomParser.isPrivateTag(element.tag))
    //                 {
    //                     console.log("private tag");
    //                     var str = dataSet.string(propertyName);
    //                     var deIdentifiedValue = makeDeIdentifiedValue(str.length, vr);
    //                     var char = (deIdentifiedValue.length > i) ? deIdentifiedValue.charCodeAt(i) : 32;
    //                     dataSet.byteArray[element.dataOffset + i] = char;
    //                 };
    //             }
    //             else{
    //                 //console.log("undefined value");
    //             };
    //         };
    //         var blob = new Blob([dataSet.byteArray], {type: "application/dicom"})
    //         anonymizedFiles[num] = blob;
    //     });
    //     reader.readAsArrayBuffer(file);
    //     reader.onloadend = (function(){
    //         if(isLast){
    //             sendFiles(anonymizedFiles,id)
    //         }
    //     });
    // }

    // function makeDeIdentifiedValue(length, vr) {
    //     if(vr === 'LO' || vr === "SH" || vr === "PN") {
    //         return makeRandomString(length);
    //     }
    //     else if(vr === 'DA') {
    //         var now = new Date();
    //         return now.getYear() + 1900 + pad(now.getMonth() + 1, 2) + pad(now.getDate(), 2);
    //     } else if(vr === 'TM') {
    //         var now = new Date();
    //         return pad(now.getHours(), 2) + pad(now.getMinutes(), 2) + pad(now.getSeconds(), 2);
    //     }
    //     console.log('unknown VR:' + vr);
    // }

    // // from http://stackoverflow.com/questions/1349404/generate-a-string-of-5-random-characters-in-javascript
    // function makeRandomString(length)
    // {
    //     var text = "";
    //     var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

    //     for( var i=0; i < length; i++ )
    //         text += possible.charAt(Math.floor(Math.random() * possible.length));

    //     return text;
    // }
    // function pad(num, size) {
    //     var s = num+"";
    //     while (s.length < size) s = "0" + s;
    //     return s;
    // }


    // function sendFiles(files,id) {
    //     console.log("sending data to /" + id)
    //   	var formData = new FormData();
    //     var request = new XMLHttpRequest();
    //     formData.set('files', files);
    //     request.open("POST", '/'+id);
    //     request.send(formData);
    //     getImages()
    // };


})
