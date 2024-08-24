var http = require('http');

const PORT = process.env.PORT || 8080;
http.createServer( (req, res) => {
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
            try {
                parsed = JSON.parse(body)
                console.log("Parsed: ", parsed)
                res.writeHead(200, headers)
                res.end("Response sent")
            } catch (err) {
                console.log(`Error: ${err}`)
                console.log(`Request causing error: ${body}`)
                let errorHeaders = {
                    "Content-Type": "application/json",
                    "status": "error"
                }
                res.writeHead(400, errorHeaders)
                res.end("Error: ", err)
            }
        })
    }
}).listen(PORT)