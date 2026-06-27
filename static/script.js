function showMessage() {

    let question =
        document.getElementById("question").value;

    document.getElementById("answer").innerHTML =
        "You asked: " + question;
}