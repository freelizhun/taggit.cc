var IP = "http://127.0.0.1:8002"
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
	    obj['input']['papers'] = []
	    obj['input']['papers'][0] = {'bibtex':txt}
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

TEST_ID = "dbg_user_signup"

test_json("dbg_user_signup", IP+"/user/signup",
	  '{"input": {"users": [{"name": "sixin"}]}}')
test_json("dbg_user_login", IP+"/user/login",
	  '{"input": {"users": [{"name": "sixin"}]}}')
test_json("dbg_paper_add_bibtex", IP+"/paper/addbibtex",
	  '{"input":{"users":[{"id":1}],"papers":[{"bibtex":\"@article \{ abc-13,\\n title = \\"EDF\\",\\n author = \\"GHI\\",\\n journal = \\"JKL\\",\\n year = \\"2013\\",\\n note = \\"in press\\"\\n\}\"}]}}')
//	  '{"input": {"users": [{"id": 1}]}}')
test_json("dbg_paper_get_by_id", IP+"/paper/getbyid",
	  '{"input": {"papers": [{"id": 1}, {"id": 2}]}}')
test_json("dbg_tag_add_by_name", IP+"/tag/addbyname",
	  '{"input": {"tags": [{"name": "tag1"}]}}')
test_json("dbg_user_tag_item", IP+"/user/tagitem",
	  '{"input": {"utis": [{"user_id": 1, "tag_id": 1, "item_id": 1}]}}')
test_json("dbg_tag_get_by_item_id", IP+"/tag/getbyitem",
	  '{"input": {"items": [{"id": 1}]}}')
test_json("dbg_user_detag_item", IP+"/user/detagitem",
	  '{"input": {"utis": [{"user_id": 1, "tag_id": 1, "item_id": 1}]}}')
test_json("dbg_paper_get_by_tag_id", IP+"/paper/getbytag",
	  '{"input": {"tags": [{"id": 1}]}}')
test_json("dbg_paper_get_top10", IP+"/paper/gettop10",
	  '{}')
test_json("dbg_tag_get_top10", IP+"/tag/gettop10",
	  '{}')
test_json("dbg_tag_search_by_prefix", IP+"/tag/searchbyprefix",
	  '{"input": {"query": "tag", "query_size": 100}}')
