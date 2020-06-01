function get_paths(path=''){

	const base_path = '/apl-wm-crm/api/fs';

	let path_to_fetch = base_path + path;

	fetch(path_to_fetch)
	.then(response => {
	    if(response.ok)
	        return response.json();
	    throw new Error(response);
	})
	.then(data => {
		set_select(data['files_info']);
		//set_breadcrumbs(data['locations']);
	});
}

function set_select(data){
	//console.log("data input", data);
	let select = document.querySelector("#venvName");
	
	Array.from(select.children).forEach((child) => select.removeChild(child));
	data = [{'name' : ''}].concat(data);

	data.forEach((d) => {
		let opt = document.createElement('option');

		opt.appendChild( document.createTextNode(`${d['name']}`));
		opt.value = d['path'];
		select.appendChild(opt);
	});
}

get_paths();