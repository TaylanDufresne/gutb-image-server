
const port = process.env.PORT || 3010;
const cors = require("cors");
const { createCanvas, loadImage } = require('canvas');
const fs = require("fs")


const corsOptions = {
    origin: '*',
    credentials: true,
    optionSuccessStatus: 200,
}


const express = require('express')
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

app.use('/static', express.static('track_images'))

app.listen(port)


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

// pixel_width = int(input("How many pixels?:\n"))
//     print("Parsing files...")
//     dataset = read_bed_file(bed_file)

//     statement = "Generating dark " if dark else "Generating light "
//     background_color = 18 if dark else 255

//     overview_bar = ChargingBar("Overall Progress", max=len(dataset.keys()))
//     for x in dataset.keys():

//         last_bp = max(dataset[x].items(), key=lambda a: a[1]['end'])
//         gap = dataset[x][0]['end']
//         last_bp = last_bp[1]['end']
//         number_of_entries = len(dataset[x])

//         total = pixel_width

//         bp_ratio = last_bp / total
//         adjustment = round(last_bp / bp_ratio)
//         rounded_bp_ratio = round(last_bp / total)
//         pixels_per_block = round(total/number_of_entries)
//         # print(pixels_per_block)
//         # print(rounded_bp_ratio)

//         if bp_ratio != 0:
//             # print(statement + x + " methylation image with " +
//             #       str(total) + " pixels...")
//             # print("Resolution: " + str(rounded_bp_ratio) + " base pairs per pixel")
//             heatmap_image = Image.new('RGBA', (adjustment, 1))
//             histogram_image = Image.new('RGBA', (adjustment, 1000))
//             previous = -1
//             # bar = Bar("Chromosome", max=len(dataset[x].keys()))
//             for block in dataset[x]:
//                 if previous > dataset[x][block]['start']:
//                     print("File out of order.")
//                     exit(-1)
//                 previous = dataset[x][block]['start']
//                 value = dataset[x][block]['value']
//                 alpha = int(255 * ((100 - value) / 100))
//                 value = value * 10
//                 spacing = int(dataset[x][block]['start'] / gap)

//                 for z in range(0, pixels_per_block):
//                     placement = int(z + int(spacing * pixels_per_block))
//                     if placement < total:
//                         heatmap_image.putpixel((placement, 0), (background_color, background_color,
//                                                                 background_color, alpha))
//                         for n in range(0, 999 - value):
//                             histogram_image.putpixel((placement, n), (background_color, background_color,
//                                                                       background_color, 255))

//             # print("Successfully made track image! Saving...")
//             suffix = "_methylation_dark.png" if dark else "_methylation.png"
//             heatmap_image.save(image_path + "/" + x + "_" + str(int(pixel_width / 1000)) + "K_heatmap" + suffix,
//                                "PNG")
//             histogram_image.save(image_path + "/" + x + "_" + str(int(pixel_width / 1000)) + "K_histogram" + suffix,
//                                "PNG")
//             # bar.next()
//             overview_bar.next()
//     overview_bar.finish()