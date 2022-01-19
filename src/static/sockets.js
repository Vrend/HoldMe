var timeout_check = 0;
var socket = io({transports: ['websocket']});

function timeout() {
    timeout_check += 1;
    if(timeout_check === 15) {
        console.log('Destroying node');
        localStorage.clear();
        socket.close();
    }
}

socket.on('connect', function() {
    timeout_check = 0;
    if(localStorage.getItem('id') === null) {
        socket.emit('on_connect', {'id': 'none' });
    }
    else {
        socket.emit('on_connect', {'id': localStorage.getItem('id')});
    }
});
socket.on('heartbeat', function(){
    console.log('Heartbeat');
    var obj = {};
    var blocks = [];
    for(var i = 0; i < localStorage.length; i++){
        var id = localStorage.key(i);
        if(id === 'id') {
            obj.id = localStorage.getItem(id);
        }
        else {
            blocks.push(id);
        }
    }
    obj.blocks = blocks;
    socket.emit('heartbeat_resp', obj);
});
socket.on('add_block', function(obj){
    console.log('Received Block');
    localStorage.setItem(obj.id, obj.data);
});
socket.on('give_uid', function(uid){
    localStorage.setItem('id', uid);
});
socket.on('send_block', function(id) {
    console.log('sending block');
    obj = {};
    obj.id = id;
    obj.block = localStorage.getItem(id);
    socket.emit('receive_block', obj);
});
socket.on('send_block_propagate', function(id) {
    console.log('sending block');
    obj = {};
    obj.id = id;
    obj.block = localStorage.getItem(id);
    socket.emit('receive_block_propagate', obj);
});
socket.on('flush_block', function(id) {
    localStorage.removeItem(id);
});
socket.on('flush_all', function() {
    localStorage.clear();
});
socket.on('force_disconnect', function() {
    socket.close();
});
socket.on('reconnect_error', timeout);
socket.on('connect_timeout', timeout);
socket.on('reconnect_failed', timeout);
socket.on('connect_error', timeout);