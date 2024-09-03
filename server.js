var http = require('http');
var fs = require("fs");



const server = http.createServer( (req, res) => {
    const headers = {
        "Content-Type": "application/json",
    };
    if (req.url = "/endpoint") {
        let body = '';
        req.on('data', chunk => {
            body += chunk
        });
        req.on('end', () => {
            console.log(`Raw Body: ${body}`)
            fs.writeFile('last_signal.txt', body, (err) => {
                console.log("Error: ", err)
            })         
        })
    }
});

server.listen(80, () => {
    const PORT = server.address().port;
    console.log("Server listening on port: ", PORT);
});

