var IP = "http://127.0.0.1:8080"
var TEST_ID = ""

// File API support.
if (window.File && window.FileReader && window.FileList && window.Blob) {
    // Great success! All the File APIs are supported.
} else {
    alert('The File APIs are not fully supported in this browser.');
}

function handleFileSelect(evt) {
    var files = evt.target.files;
    // assume only one file
    var f = files[0]
    if (f) {
	var reader = new FileReader();
	reader.onload = function(ev) {
	    // read success
	    // load (into) text
	    txt = ev.target.result
	    json = $("#input_json").val()
	    obj = jQuery.parseJSON(json)
	    obj['input']['items'] = []
	    obj['input']['items'][0] = {'bibtex':txt}
	    $("#input_json").val(JSON.stringify(obj))
	}
	reader.readAsText(f)
    } else {
	alert('file select error')
    }
}

$('#upload').change(handleFileSelect)

function test_json(id,url,json) {
    $("#testdiv").append(
       '<input type="radio" id="' + id + '">' + id + '</input><br>')

    $("#"+id).click(function() {
	$("#input_url").val(url)
	$("#input_json").val(json)
	
	$("#"+TEST_ID).attr('checked', false);
	TEST_ID = id
    })
    if (id == TEST_ID) {
	$("#"+TEST_ID).trigger('click');
    }
}

$(function() {
    $("#input_send").click(function(evt) {
	evt.preventDefault();
	$.ajax
	({
	    type: 'POST',
            url: $("#input_url").val(),
	    contentType: "application/json",
            dataType: "json",
            data: $("#input_json").val(),
            success: function(json) {
		$("#output").empty().append(JSON.stringify(json))
	    },
	    error: function(a,b,c) {
		$("#output").empty().append('json request error')
	    }
	})
    })
});

TEST_ID = "dbg_add_tag_to_item"

test_json("dbg_up", IP+"/", "")
test_json("dbg_user_signup", IP+"/u/signup",
	  '{"input": {"users": [{"name": "sixin"}]}}')
test_json("dbg_user_login", IP+"/u/login",
	  '{"input": {"users": [{"name": "sixin"}]}}')
test_json("dbg_item_add_bibtex", IP+"/i/addbibtex",
	  '{"input": {"users": [{"id": 1353815828105871}]}}')
test_json("dbg_get_item", IP+"/i/info",
	  '{"input": {"items": [{"id": 1353818091220523}, {"id": 1353818091342429}]}}')
test_json("dbg_add_tag_to_item", IP+"/t/aggit",
	  '{"input": {"users": [{"id": 1353815828105871}]}, {"items": [{"id": 1353818091220523}]}, {"tags": [{"name": "tag1"}, {"name", "tag2"}]} }')


