document.addEventListener("DOMContentLoaded", () => {
    let form = document.querySelector("form");
    let submit_button = document.querySelector(".submit");
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((position) => {
            let buyerlat = position.coords.latitude;
            let buyerlong = position.coords.longitude;
            let positionInfo = `Your current position is (Latitude: ${buyerlat}, Longitude: ${buyerlong})`;
            console.log(positionInfo);
            document.querySelector("#lat").value = buyerlat;
            document.querySelector("#long").value = buyerlong;
            return true;
            });
        } 
        else {
            alert("Sorry, your browser does not support HTML5 geolocation. Please update your browser, or try a different browser");
            return false;
        }
    submit_button.addEventListener("click", function() {
        form.submit();
    })
})