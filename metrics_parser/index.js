var DUMP_PARSE_ERRORS = true;
var DUMP_DIR = "./debug";
var DUMP_NUM = 1;

const escomplex = require('escomplex');
const util = require('util');
const zmq = require('zeromq');
const process = require('process');
const fs = require('fs');
const path = require('path');

var SERVER_MODE = false;
var FILE_MODE = false;
var file = "";

for (var i = 2; i < process.argv.length; i++) {
  if (process.argv[i] == "--server_mode") {
    SERVER_MODE = true;
  }
  else if (process.argv[i] == "--file") {
    i++;
    if (i >= process.argv.length) {
      console.log("Error while processing arguments: file path argument is missing.");
      process.exit(1);
    }
    file = process.argv[i];
    FILE_MODE = true;
  }
}

if (SERVER_MODE) {
  runserver()
}
else if (FILE_MODE) {
  var contents;
  try {
    contents = fs.readFileSync(file, 'utf8');
  } catch (err) {
    console.log('Error reading file:');
    console.log(err);
  }
  console.log(analyze(contents, false));
}

function runserver()
{
  sock = zmq.socket('rep');
  sock.bindSync('tcp://127.0.0.1:5557');
  if (DUMP_PARSE_ERRORS) {
    if (!fs.existsSync(DUMP_DIR)){
      fs.mkdirSync(DUMP_DIR);
    }
  }

  sock.on('message', function(js_code) {
    //console.log('Received code:');
    //console.log(js_code);
    //console.log('');
    sock.send(JSON.stringify(analyze(js_code, DUMP_PARSE_ERRORS)));
  });
}

function analyze(js_code, dump_parse_errors)
{
  res = {};
  try {
    res = escomplex.analyse(js_code, null, { ecmaVersion: 8, loc: true,
                                             sourceType: 'module',
                                             allowImportExportEverywhere: true,
                                             allowReturnOutsideFunction: true,
                                             ecmaFeatures: {
                                               // enable implied strict mode (if ecmaVersion >= 5)
                                               impliedStrict: false
                                             }});
  } catch (err) {
    res.error = err.message + " at (" + err.lineNumber + ", " + err.column + ")";
    if (dump_parse_errors) {
      filename = path.join(DUMP_DIR, 'dump_' + DUMP_NUM++ + ".js");
      fs.writeFileSync(filename, js_code);
    }
  }
  return res;
}

