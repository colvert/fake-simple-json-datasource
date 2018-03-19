Adaptation of https://github.com/bergquist/fake-simple-json-datasource
to build grafana views of ONAP robot results

You need to 
  1) generate the series through the python script generate_time_series.py
  2) start the node server

```
npm install
node index.js
```

the node server will consume the csv and json file produced through the python script.

Do not forget to adapt the configuration of teh python script to your environement
