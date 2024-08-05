// log Delete Scripts

let logdeleteConfirmationModal = null; // Declare the modal variable outside the function
let responseModal = null; // Declare the response modal variable outside the function

function showConfirmationModallog(logFile) {
    const modalText = document.getElementById('modalText');
    // modalText.textContent = `Are you sure you want to delete "${logFile}"?`;
    modalText.textContent = 'Are you sure you want to delete this log ?';
    modalText.textContent_new = `Are you sure you want to delete "${logFile}"?`;


    if (!logdeleteConfirmationModal) {
      console.log("nothing")
      logdeleteConfirmationModal = new bootstrap.Modal(document.getElementById('logdeleteConfirmationModal'));
    }

    logdeleteConfirmationModal.show(); // Show the confirmation modal
}

function deleteLogFile() {
    const logFile = document.getElementById('modalText').textContent_new.replace('Are you sure you want to delete "', '').replace('"?', '');
    // Make an AJAX request to the server to delete the log file
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/delete_log', true);
    xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                // Display the response message in the response modal
                if (!responseModal) {
                    responseModal = new bootstrap.Modal(document.getElementById('responseModal'));
                }
                const responseModalBody = document.getElementById('responseModalBody');
                responseModalBody.textContent = xhr.responseText;
                responseModal.show(); // Show the response modal
            } else {
                // Handle error response
                alert('Error occurred while deleting the log file.');
            }
        }
    };
    xhr.send('log_file=' + encodeURIComponent(logFile));
    if (logdeleteConfirmationModal) {
      logdeleteConfirmationModal.hide(); // Hide the confirmation modal
    }
}

// Close the response modal when the OK button is clicked and refresh the page
document.getElementById('responseModalOKButton').addEventListener('click', function() {
    if (responseModal) {
        responseModal.hide(); // Hide the response modal
    }
    location.reload(); // Refresh the page
});