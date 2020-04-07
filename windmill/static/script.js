// === GLOBALS ====================================================
	let data = {arr:[]};

	let data_proxy = new Proxy(data, {
		set(target, prop, value, receiver){
			if(prop == "arr")
			return Reflect.set(target, prop, value, receiver);
		}
	});

// ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

// === BREADCRUMBS SELECTION ======================================
	function get_paths(path=''){

		const base_path = '/api/fs';

		let path_to_fetch = base_path + path;

		return fetch(path_to_fetch)
		.then(response => {
		    if(response.ok)
		        return response.json();
		    throw new Error(response);
		})
		.then(data => {
			set_select(data['files_info']);
			set_breadcrumbs(data['locations']);
		});
	}

	function set_select(data){
		//console.log("data input", data);
		let select = document.querySelector("#taskEntry");
		
		Array.from(select.children).forEach((child) => select.removeChild(child));
		data = [{'name' : ''}].concat(data);
		
		const folder_icon = '';
		const file_icon = '';
		const file_env = '';

		let icon = '';

		data.forEach((d) => {
			let opt = document.createElement('option');

			if(d['file_folder_flag'] === true){
				icon = folder_icon;
				opt.dataset.type = 'folder';
			}
			else if(d['file_folder_flag'] === false){
				icon = file_icon;
				opt.dataset.type = 'file';
			}

			opt.appendChild( document.createTextNode(`${icon}   ${d['name']}`));
			opt.value = d['path'];
			select.appendChild(opt);
		});
	}

	function load_select_dir(event, path){
		event.preventDefault();
		get_paths(path.substr(3));
	}

	function set_breadcrumbs(data){
		let breadcrumb = document.querySelector("#list-breadcrumb");

		Array.from(breadcrumb.children).forEach((child) => breadcrumb.removeChild(child));

		data.forEach((d) => {
			let li = document.createElement('li');
			li.innerHTML = `<a href="${d['path']}" onclick='load_select_dir(event, "${d['path']}")'>${d['name']}</a>`;
			li.classList.add('breadcrumb-item');
			breadcrumb.appendChild(li);
		});

	}

	function load_select(){
		let select_opt = document.querySelector("#taskEntry").value;
		let type = Array.from(document.querySelector("#taskEntry").children).filter((el) => el.selected)[0].dataset.type
		if(type =='folder')
			get_paths(`/${select_opt}`);
	}

	get_paths();
// ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


fetch("/api/tasks/")
	.then(response => {
		if(response.ok){
			return response.json();
		}
		throw new Error(response);
	})
	.then(received_data => data_proxy.arr = received_data);

$(function () {
	$('#datetimepicker1').datetimepicker();
});

$(function () {
	$('#datetimepicker2').datetimepicker();
});

function clear_value(elmt){
	document.querySelector(`#${elmt}`).value = "";
}

// === ACTIONS ====================================================

	function action(action, task_id){
		let actions = {
			"play" : "/api/task/play",
			"stop" : "/api/task/stop",
			"schedule" : "/api/task/schedule"
		};

		console.log(action, task_id);
		let req = new XMLHttpRequest();
		req.onreadystatechange = function() {
			if (this.readyState == 4 && this.status == 200) {
				// Typical action to be performed when the document is ready:
				//console.log(req.responseText);
			}
		};
		req.open("GET", `${actions[action]}/${task_id}`);
		req.send();
	}

	function play(task_id){ action("play", task_id); }
	function stop(task_id){ action("stop", task_id); }
	function schedule(task_id){ action("schedule", task_id); }
	function drop(task_id){
		fetch(`/api/task/${task_id}`, {
			method: 'DELETE'
		}).then(response => console.log(response.json()));
	}

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

/*
taskName
taskEntry
datetimepicker1_input
datetimepicker2_input
taskCronValueHours
taskCronValueMins
taskCronValueSecs
customSwitch1

*/
	function formatDate(date){
		let res = {
			"start-at": "",
			"seconds": "",
			"minutes": "",
			"hours": "",
			"end-at": ""
		}

		/* TODO funcao para formatar data */

		return res;
	}

	function edit(task_id){
		fetch(`/api/task/${task_id}`)
		.then(response => response.json())
		.then(task =>{
			let form = document.querySelector("form");
			let date = formatDate(task["cron"]);

			form.querySelector("#taskName").value = task["name"];
			form.querySelector("#datetimepicker1_input").value = date["start-at"];
			form.querySelector("#datetimepicker2_input").value = date["end-at"];
			form.querySelector("#taskCronValueSecs").value = date["seconds"];
			form.querySelector("#taskCronValueMins").value = date["minutes"];
			form.querySelector("#taskCronValueHours").value = date["hours"];
			form.querySelector("#customSwitch1").checked = true;

			let v = task["entry"].split("\\");
			
			let path = "/" + v[0];
			let filename = v[1];

			let entry = form.querySelector("#taskEntry");
			get_paths(path).then(() =>
				Array.from(entry.options).forEach(opt =>{
					if(opt.value.search(filename) != -1)
						opt.selected = true;
				})
			);
		});
	}
// ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++