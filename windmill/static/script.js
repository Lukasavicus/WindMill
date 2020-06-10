
let ACTION_FORM = "POST";

// === BREADCRUMBS SELECTION ======================================
	function get_paths(path=''){

		const base_path = '/apl-wm-crm/api/fs';

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

// === USEFULL ====================================================

	$(function () {
		$('#datetimepicker1').datetimepicker();
	});

	$(function () {
		$('#datetimepicker2').datetimepicker();
	});

	function clear_value(elmt){
		document.querySelector(`#${elmt}`).value = "";
	}

	document.querySelector("#submit-button").addEventListener('click', function(event){
		//alert('intercepted', ACTION_FORM);
		if(ACTION_FORM == "POST"){
			console.log(this);
			return true;
		}
		else{
			event.preventDefault();
			const task_id = document.querySelector("#taskId").value;
			update(task_id);
			ACTION_FORM = "POST";
			return false;
		}
	});
// ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

// === ACTIONS ====================================================
	function get_task_row(row_id){
		return document.querySelector("#jobs").querySelector("tbody").children[row_id];
	}

	function get_job_id(row_id){
		let row = get_task_row(row_id-1);
		return row.cells[0].textContent;
	}

	function get_job_name(row_id){
		let row = get_task_row(row_id-1);
		return row.cells[1].textContent;
	}

	function get_job_no_runs(row_id){
		let row = get_task_row(row_id-1);
		return row.cells[6].textContent;
	}

	function play(row_id){
		let job_name = get_job_name(row_id);
		notify(`Playing Job: '${job_name}'`, 'success');
		action("/apl-wm-crm/api/task/play/", row_id)
	}
	function stop(row_id){
		let job_name = get_job_name(row_id);
		notify(`Stoping Job: '${job_name}'`, 'success');
		action("/apl-wm-crm/api/task/stop/", row_id)
	}
	function schedule(row_id){
		notify(`Scheduling Job: '${task_id}'`, 'success');
		action("/apl-wm-crm/api/task/schedule/", row_id)
	}
	function drop(row_id){
		action("/apl-wm-crm/api/task/", row_id, { method : 'DELETE' })
	}

	function action(url_base, row_id, fetch_options={}){
		let task_id = get_job_id(row_id);
		fetch(`${url_base}${task_id}`, fetch_options)
			.then(response => response.json())
			.then(data => process_answer(data))
			.then(() => {
				fetch("/apl-wm-crm/api/tasks/")
					.then(response => response.json())
					.then(data => update_table(data))
			})
	}

	function process_answer(answer){
		//console.log(answer);
		if(answer.response.status == "OK")
			notify(answer.msg, 'success');
		else
			notify(answer.err, 'danger');
	}

	function update_table(data){
		console.log("update_table", data);

		let tbody = document.querySelector("#jobs").querySelector("tbody");
		while(tbody.childElementCount != 0)
			tbody.deleteRow(0)

		data.forEach(job =>{
			let idx = tbody.childElementCount;
			let row = tbody.insertRow(idx)
			row.innerHTML = `
				<td>${job.name}</td>
				<td>${job.entry_point}</td>
				<td></td>
				<!-- <td></td> -->
				<td>${job.last_exec_status}</td>
				<td>"/s /0 /0 /0 /e"</td>
				<td>${job.no_runs}</td>
				<td><i onclick='play("${idx}")' class="fa fa-play"></i></td>
				<!-- <td><a href="/apl-wm-crm/task/play/${idx}"><i class="fa fa-play"></i></a></td> -->
				<td><i onclick='stop("${idx}")' class="fa fa-stop"></i></td>
				<td><i onclick='schedule("${idx}")' class="fa fa-calendar"></i></td>
				<td><i onclick='edit("${idx}")' class="fa fa-edit"></i></td>
				<td><i onclick='drop("${idx}")' class="fa fa-trash"></i></td>
				<td><i onclick='alert("hey")' class="fa fa-copy"></i></td>
				<!-- <td><i onclick='modal_info_click("${idx}")' data-toggle="modal" data-target="#modal-info" class="fa fa-info"></i></td> -->
			`
		});

	}

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

	function edit(row_id){
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

		let job_no_runs = get_job_no_runs(row_id);
		let job_name = get_job_name(row_id);
		if(job_no_runs > 0){
			notify(`Could not edit Job '${job_name}' because it alerady ran once`, "danger");
			return null;
		}

		let task_id = get_job_id(row_id);

		document.querySelector("#submit-button").innerText = "Update";
		document.querySelector("#taskId").value = task_id;

		fetch(`/apl-wm-crm/api/task/${task_id}`)
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
			//form.querySelector("#customSwitch1").checked = true;

			//let v = task["entry"].split("/"); //\\
			
			let path = "/" + task["path_to_entry_point"]; //v[0]
			let filename = task["file_of_entry_point"]; //v[1]

			let entry = form.querySelector("#taskEntry");
			get_paths(path).then(() =>
				Array.from(entry.options).forEach(opt =>{
					if(opt.value.search(filename) != -1)
						opt.selected = true;
				})
			);
		});

		ACTION_FORM = "PUT";
	}

	function update(task_id){
		const form = document.querySelector("#form-task");

		let formData = new FormData(form);

		console.log(">>", formData);

		fetch(`/apl-wm-crm/api/task/${task_id}`, {
			method: 'PUT',
			body: formData

		})
		.then(response => console.log(response.json()))
		.catch(response => console.log(response.json()));
	}

	function notify(msg, msg_type, title=""){
		div = document.createElement('div');
		div.classList.add('alert', `alert-${msg_type}`, 'alert-dismissible', 'fade', 'show');
		div.setAttribute('role', 'alert');
		div.innerHTML = `
			<strong>${title}</strong> ${msg}
			<button type="button" class="close" data-dismiss="alert" aria-label="Close">
				<span aria-hidden="true">&times;</span>
			</button>
		`;
		document.querySelector('#messaging').appendChild(div);
	}

// ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++