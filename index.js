const escomplex = require('escomplex');
const fs = require('fs');
const util = require('util')

var code = fs.readFileSync('index.js', 'utf8');

const result = escomplex.analyse(code);
console.log(util.inspect(result, {showHidden: false, depth: null}))
