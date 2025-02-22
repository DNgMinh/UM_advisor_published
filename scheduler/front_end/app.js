$(document).ready(function() {

    // keyboard commands
    $(document).keydown(function(event) {
        const isFormElementFocused = $(document.activeElement).is('input, textarea, select');
        // const isFormElementFocused = false;

        if (event.key === 'Enter') {  
            event.preventDefault();  
            $('#submit').click();  
        }
        if (event.key === 'ArrowRight' && !isFormElementFocused) {
            event.preventDefault(); 
            $('#nextSchedule1').click();
        }
        if (event.key === 'ArrowLeft' && !isFormElementFocused) {
            event.preventDefault(); 
            $('#prevSchedule1').click();
        }
    });


    $('#submit').click(function() {
        $('#loading1').show();
        $('#error').text('');
        // $('#error2').text('');
        $("#scheduleInfo1").html('');
        // $("#scheduleInfo2").html('');
        $("#ways").html("");
        $("#smallestTimeGap").html("");
        $("#best_class_list").html("");
        $("#customizedWays").html("");
        // $("#smallestCustomizedTimeGap").html("");
        // $("#best_customized_class_list").html("");
        $(".newTable").empty();
        // $(".myCustomizedTable").empty();

        // class list options without customization
        window.class_list_ways = [];
        // class list options with customization
        window.customized_class_list_ways = [];
        // for courses with weird schedule (e.g., ENG1440)
        window.weirdCourses = [];
        window.CRNsList = [];

        // for the best option without customization
        window.BEST_CLASS_LIST;
        window.START_TIME_LIST;
        window.END_TIME_LIST;
        window.WAYS;
        window.SMALLEST_TIME_GAP;

        // currentScheduleIndex1 = 0;
        currentScheduleIndex2 = 0;
        // Get the input value
        const coursesInput = $('#courses');
        const courses = coursesInput.val();
        const termInput = $('#term');
        const term = termInput.val();

        // Make an AJAX request to the backend
        $.ajax({
            url: 'http://127.0.0.1:5000/schedule',
            type: 'POST',
            // contentType: 'application/json',
            // data: JSON.stringify({ courses }),      // key is courses
            data: { courses: courses, term : term },

            success: function(response) {
                class_list_ways = response.class_list_ways;
                customized_class_list_ways = response.class_list_ways;
                weirdCourses = response.weirdCourses;
                console.log('Backend response:', response.ways);
                console.log('Backend response:', response.smallestTimeGap);

                // const best_class_list = response.best_class_list;
                BEST_CLASS_LIST = response.best_class_list;
                // console.log('Backend response:', best_class_list);
                console.log('Backend response:', BEST_CLASS_LIST);

                // const best_class_list_str = JSON.stringify(best_class_list);
                // const best_class_list_str = JSON.stringify(BEST_CLASS_LIST);

                START_TIME_LIST = response.startTime_list;
                END_TIME_LIST = response.endTime_list;
                WAYS = response.ways;
                SMALLEST_TIME_GAP = response.smallestTimeGap;

                $('#loading1').hide();
                $("#scheduleInfo1").html('');

                if (WAYS == 0) {
                    $("#ways").html("There are: " + WAYS + " ways.");
                }
                else {
                    $("#ways").html("There are: " + WAYS + " ways.");
                    $("#smallestTimeGap").html("The best option (fewest class days and minimal time gaps between classes) has the time gap of: " + SMALLEST_TIME_GAP + " hours per week.");
                    // $("#best_class_list").html("With this schedule: " + best_class_list_str);

                    $("#scheduleInfo1").html("Schedule number " + (currentScheduleIndex2+1) + " with the time gap = " + SMALLEST_TIME_GAP + " hrs/week");
                }

                drawScheduleTable("newTable", BEST_CLASS_LIST, START_TIME_LIST, END_TIME_LIST);
            },

            error: function(error) {
                BEST_CLASS_LIST = [];
                START_TIME_LIST = [];
                END_TIME_LIST = [];
                WAYS = -1;
                SMALLEST_TIME_GAP = -1;

                if (error.status == 404) {
                    let error_course = error.responseJSON.error_course;
                    if (error_course == "Maintenance") {
                        console.error(error_course);
                        $('#loading1').hide();
                        $('#error').text("The aurora site is under maintenance! Please try again later!");
                    }
                    // else if (error_course.includes("has no specific time (TBA)!") ) {
                    //     $('#loading1').hide();
                    //     $('#error').text(error_course);
                    // }
                    else {
                        console.error('Error 404: Course not found: ', error_course);
                        $('#loading1').hide();
                        $('#error').text(`No course ${error_course} can be found! Please check again!`);
                    }
                    
                } else {
                    console.error('Error:', error);  
                    $('#loading1').hide();                  
                    $('#error').text('Error! PLease check again!');
                }
            }
        })
    })

    // draw the schedule table
    function drawScheduleTable(tableClassName, class_list, startTime_list, endTime_list) {

        // return indexes of values of an array by ascending order
        function sortedIndexes(array) {
            const indexedArray = array.map((value, index) => ({ value:value, index:index }));
            indexedArray.sort((a, b) => a.value - b.value);
            const sortedIndexes = indexedArray.map(item => item.index);
            return sortedIndexes;
        }

        const startTime_sorted_indexes = sortedIndexes(startTime_list);
        const endTime_sorted_indexes = sortedIndexes(endTime_list);

        $(`.${tableClassName}`).empty(); 
        let soonest_time = startTime_list[startTime_sorted_indexes[0]] | 0;
        let latest_time = endTime_list[endTime_sorted_indexes[endTime_sorted_indexes.length-1]] | 0;
        for (let j = soonest_time; j <= latest_time; j++) {
            let first_column = `
            <tr value = "${j}" class="noBorder">
                <td style = "background-color: #f2f2f2;"></td>                
                <td class = "M"></td>
                <td class = "T"></td>
                <td class = "W"></td>
                <td class = "R"></td>
                <td class = "F"></td>
            </tr>
            <tr value = "${j+0.25}" class="noBorder">
                <td class="cell" style = "background-color: #f2f2f2;"><div class="hour"><strong>${j}:00</strong></div></td>
                <td class = "M"></td>
                <td class = "T"></td>
                <td class = "W"></td>
                <td class = "R"></td>
                <td class = "F"></td>
            </tr>
            <tr value = "${j+0.5}" class="noBorder">
                <td style = "background-color: #f2f2f2;"></td>
                <td class = "M"></td>
                <td class = "T"></td>
                <td class = "W"></td>
                <td class = "R"></td>
                <td class = "F"></td>
            </tr>
            <tr value = "${j+0.75}" class="noBorder">
                <td style="background-color: #f2f2f2; border-bottom: 1px solid #ddd;"></td>
                <td class = "M" style="border-bottom: 1px solid #ddd;"></td>
                <td class = "T" style="border-bottom: 1px solid #ddd;"></td>
                <td class = "W" style="border-bottom: 1px solid #ddd;"></td>
                <td class = "R" style="border-bottom: 1px solid #ddd;"></td>
                <td class = "F" style="border-bottom: 1px solid #ddd;"></td>
            </tr>`;

            $(`.${tableClassName}`).append(first_column);
        }
        var weirdCoursesColor = {};
        CRNsList = []
        for (let j = 0; j < startTime_list.length; j++) {
            let color_list = ["goldenrod","slateblue","firebrick","limegreen","mediumorchid","darksalmon","cornflowerblue","darkkhaki","darkslategray","darkgoldenrod"];
            let round_start_time = startTime_list[j] % 0.25 !== 0 ? startTime_list[j] - (startTime_list[j] % 0.25) : startTime_list[j];
            let round_end_time = endTime_list[j] % 0.25 !==0 ? endTime_list[j] - (endTime_list[j] % 0.25) + 0.25 : endTime_list[j];
            const _class = class_list[j];
            const className = Object.keys(_class)[0].slice(0, -3);                       // this object only has one key
            const classSection = Object.keys(_class)[0].slice(-3);
            const classTime = _class[Object.keys(_class)[0]][0];                    
            const days = _class[Object.keys(_class)[0]][1];
            let table = document.getElementsByClassName(`${tableClassName}`)[0];
            let time = round_start_time;
            let isExistedCRN = false;
            for (let i = 0; i < CRNsList.length; i++) {
                if (CRNsList[i] == _class[Object.keys(_class)[0]][2]) {
                    isExistedCRN = true;
                    break;
                }
            }
            if (!isExistedCRN) {
                CRNsList.push(_class[Object.keys(_class)[0]][2]) 
            }
            while (time < round_end_time) {
                let time_string = time.toString();
                let row = table.querySelector(`[value="${time_string}"]`);
                console.log(row);
                for (let i = 0; i < days.length; i++) {
                    let cell = row.querySelector(`.${days[i]}`);
                    if ((round_end_time + round_start_time - 0.25)/2 - time < 0.25 && (round_end_time + round_start_time - 0.25)/2 - time >= 0) {
                        cell.innerHTML = classSection; 
                        let above_row = table.querySelector(`[value="${(time-0.25).toString()}"]`);
                        let above_cell = above_row.querySelector(`.${days[i]}`);
                        above_cell.innerHTML = className;
                        let below_row = table.querySelector(`[value="${(time+0.25).toString()}"]`);
                        let below_cell = below_row.querySelector(`.${days[i]}`);
                        below_cell.innerHTML = classTime;
                    }
                    let color = color_list[j];
                    for (let i = 0; i < weirdCourses.length; i++) {
                        if (className == weirdCourses[i]) {
                            if (className in weirdCoursesColor) {
                                color = weirdCoursesColor[className]; 
                                continue;
                            }
                            weirdCoursesColor[className] = color_list[j];
                        }
                    }
                    cell.classList.add(color); 
                    cell.setAttribute('class-index', j)
                    cell.classList.add('isACourse')
                    if (time < round_end_time - 0.25) {cell.style.borderBottom= "none";}
                    if (time == round_end_time - 0.25 && round_end_time !== endTime_list[j]) {
                        let divHTML = `<div style="position: absolute; top: 0; left: 0; width: 100%; height: 33.33%; background-color: ${color_list[j]};"></div>`;
                        for (let i = 0; i < weirdCourses.length; i++) {
                            if (className == weirdCourses[i]) {
                                divHTML = `<div style="position: absolute; top: 0; left: 0; width: 100%; height: 33.33%; background-color: ${weirdCoursesColor[className]};"></div>`; 
                            }
                        }
                        cell.style.position = "relative";
                        cell.innerHTML += divHTML;
                        cell.style.backgroundColor = "transparent";
                    }
                }
                time += 0.25;
            }
        }
    }
    
    // the current option index 
    // var currentScheduleIndex1 = 0;

    // this function is no longer needed
    // function loadSchedule(index) {

    //     if (index == class_list_ways.length) {
    //         index = 0;
    //     }
    //     else if (index < 0) {
    //         index = class_list_ways.length - 1;
    //     }        

    //     currentScheduleIndex1 = index;
    //     const current_class_list = class_list_ways[index];

    //     $.ajax({
    //         url: 'http://127.0.0.1:5000/loadSchedule',
    //         type: 'POST',
    //         contentType: 'application/json',
    //         data: JSON.stringify({ current_class_list: current_class_list }),

    //         success: function(response) {
    //             $("#scheduleInfo1").html("Schedule number " + (currentScheduleIndex1+1) + " with the time gap = " + response.timeGap + " hrs/week");
    //             drawScheduleTable("newTable", current_class_list, response.startTime_list, response.endTime_list);
    //         },

    //         error: function(error) {
    //             console.error('Error:', error);
    //         }
    //     });
    // }

    $('#nextSchedule1').click(function() {
        // currentScheduleIndex1++;
        // loadSchedule(currentScheduleIndex1);
        currentScheduleIndex2++;
        loadCustomizedSchedule(currentScheduleIndex2);
    })

    $('#prevSchedule1').click(function() {
        // currentScheduleIndex1--;
        // loadSchedule(currentScheduleIndex1);
        currentScheduleIndex2--;
        loadCustomizedSchedule(currentScheduleIndex2);
    })

    $('#return1').click(function() {
        // currentScheduleIndex1 = 0;
        // loadSchedule(currentScheduleIndex1);
        currentScheduleIndex2 = 0;
        loadCustomizedSchedule(currentScheduleIndex2);
    })

    $('#retrieveCRNs').click(function() {
        $('.popup-overlay').css('display', 'flex');  // Show the popup
        for (let i = 0; i < CRNsList.length; i++) {
            let newLine = $(`<p>${CRNsList[i].slice(4)}</p>`);   
            // Append the new line to the popup
            $('#CRNsList').append(newLine);    
            console.log(CRNsList[i]);   
        }
    })

    $('#okPopup').click(function() {
        $('.popup-overlay').css('display', 'none');  // Hide the popup
        $('#CRNsList').empty(); 
    });


    $('table').on('click', '.isACourse', function (event) {
        console.log('Element clicked!', event);
        let index = event.target.getAttribute('class-index');
        // console.log(customized_class_list_ways[currentScheduleIndex2])
        // let index = 0
        // if (key[key.length-3] == 'A') {
        //     index = 0
        // } else if (key[key.length-3] == 'B') {
        //     index = 1
        // } else {
        //     index = 2
        // }
        let this_class_dict = customized_class_list_ways[currentScheduleIndex2][index] // dict contain one class
        let this_class = this_class_dict[Object.keys(this_class_dict)[0]]
        console.log(this_class)
        // Check if a popup already exists
        if ($('.popup').length != 0) {
            $('.popup').remove();
        }
        if ($('.popup').length === 0) {
            // Create the popup dynamically
            const popup = $(`
                <div class="popup">
                    <p>${this_class[2]}</p>
                    <p>Title: ${this_class[8]}</p>
                    <p>Enrolled: ${this_class[3]}</p>
                    <p>Waitlist: ${this_class[4]}</p>
                    <p>Instructor: ${this_class[5]}</p>
                    <p>Location: ${this_class[6]}</p>
                </div>
            `);   
            $('body').append(popup);

            // Position the popup near the target
            const offset = $(this).offset();
            popup.css({
                top: offset.top + $(this).outerHeight(),
                left: offset.left,
            });
        }

        // Stop propagation to prevent immediate hiding
        event.stopPropagation();
    });

    // Hide the popup when clicking anywhere else
    $(document).on('click', function () {
        $('.popup').remove(); // Remove the popup
    });

    // Prevent hiding when clicking inside the popup
    $(document).on('click', '.popup', function (event) {
        event.stopPropagation();
    });


    $('#done').click(function() {
        // $('#loading2').show();
        // $("#error2").html("");
        var customizations_list = [];
        currentScheduleIndex2 = 0;
        // customized_class_list_ways = [];
        // const weekDay = -1;     // impossible value

        // $("#scheduleInfo2").html('');

        $('.customization').each(function() {
            // Get the input value
            const weekDaySelect = $(this).find('.weekDay');
            const weekDay = weekDaySelect.val();
            const dayTimeSelect = $(this).find('.dayTime');
            const dayTime = dayTimeSelect.val();
            const customTimeInput = $(this).find('.customTime');
            const customTime = customTimeInput.val();

            customizations_list.push({
                weekDay: weekDay,
                dayTime: dayTime,
                customTime: customTime
            });
        });

        console.log(customizations_list[0]);

        // send customization info to backend if there is 
        if (customizations_list.length > 0) {
            $('#loading1').show();
            $("#scheduleInfo1").html('');
            $("#error").html("");
            $('#loading2').show();

            customized_class_list_ways = [];
            // Make an AJAX request to the backend
            $.ajax({
                url: 'http://127.0.0.1:5000/customization',
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({ customizations: customizations_list, class_list_ways: class_list_ways}),               // can only send text to backend
                    // data: { weekDay: weekDay, dayTime : dayTime , customTime : customTime},
        
                    success: function(response) {
                        $('#loading1').hide();
                        $('#loading2').hide();
                        customized_class_list_ways = response.customized_class_list_ways;
                        // {'customizedWays': ways, 'smallestCustomizedTimeGap': smallestTimeGap,'best_customized_class_list': best_class_list}
        
                        // if (response.customizedWays != -1) {
                        console.log("There are ", response.customizedWays)
                        const best_customized_class_list = response.best_customized_class_list;
                        console.log('Backend customized response:', best_customized_class_list);
                        // const best_customized_class_list_str = JSON.stringify(best_customized_class_list);

                        if (response.customizedWays == 0) {
                            $("#ways").html("There are: " + response.customizedWays + " customized ways.");
                            $("#smallestTimeGap").html("");
                        }
    
                        // $("#customizedWays").html("There are: " + response.customizedWays + " customized ways.");
                        // $("#smallestCustomizedTimeGap").html("The best option (fewest class days and minimal time gaps between classes) has the time gap of: " + response.smallestCustomizedTimeGap + " hours per week.");
                        // $("#best_customized_class_list").html("With this schedule: " + best_customized_class_list_str);
                        else {
                            $("#ways").html("There are: " + response.customizedWays + " customized ways.");
                            $("#smallestTimeGap").html("The best option (fewest class days and minimal time gaps between classes) has the time gap of: " + response.smallestCustomizedTimeGap + " hours per week.");
                            // $("#best_class_list").html("With this schedule: " + best_customized_class_list_str);
        
                            $("#scheduleInfo1").html("Schedule number " + (currentScheduleIndex2+1) + " with the time gap = " + response.smallestCustomizedTimeGap + " hrs/week");
                        }
                        
    
                        drawScheduleTable("newTable", best_customized_class_list, response.startTime_list, response.endTime_list);
                        // }
        
                        // else {
                        //     loadCustomizedSchedule(currentScheduleIndex2);
                        // }
                    },
        
                    error: function(error) {
                        // $('#loading2').hide();                  
                        // $('#error2').text('Error! PLease check again!');
                        // $("#customizedWays").html("");
                        // $("#smallestCustomizedTimeGap").html("");
                        // $("#best_customized_class_list").html("");
                        // $(".myCustomizedTable").empty();
                        $('#loading1').hide();    
                        $('#loading2').hide();              
                        $('#error').text('Error! PLease check again!');
                        $("#ways").html("");
                        $("#smallestTimeGap").html("");
                        $("#best_class_list").html("");
                        $(".newTable").empty();
                        console.error('Error:', error);   
                    }
                })
        }
        // return to the first option if there is no customized info
        else {
            // if submit is not error
            if (WAYS != -1) {
                $("#error").html("");
                customized_class_list_ways = class_list_ways;
                if (WAYS == 0) {
                    $("#ways").html("There are: " + WAYS + " ways.");
                    $("#smallestTimeGap").html("");
                    $("#scheduleInfo1").html("");
                }
                else {
                    $("#ways").html("There are: " + WAYS + " ways.");
                    $("#smallestTimeGap").html("The best option (fewest class days and minimal time gaps between classes) has the time gap of: " + SMALLEST_TIME_GAP + " hours per week.");
                    $("#scheduleInfo1").html("Schedule number " + (currentScheduleIndex2+1) + " with the time gap = " + SMALLEST_TIME_GAP + " hrs/week"); 
                } 
                drawScheduleTable("newTable", BEST_CLASS_LIST, START_TIME_LIST, END_TIME_LIST);
            }      
        }
    })

    // the current option index
    var currentScheduleIndex2 = 0;

    // navigating between option
    function loadCustomizedSchedule(index) {

        if (index == customized_class_list_ways.length) {
            index = 0;
        }
        else if (index < 0) {
            index = customized_class_list_ways.length - 1;
        }        

        currentScheduleIndex2 = index;
        const current_class_list = customized_class_list_ways[index];

        // send request to backend to obtain data for making table
        $.ajax({
            url: 'http://127.0.0.1:5000/loadCustomizedSchedule',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ current_class_list: current_class_list }),

            success: function(response) {       
                // $("#scheduleInfo2").html("Schedule number " + (currentScheduleIndex2+1) + " with the time gap = " + response.timeGap + " hrs/week");
                $("#scheduleInfo1").html("Schedule number " + (currentScheduleIndex2+1) + " with the time gap = " + response.timeGap + " hrs/week");
                drawScheduleTable("newTable", current_class_list, response.startTime_list, response.endTime_list);
            },

            error: function(error) {
                console.error('Error:', error);
            }
        });
    }

    // $('#nextSchedule2').click(function() {
    //     currentScheduleIndex2++;
    //     loadCustomizedSchedule(currentScheduleIndex2);
    // })

    // $('#prevSchedule2').click(function() {
    //     currentScheduleIndex2--;
    //     loadCustomizedSchedule(currentScheduleIndex2);
    // })

    // $('#return2').click(function() {
    //     currentScheduleIndex2 = 0;
    //     loadCustomizedSchedule(currentScheduleIndex2);
    // })


    $('#addCustomization').click(function () {
        // let newCustomization = $('.customization').first().clone();
        let newCustomization = 
        `
        <div class="customization">
                <div>
                    <label for="weekDay">Select day that you want to customize time:</label>
                    <select name="weekDay" class="weekDay">
                        <option value="M">Monday</option>
                        <option value="T">Tuesday</option>
                        <option value="W">Wednesday</option>
                        <option value="R">Thursday</option>
                        <option value="F">Friday</option>
                    </select>
                </div>
                <div class="customeTime_container">
                    <label for="dayTime">Select time that you do not want to have class:</label>
                    <select name="dayTime" class="dayTime">
                        <option value="customize">Customize</option>
                        <option value="allday">All day</option>
                        <option value="morning">Morning (08:00 am-11:00 am)</option>
                        <option value="midday">Midday (11:00 am-01:00 pm)</option>
                        <option value="afternoon">Afternoon (01:00 pm-17:00 pm)</option>
                        <option value="evening">Evening (17:00 pm-22:00 pm)</option>           
                    </select>
                    <div class="customTime_div">
                        <label for="customTime">Enter time: (format: '08:00 am-11:00 am'):</label>
                        <input type="text" name="customTime" class="customTime" placeholder="e.g., 11:00 am-03:00 pm">
                    </div>
                </div>
                <br>
            </div>
        `
        $('#customizationForm').append(newCustomization);

    });

    $('#removeCustomization').click(function() {
        const numCustomizations = $('.customization').length;
        if (numCustomizations > 0) {
            $('.customization:last-child').remove();                // remove the last class if there is > 0 class
        }
    });

    // $('.dayTime').change(function() {
    //     if ($(this).val() === 'customize') {
    //         $('.customTime').show();
    //     } else {
    //         $('.customTime').hide();
    //     }
    // });

    $(document).on('change', '.dayTime', function() {
        if ($(this).val() === 'customize') {
            $(this).closest('.customization').find('.customTime_div').show();
        } else {
            $(this).closest('.customization').find('.customTime_div').hide();
        }
    });
    
})
