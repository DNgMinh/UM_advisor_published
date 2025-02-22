$(document).ready(function () {
    // Send button click event
    $("#send-btn").click(function () {
        let userMessage = $("#user-input").val().trim();
        if (userMessage !== "") {
            appendMessage(userMessage, "user");
            $("#user-input").val(""); // Clear input field
            sendMessageToServer(userMessage);
        }
    });

    // Pressing Enter key triggers send button
    $("#user-input").keypress(function (e) {
        if (e.which === 13) {
            $("#send-btn").click();
        }
    });

    // Function to append messages to chat box
    function appendMessage(message, sender) {
        let alignmentClass = sender === "user" ? "right" : "left";

        message = message.replace(/\n/g, '<br>');

        let messageHTML = marked(message); 
  
        messageHTML = `
            <div class="chat-message ${alignmentClass}">
                <div class="message-bubble">
                    ${messageHTML}
                </div>
            </div>
        `;
        $("#chat-box").append(messageHTML).scrollTop($("#chat-box")[0].scrollHeight);
        // $("#chat-box").append(messageHTML.replace(/\n/g, "<br>")).scrollTop($("#chat-box")[0].scrollHeight);
    }
    

    // Modify the send button click function
    $("#send-btn").click(function () {
        let userMessage = $("#user-input").val().trim();
        if (userMessage !== "") {
            appendMessage("You: " + userMessage, "user");
            $("#user-input").val(""); // Clear input field
            sendMessageToServer(userMessage);
        }
    });

    // Simulated AJAX call (replace with actual server request)
    function sendMessageToServer(message) {
        $.ajax({
            url: "http://127.0.0.1:5000/chat", // Replace with your API endpoint
            type: "POST",
            data: JSON.stringify({ question: message }),
            contentType: "application/json",
            success: function (response) {
                // appendMessage("Bot: This is a test response.");
                appendMessage(response.response)
            },
            error: function () {
                appendMessage("Bot: Sorry, there was an error.");
            }
        });
    }

    // File input change event
    $("#file-input").change(function () {
        let fileName = $(this).val().split("\\").pop();
        appendMessage("File attached: " + fileName);
    });

    // Voice button (not implemented, just placeholder)
    $("#voice-btn").click(function () {
        alert("Voice feature not implemented yet.");
    });

    // Function to clear the conversation when the clear button is clicked
    $("#clear-btn").on("click", function() {
        $("#chat-box").empty(); // Remove all messages from the chat box
    });
});