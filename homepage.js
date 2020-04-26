$(document).ready(function(){

    const adc = document.getElementById("adc-list");
    const highb = document.getElementById("highb-list");
    const t2 = document.getElementById("t2-list");
    const updateButton = document.getElementById("updatelist");
    updateButton.addEventListener("click", updateLists);
    var adc_list = "";
    var highb_list = "";
    var t2_list = "";

    $.ajax({type: 'GET', url: '/api/imagelist',
        success : function(data) {
            console.log('success', data);

            adc_list = " <ul> ";
            for(i=0; i<data.adc[0].length; i++)
            {
                adc_list = adc_list + " <li> "+ data.adc[0][i] +" </li>";
            }
            adc_list = adc_list +  " </ul> ";
            highb_list =  " <ul> ";
            for(i=0; i<data.highb[0].length; i++)
            {
                highb_list = highb_list +  "<li> "+ data.highb[0][i] +" </li>";
            }
            highb_list = highb_list + " </ul> ";
            t2_list  = "<ul>";
            for(i=0; i< data.t2[0].length; i++)
            {
                t2_list = t2_list + "<li> "+ data.t2[0][i] +" </li>";
            }
            t2_list  =  t2_list + " </ul> ";

            console.log(adc_list);
            console.log(highb_list);
            console.log(t2_list);
        }
    })
    function updateLists(){
        adc.innerHTML = adc_list;
        highb.innerHTML = highb_list;
        t2.innerHTML = t2_list;
    }
})