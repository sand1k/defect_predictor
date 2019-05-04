const escomplex = require('escomplex');
const util = require('util')
const zmq = require('zeromq')

sock = zmq.socket('rep');
sock.bindSync('tcp://127.0.0.1:5557');

sock.on('message', function(js_code) {
  console.log('Received code:');
  console.log(js_code);
  console.log('');
  res = {};
  try {
    res = escomplex.analyse(js_code);
  } catch (err) {
    res.error = err.message;
  }
  sock.send(JSON.stringify(res));
});


