var express = require('express');
var bodyParser = require('body-parser');
var _ = require('lodash');
var app = express();

app.use(bodyParser.json());

// var timeserie = require('./series_pod4-orange-heat2');
var timeserie = []
var now = Date.now();

// for (var i = timeserie.length -1; i >= 0; i--) {
//   var series = timeserie[i];
//   var decreaser = 0;
//   for (var y = series.datapoints.length -1; y >= 0; y--) {
//      series.datapoints[y][1] = Math.round((now - decreaser) /1000) * 1000;
//      decreaser += 50000;
//   }
// }

var annotation = {
  name : "annotation name",
  enabled: true,
  datasource: "generic datasource",
  showLine: true,
}

var annotations = [
  { annotation: annotation, "title": "Donlad trump is kinda funny", "time": 1450754160000, text: "teeext", tags: "taaags" },
  { annotation: annotation, "title": "Wow he really won", "time": 1450754160000, text: "teeext", tags: "taaags" },
  { annotation: annotation, "title": "When is the next ", "time": 1450754160000, text: "teeext", tags: "taaags" }
];

// var now = Date.now();
// var decreaser = 0;
// for (var i = 0;i < annotations.length; i++) {
//   var anon = annotations[i];
//
//   anon.time = (now - decreaser);
//   decreaser += 1000000
// }


var table =
  {
    columns: [{text: 'Time', type: 'time'}, {text: 'POD', type: 'string'}, {text: 'Score', type: 'number'}],
    rows: [],
    type: "table"
  };


function setCORSHeaders(res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST");
  res.setHeader("Access-Control-Allow-Headers", "accept, content-type");
}

function updateTable() {
  var fs = require('fs');
  var parse = require('csv-parse');

  var csvData=[];
    fs.createReadStream('./scores_pod.csv')
        .pipe(parse({delimiter: ','}))
        .on('data', function(csvrow) {
            // console.log(csvrow);
            //do something with csvrow
            csvData.push(csvrow);
        })
        .on('end',function() {
          //do something wiht csvData
          console.log(csvData);
          table =
            {
              columns: [{text: 'Time', type: 'time'}, {text: 'POD', type: 'string'}, {text: 'Score', type: 'number'}],
              rows: csvData,
              type: "table"
            };
        });
}

function updateTimeSeries() {
  // timeserie = require('./series_pod4-orange-heat2');
  console.log("Update series....")
  // console.log(timeserie)
  timeserie = JSON.parse(require('fs').readFileSync('./series_pod4-orange-heat2.json', 'utf8'));

  var now = Date.now();
  //console.log(timeseries)
  console.log(now)

  for (var i = timeserie.length -1; i >= 0; i--) {
    var series = timeserie[i];
  }

}

var now = Date.now();
var decreaser = 0;
for (var i = 0;i < table.rows.length; i++) {
  var anon = table.rows[i];

  anon[0] = (now - decreaser);
  decreaser += 1000000
}

app.all('/', function(req, res) {
  setCORSHeaders(res);
  res.send('I have a quest for you!');
  res.end();
});

app.all('/search', function(req, res){
  setCORSHeaders(res);
  var result = [];
  _.each(timeserie, function(ts) {
    result.push(ts.target);
  });

  res.json(result);
  res.end();
});

app.all('/annotations', function(req, res) {
  setCORSHeaders(res);
  console.log(req.url);
  console.log(req.body);

  res.json(annotations);
  res.end();
})

app.all('/query', function(req, res){
  setCORSHeaders(res);
  updateTable()
  updateTimeSeries()
  console.log(req.url);
  console.log(req.body);

  var tsResult = [];
  _.each(req.body.targets, function(target) {
    if (target.type === 'table') {
      tsResult.push(table);
    } else {
      var k = _.filter(timeserie, function(t) {
        return t.target === target.target;
      });

      _.each(k, function(kk) {
        tsResult.push(kk)
      });
    }
  });

  res.json(tsResult);
  res.end();
});

app.listen(3333);

console.log("Server is listening to port 3333");
