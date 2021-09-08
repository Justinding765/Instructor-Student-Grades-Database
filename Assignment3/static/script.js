// Handle alert messages
function handleMessage(message) {
    if (message === 'wrongcredentials') {
        alert("Incorrect username/password.")
    } else if (message === 'createaccountsuccess') {
        alert("Account created successfully.");
    } else if (message === 'emptyfields') {
        alert("You did not fill in all the fields.")
    } else if (message === 'existinguser') {
        alert("This username is already taken.");
    } else if (message === 'nonnumbererror') {
        alert("You must enter a number.");
    } else if (message === 'feedbacksuccess') {
        alert("Thank you for your feedback.");
    } else if (message === 'editmarksuccess') {
        alert("Mark successfully updated.")
    } else if (message === 'nosuchgrade') {
        alert("This student does not have a grade for this assignment.");
    } else if (message === 'studentdoesnotexist') {
        alert("Student is not enrolled.");
    } else if (message === 'error') {
        alert("An unexpected error ocurred.");
    }
}