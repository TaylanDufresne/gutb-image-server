
const port = process.env.PORT || 3010;
const https = require("https")
const cors = require("cors");
const { createCanvas, loadImage } = require('canvas');
const fs = require("fs")
const express = require('express')


const corsOptions = {
    origin: '*',
    credentials: true,
    optionSuccessStatus: 200,
}


const app = express()


app.use(cors(corsOptions))

app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ limit: '50mb' }));

app.post("/", async (req, res) => {

    try {
        let image = buildTrack(req.body)
        res.writeHead(200, {
            'Content-Type' : 'image/png'
        })
        res.end(image)
        console.log("Sent!")
    } catch (err) {
        console.log(`Error: ${err} ${req.headers} ${req.body}`)
    }

})


const options ={ 
    key: fs.readFileSync("server.key"),
    cert: fs.readFileSync("server.cert"),
};

app.use('/static', express.static('track_images'))

https.createServer(options, app)
.listen(port, function (req, res) {
  console.log(`GUTB image server up and listening on port:${port}`);
});

function buildTrack(data) {

    // Maximum canvas size is 16383, most chromosomes will have more base pairs than this
    let pixelWidth = 16383
    let height = 1

    // var track = new Image()

    let background_color = data.isDark ? 18 : 255
    let lastBP = data.end
    let chromosome = data.chromosome
    const ratio = pixelWidth / lastBP


    const canvas = createCanvas(pixelWidth, height)
    const ctx = canvas.getContext('2d')

    // Building a boolean array for which pixels should be coloured
    let buildingBitmap = Array(Math.round(lastBP * ratio)).fill(false)

    data.data.forEach(element => {


        for (let p = Math.round(element.start * ratio) - 1; p < Math.round(element.end * ratio); p++) {
            buildingBitmap[p] = true
        }
    })

        // Allocating the required number of bytes
        let buffer = new Uint8ClampedArray(pixelWidth * height * 4);

        for (var y = 0; y < height; y++) {
            for (var x = 0; x < pixelWidth; x++) {
                var pos = (y * pixelWidth + x) * 4; // position in buffer based on x and y
                if (!buildingBitmap[x]) {
                    buffer[pos] = background_color;
                    buffer[pos + 1] = background_color;
                    buffer[pos + 2] = background_color;
                    buffer[pos + 3] = 255;    // set alpha channel

                }
                else {
                    buffer[pos] = 0;
                    buffer[pos + 1] = 0;
                    buffer[pos + 2] = 0;
                    buffer[pos + 3] = 0;

                }
            }
        }

        let imageData = ctx.createImageData(pixelWidth, height);
        imageData.data.set(buffer);

        // update canvas 
        ctx.putImageData(imageData, 0, 0);
        
        let sending = canvas.toBuffer("image/webp")
        // fs.writeFileSync("./" + chromosome +"server_generated.png", canvas.toBuffer("image/png"))
        return sending
}

