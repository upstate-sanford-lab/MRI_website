$(document).ready(function(){

    const adc = document.getElementById("adc-list");
    const highb = document.getElementById("highb-list");
    const t2 = document.getElementById("t2-list");
    const updateButton = document.getElementById("updatelist");
    const submitButton = document.getElementById("uploadBtn");

    updateButton.addEventListener("click", getLists);
    submitButton.addEventListener("click", getLists);
    window.onload = getLists();

    var adc_list = "";
    var highb_list = "";
    var t2_list = "";

    var adc_empty = true;
    var highb_empty = true;
    var t2_empty = true;

    function getLists(){
        console.log("getLists function was called")
        $.ajax({type: 'GET', url: '/api/imagelist',
            success : function(data) {
                console.log('success', data);
                adc_empty = true;
                highb_empty = true;
                t2_empty = true;

                adc_list = " <ul> ";
                for(i=0; i<data.adc[0].length; i++)
                {
                    adc_empty = false;
                    adc_list = adc_list + " <li> "+ data.adc[0][i] +" </li>";
                }
                adc_list = adc_list +  " </ul> ";



                highb_list =  " <ul> ";
                for(i=0; i<data.highb[0].length; i++)
                {
                    highb_empty = false;
                    highb_list = highb_list +  "<li> "+ data.highb[0][i] +" </li>";
                }
                highb_list = highb_list + " </ul> ";



                t2_list  = "<ul>";
                for(i=0; i< data.t2[0].length; i++)
                {
                    t2_empty = false;
                    t2_list = t2_list + "<li> "+ data.t2[0][i] +" </li>";
                }
                t2_list  =  t2_list + " </ul> ";

                updateLists();
            }
        })
    }

    function updateLists(){

        if(adc_empty == true)
        {
            adc.innerHTML = "No files uploaded";
            adc.style.color = "red";
        }
        else
        {
            adc.innerHTML = adc_list;
            adc.style.color = "green";
        }
        if(highb_empty == true)
        {
            highb.innerHTML = "No files uploaded";
            highb.style.color = "red"
        }
        else
        {
            highb.innerHTML = highb_list;
            highb.style.color = "green";
        }
        if(t2_empty == true)
        {
            t2.innerHTML = "No files uploaded";
            t2.style.color = "red"
        }
        else
        {
            t2.innerHTML = t2_list;
            t2.style.color = "green";
        }
    }
})
