function modal_info_click(index){

    let req = new XMLHttpRequest();
    req.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            document.querySelector("#modal-info-label").innerText = data.arr[index].name;
            document.querySelector("#modal-info-para").innerText = JSON.parse(req.responseText);
        }
    };

    req.open("GET", `/api/task/info/${data.arr[index].id}`);
    req.send();
}