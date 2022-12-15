var game = JSON.parse('{{game|safe}}');
if (game.status != "Finished") {
    window.setInterval(checkChanged, 1000);
}
function checkChanged() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '{{data}}', true);
    xhr.onreadystatechange = function(){
        if (xhr.readyState === 4 && xhr.status === 200) {
            if (JSON.stringify(JSON.parse(xhr.responseText)) != JSON.stringify(game)) {
                location.reload();  // refresh the page if new data comes in
            }
        }
    };
    xhr.send(null);
}
